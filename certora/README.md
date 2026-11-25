# Babylon collateral restrictions

## Liquidator payment bounds (property 2)

`confs/BabylonLiquidationPaymentBounds.conf` checks the production `BabylonSpokeInstance`:
after a successful `liquidationCall`, the amount passed to `safeTransferFrom` from
the liquidator is at most `debtToCover` and at most the user's pre-liquidation debt
from `getUserDebt`. This spoke takes one debt reserve per call; the per-reserve
`debtToCoverAmounts[i]` wording in `ppties.md` matches the batch variant.
`confs/BabylonLiquidationCollateralBound.conf` checks, on the same model without the
galois facts, that the collateral removed is worth at most the pulled debt times
the liquidation bonus.

```sh
certoraRun certora/confs/BabylonPaymentMath.conf
certoraRun certora/confs/BabylonLiquidationPaymentBounds.conf
certoraRun certora/confs/BabylonLiquidationCollateralBound.conf
```

Model:

- `Math.mulDiv` (both overloads) is `exactMulDiv` from `helpers/MulDiv.spec`: the
  exact quotient, with the Solidity revert cases (zero denominator, overflowing
  quotient) pruned. `BabylonPaymentMath.conf` checks it against the Solidity, reverts
  included, whenever `x * y` fits in 256 bits. Larger products cannot be checked by
  the Prover in either bitwise mode (integer mode over-approximates the 512-bit
  code; `precise_bitwise_ops` bounds `mathint` near 2^256), so that branch relies
  on OpenZeppelin's correctness.
- Hub views follow `Hub.sol`: one drawn index and one `(addedAssets, addedShares)`
  pair per asset, with `SharesMath` rounding and virtual shares. This is a **trust
  assumption on the Hub**: in the cap-resized branch the bound only holds because
  `previewAddByShares` and `previewAddByAssets` share that pair. With independent
  arbitrary previews the resized drawn shares are unbounded and the property fails.
- Arbitrary values: oracle prices, the liquidation bonus, asset units,
  `previewRemoveByShares`, and `_calculateUserAccountData`. The bound holds for any
  of them. State-changing Hub calls and `notifyReportDeficit` are `HAVOC_ALL`;
  `_notifyRiskPremiumUpdate` is `NONDET` (runs after the pull).

Status: no counterexamples. Both assertions
[time out](https://prover.certora.com/output/7508195/22372b1772f945fc99d2ab9b45511707)
with 76% (cover bound) and 90% (debt bound) of the split tree proved, at 600 s per
query. The NIA backend strategy
([run](https://prover.certora.com/output/7508195/a6f81cdc8b52483d9eb0996137f03e91))
gives the same result. The
[mulDiv check](https://prover.certora.com/output/7508195/bbe0de0445914c5bbe636f09846bf552)
verifies.

## Collateral restrictions (property 1)

`confs/BabylonCollateralRestrictions.conf` targets the current source through a read-only
`BabylonSpokeHarness`. Production contracts are unchanged. The spec implements
property 1 from `certora/ppties.md`:

- Only `MANAGED_COLLATERAL_RESERVE_ID` may have a collateral flag.
- Every user has at most one collateral reserve and one borrowed reserve.
- The managed reserve is never borrowable and no user has its borrowing flag set.

The target contains only the five invariants for property 1. `setup()` assumes
Babylon's constructor-set user limit of one and the no-Hub clause of Spoke's
`validReserveId` property. Inline assumptions supply its no-position-flags
clause for the relevant user and reserve. These general Spoke facts are proof
dependencies, not separate verification targets here.

`onlyManagedCollateral` and `managedReserveNeverBorrowed` check listed reserves;
the assumed Spoke validity property covers unlisted IDs. The position assumption
also prevents newly listed reserves from exposing pre-existing flags.

Liquidation preservation also uses `requireInvariant borrowCountAtMostOne` for
the actual liquidated user, who may differ from the invariant's symbolic user.
This removes unreachable multiple-debt pre-states from deficit-loop reasoning.
The borrow-count invariant's initialization and preservation are included in the
same target, including its liquidation step; this dependency is not a standalone
assumption and requires all invariant checks to pass together.

## Run

From the `aave-v4` root, with Solidity 0.8.28 and the Certora CLI installed:

```sh
certoraRun certora/confs/BabylonCollateralRestrictions.conf --compilation_steps_only
certoraRun certora/confs/BabylonBitMathEquivalence.conf
certoraRun certora/confs/BabylonCollateralRestrictions.conf
```

Cloud verification uses `CERTORAKEY`. Compilation alone is not a proof.
Both cloud targets must verify. `BabylonBitMathEquivalence.conf` checks the original
`LibBit.fls` implementation against the exact CVL model used by the main target;
its spec intentionally does not apply that summary to itself. Re-run both targets
after changing the library, the model, or the proof configuration.
The config uses non-IR compilation to keep the Prover's decompiled representation
manageable.

## Validation status

The current five-invariant target has been simplified and needs a new cloud run.
The [earlier main run](https://prover.certora.com/output/7508195/8f517346e037454c9bcd30613dc8553a)
reported 14 root groups and 400 leaf checks for a previous snapshot containing
additional supporting invariants, witnesses and a bitmap lemma. Those totals do
not describe the current target. Non-vacuity checks remain enabled through
`rule_sanity: "basic"`.

The [checked-in helper equivalence target](https://prover.certora.com/output/7508195/1690f8211a014db2851de027a51ace64)
verified, including its non-vacuity and envfree checks. It compares the shared
CVL model with the original `LibBit.fls` for all `uint256` values without input
assumptions.

Use the compilation command above to check the current harness and CVL spec.
Non-IR compilation avoids the preprocessing expansion that previously exceeded
`maxCommandCount=1000000`.

### Vacuity diagnosis

Before these changes, the [Default evm timeouter run](https://prover.certora.com/output/7508195/8b1d465605a34266be7ada48ff600648)
finished with 378 verified leaf checks and 16 failed non-vacuity checks:
repayment and the supported liquidation overload for each of the eight
invariants. Only three root groups were fully green. More time alone did not
resolve that vacuity. The following experiments isolated its cause.

The symbolic `IHubBase.PremiumDelta` summary contains two signed `int256` fields.
Its interaction with `precise_bitwise_ops` is problematic in the tested backend:

- [Focused reachability checks](https://prover.certora.com/output/7508195/73dc1c7cbb454245af16541d4455f945)
  cannot reach successful repayment, even with all setup assumptions removed.
- [The same repayment model with the integer backend](https://prover.certora.com/output/7508195/b9ce1e863cff492e97b3efbc06635fbe)
  verifies both repayment witnesses. This run disables `precise_bitwise_ops`
  and uses `-backendStrategy singleRace -smt_useLIA false -smt_useNIA true`.
- [A minimal reproduction without Aave code](https://prover.certora.com/output/7508195/6a7681a46af04eedbb620c6069a167bc)
  has an unreachable signed-struct witness and a verified unsigned-struct
  witness under `precise_bitwise_ops`. A readable copy is in
  `repros/SignedStructSummary.{sol,spec,conf}`. Both concrete Solidity calls
  return successfully, and both summaries admit the concrete zero result.
- [The minimal reproduction with only `precise_bitwise_ops` disabled](https://prover.certora.com/output/7508195/51de243404754112a1d5db8cdff4ecbc)
  verifies both witnesses. This isolates the flag/summary interaction without
  changing the Solidity code, summary values, invariants or loop bounds.

Both affected production entry points use the premium-delta summary. The
reproduction establishes a verification-model/encoding issue, not a Solidity
counterexample. Fixing the returned delta to zero also restores repayment
reachability in a diagnostic, but that restriction is not a general proof fix.

The [Nonlin depth 0 timeouter run](https://prover.certora.com/output/7508195/25b1acf757cd41fa856c9b935c7d80b7)
instead errors because it combines integer and bit-vector solver modes
(`IllegalStateException`, code `2781128436`). It is not a property violation.

Disabling `precise_bitwise_ops` in the [full property experiment](https://prover.certora.com/output/7508195/c8a472a9748346c4a102b614a0490f18)
exposes imprecise bitmap counterexamples. For example, the
`managedReserveNeverBorrowed / setUsingAsCollateral` trace starts with bitmap
word `2`, disables collateral for reserve `0`, and stores word `1`. The concrete
operation is `2 & ~2 == 0`; it cannot create borrowing bit `1`. This is a modeling
counterexample, not an execution of the Solidity operation. The alternative
`smt_use_bv` mode reproduces the signed-summary
failure in the minimal example. The main config therefore retains exact bitwise
operations and uses the property-specific premium-payload projection described
below. It also uses `twostage` preprocessing and an 1800-second overall budget;
sanity checks remain enabled. The completed main run above verifies this revised
model, including all previously failing non-vacuity checks. The remaining
liquidation timeouts were resolved using the proved bitmap facts and exact
bit-search model, the listed/unlisted case split, and summaries of unobserved
pricing arithmetic. Both the external and internal forms of the pure
liquidation-bonus calculation are summarized; the external declaration alone
did not cover the executed internal body.

## Scope

- Users, caller addresses, amounts and reserve IDs are symbolic. Users are not
  enumerated. The managed reserve ID is not fixed to a particular number.
- Preservation is restricted to pre-states with at most **four listed reserves**.
  The count invariant expressions also guard their pre-state count evaluation
  with this bound. Listing a fifth reserve leaves the count proof scope.
- Signed manager-update batches have at most four updates. `loop_iter` is five
  and `optimistic_loop` is false; loop overruns must fail instead of being assumed
  away. Increasing the scope requires checking the corresponding loop bounds.
- The real bitmap operations, popcounts and reserve guards are executed through
  the production entry points, including borrowing, repayment, liquidation and
  deficit reporting. The highest-set-bit search `LibBit.fls` uses an exact CVL
  model whose equality to the original implementation is independently checked
  for every `uint256` input, including zero. Bitmap writes, masks and popcounts
  remain concrete. Accounting helpers are abstracted as described below. No
  summary assumes property 1.
- External Hub, oracle, token and authority calls return arbitrary values without
  callbacks into the Spoke. Token transfers and signature/authority checks are
  similarly modeled. External accounting and adversarial callbacks are outside
  this target. Unknown external calls fail explicitly.
- `Premium.calculatePremiumRay` returns an arbitrary value. The
  `calculatePremiumDelta` summary fixes its two signed payload fields to zero
  and preserves its `restoredPremiumRay` argument. This is a projection of
  data unobserved by this property, not an assumption about real premium values.
  All consumers of those signed fields are already summarized Hub calls,
  `applyPremiumDelta` (whose premium shares/offset writes are omitted), and
  events. No retained branch, bitmap operation, drawn-share update or invariant
  reads the signed payload. The relevant consumers were reviewed in `repay`,
  `_notifyRiskPremiumUpdate`, `_liquidateDebt`, and `notifyReportDeficit`, including
  the liquidation result's event forwarding. Removing the pure calculation's
  revert conditions admits additional paths. This source-reviewed projection
  is valid only together with those consumer summaries and the no-callback
  model; it must be reviewed again if they change. Drawn-share updates and
  borrowing-bit clearing remain concrete. This target does not establish
  premium-accounting correctness or separately prove this projection.
- Pure `MathUtils.uncheckedExp` and `WadRayMath.rayMulUp` results are arbitrary. This
  deliberately admits extra arithmetic outcomes; these functions do not write
  position flags, reserve configuration or the reserve count.
- `BabylonLiquidationLogic._calculateLiquidationAmounts` returns arbitrary
  unsigned amounts. It is read-only and its external Hub preview calls are
  already modeled without callbacks. This removes expensive sizing arithmetic
  and admits extra outcomes without restricting state or inputs. Liquidation
  validation, collateral/debt share updates, borrowing-bit clearing and deficit
  handling still execute. Liquidation pricing correctness is outside this proof.
  The pure `LiquidationLogic.calculateLiquidationBonus` call likewise returns an
  arbitrary value: its result feeds the sizing summary and the entry point's
  return value, without changing restriction state.
- Account-data computation returns arbitrary fields. Its optional writes to
  `UserPosition.dynamicConfigKey`, and premium notification's writes to
  `riskPremium`, `premiumShares` and `premiumOffsetRay`, are omitted. This is a
  source-reviewed frame abstraction: neither helper writes bitmap bits, reserve
  flags, reserve hubs or the reserve count. The real health-factor validation
  remains, operating on the arbitrary account data. This target does not prove
  the helpers' accounting behavior or their frame conditions separately; changes
  to either helper require reviewing these summaries again.
- The two raw storage view readers are removed from the verification scene to
  allow storage splitting.
- `multicall` is the sole filtered entry point. Its delegatecall wrapper is not
  proved here. Individual operations are checked, which supports reasoning about
  sequential batches that stay within the reserve bound, but does not independently
  verify wrapper correctness.
- Initialization is checked for the inherited implementation constructor and
  the exposed initializer. This is not a proof that upgrading an arbitrary
  existing proxy state establishes these invariants.

The main target uses the generated sanity checks to detect vacuous invariant
proofs and contains no `satisfy` rules. Review every invariant
and generated sanity verdict before treating a run as verified. These checks
do not separately establish the specific state transitions formerly requested
by the collateral-enabling and debt-opening witnesses. Historical diagnostic
reproductions above remain separate from the main target.
