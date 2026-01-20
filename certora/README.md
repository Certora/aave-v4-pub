# Certora Formal Verification

This folder contains the formal verification specifications for the Aave V4 protocol using the Certora Prover.

## Folder Structure

```
certora/
├── conf/                    # Configuration files for running the prover
│   ├── libs/               # Library-specific configurations
│   └── *.conf              # Main configuration files
├── harness/                 # Solidity harness contracts for verification
│   ├── HubHarness.sol      # Hub contract harness exposing internal functions
│   ├── LibBitHarness.sol   # LibBit library harness
│   ├── LiquidationLogicHarness.sol  # LiquidationLogic library harness
│   ├── MathWrapper.sol     # Math library wrapper for verification
│   └── PremiumWrapper.sol  # Premium library wrapper for verification
├── spec/                    # CVL specification files
│   ├── libs/               # Library specifications
│   └── symbolicRepresentation/  # Symbolic representations for CVL
├── runAll.sh               # Script to run all conf files
└── compileAll.sh           # Script to compile all contracts
```

## Key Properties Verified

The formal verification focuses on the following critical safety properties:

### Solvency & Share Rate
- **Share Rate Monotonicity** - The exchange rate between shares and assets never decreases, protecting LP token holders
- **Total Assets ≥ Total Shares** - Ensures the protocol remains solvent
- **External Solvency** - Hub underlying balance always covers total added assets

### Position Safety
- **No Collateral → No Debt** - Users without collateral cannot accumulate debt
- **Borrowing Flag Consistency** - Borrowing status accurately reflects drawn shares
- **Health Factor Maintenance** - User health stays above liquidation threshold after operations
- **Premium Debt Consistency** - Premium shares and offset maintain consistent relationship with drawn shares

### State Consistency
- **Spoke Isolation** - Operations on one spoke don't affect other spokes
- **Sum Invariants** - Sum of spoke supplies/drawn shares equals totals
- **Reserve ID Validity** - Reserve mappings remain consistent
- **Dynamic Config Consistency** - User dynamic config keys are consistent with reserve config

### Accrue Integrity
- **Idempotency** - Calling accrue twice is equivalent to calling once
- **Index Monotonicity** - Interest indices only increase

### Liquidation Safety
- **Healthy Accounts Protected** - Accounts with health factor above threshold cannot be liquidated
- **Debt Monotonicity** - Liquidation always reduces debt
- **Collateral Bounds** - Collateral seized does not exceed user's total collateral
- **Liquidation Bonus Bounds** - Bonus is bounded between no bonus and max bonus

## Prerequisites

1. Install the Certora Prover CLI:
   ```bash
   pip install certora-cli
   ```

2. Set your Certora API key:
   ```bash
   export CERTORAKEY=<your-api-key>
   ```

## Running the Prover

### Run All Configurations
```bash
./certora/runAll.sh
```

### Run a Single Configuration
```bash
certoraRun certora/conf/<config_file>.conf
```

### Run a Specific Rule
```bash
certoraRun certora/conf/<config_file>.conf --rule <rule_name> --msg "<description>"
```

### Documentation
For more information on the Certora Prover and CVL specification language, see:
- [Certora Documentation](https://docs.certora.com/)
- [CVL Language Reference](https://docs.certora.com/en/latest/docs/cvl/index.html)
- [Certora Prover CLI](https://docs.certora.com/en/latest/docs/prover/cli/index.html)

---

## Hub Specifications

### `HubBase.spec`
**Base definitions for Hub specifications.**

- **Imports:** `ERC20s_CVL.spec`, `Math_CVL.spec`, `common.spec`
- **Purpose:** Contains safe assumptions and summarizations used across all Hub spec files
- **Key Summaries:**
  - `calculateInterestRate` → NONDET
  - `Premium.calculatePremiumRay` → CVL implementation

### `Hub.spec`
**Main Hub verification rules.**

- **Config:** `certora/conf/Hub.conf`
- **Imports:** `ERC20s_CVL.spec`, `Math_CVL.spec`, `HubValidState.spec`
- **Purpose:** State change rules where validation functions are ignored, assuming `accrue` has been called
- **Key Summaries:** All `_validate*` functions → NONDET
- **Key Rules:**
  - `supplyExchangeRateIsMonotonic` - Share exchange rate never decreases (critical for LP token safety)
  - `noChangeToOtherSpoke` - Operations on one spoke don't affect other spokes' state
  - `totalAssetsCompareToSuppliedAmount` - Total assets always >= total shares (solvency)
  - `accrueWasCalled` - Ensures accrue is called before state-changing operations


### `HubValidState.spec`
**Hub valid state properties and invariants.**

- **Config:** `certora/conf/HubValidState.conf`, `certora/conf/HubValidState_totalAssets.conf`
- **Imports:** `ERC20s_CVL.spec`, `Math_CVL.spec`, `HubBase.spec`
- **Purpose:** Verifies invariants about the Hub's state, assuming a given drawnIndex and accrue was called
- **Key Features:**
  - Ghost variables for tracking spoke supply, drawn amounts, and premium offsets
  - Hooks on storage operations to maintain ghost consistency
  - Sum invariants for spoke data
- **Key Rules/Invariants:**
  - `solvency_external` - Hub underlying balance >= total added assets (external solvency)
  - `totalAssetsVsShares` - Total assets always >= total shares (share rate >= 1)
  - `sumOfSpokeSupply` - Sum of all spoke supplies equals total supply
  - `sumOfSpokeDrawnShares` - Sum of all spoke drawn shares equals total drawn
  - `premiumOffset_Integrity` - Premium offset tracking consistency
- **Additional Config:** `HubValidState_totalAssets.conf` runs `totalAssetsVsShares` with parallel splitting 

### `HubIntegrityRules.spec`
**Hub integrity verification rules.**

- **Config:** `certora/conf/HubIntegrity.conf`
- **Imports:** `ERC20s_CVL.spec`, `Math_CVL.spec`, `HubValidState.spec`
- **Purpose:** Verifies that state changes are consistent (e.g., add increases balances, remove decreases them)
- **Key Rules:**
  - `nothingForZero_add` - Add operation increases balances
  - `nothingForZero_remove` - Remove operation decreases balances


### `HubAccrueIntegrity.spec`
**Accrue function integrity proofs.**

- **Config:** `certora/conf/HubAccrueIntegrity.conf`
- **Imports:** `HubBase.spec`
- **Purpose:** Unit test properties of `AssetLogic.accrue()` function
- **Key Rules:**
  - `runningTwiceIsEquivalentToOne` - Idempotency of accrue
  - Index monotonicity rules
  - Interest rate calculation rules

### `HubAccrueSupplyRate.spec`
**Supply rate verification.**

- **Config:** `certora/conf/HubAccrueSupplyRate.conf`
- **Purpose:** Verifies supply rate calculations

### `HubAccrueUnrealizedFee.spec`
**Unrealized fee verification.**

- **Config:** `certora/conf/HubAccrueUnrealizedFee.conf`
- **Purpose:** Verifies unrealized fee calculations

### `HubAdditivity.spec`
**Additivity properties of Hub operations.**

- **Config:** `certora/conf/HubAdditivity.conf`
- **Imports:** `ERC20s_CVL.spec`, `Math_CVL.spec`, `SharesMath.spec`
- **Purpose:** Verifies that splitting operations is less beneficial than single operations
- **Key Rules:** Additivity proofs for `add`, `remove`, `draw`, `restore`, `reportDeficit`, `eliminateDeficit`


---

## Spoke Specifications

### `SpokeBase.spec`
**Base definitions for Spoke specifications.**

- **Imports:** `SpokeBaseSummaries.spec`
- **Purpose:** Safe assumptions and summarizations for all Spoke spec files
- **Key Features:**
  - `setup()` function with common requirements
  - `outOfScopeFunctions` definition for filtering
  - `increaseCollateralOrReduceDebtFunctions` definition
  - Paused/frozen flag ghost variables

### `SpokeBaseSummaries.spec`
**Method summaries for Spoke specifications.**

- **Imports:** `common.spec`, `SymbolicPositionStatus.spec`
- **Purpose:** Contains method summaries shared across Spoke specs
- **Key Summaries:**
  - Sorting functions → CVL implementation
  - Price functions → Symbolic representation
  - Authority checks → NONDET

### `Spoke.spec`
**Main Spoke verification rules and invariants.**

- **Config:** `certora/conf/Spoke.conf`, `certora/conf/Spoke_noCollateralNoDebt.conf`
- **Imports:** `SpokeBase.spec`, `SymbolicPositionStatus.spec`, `SymbolicHub.spec`
- **Purpose:** Spoke-independent verification (no link to Hub)
- **Key Features:**
  - Symbolic Hub summaries for external calls
  - Index tracking per asset per block
  - User position invariants
  - userGhost tracking for single-user operations
- **Key Rules:**
  - `increaseCollateralOrReduceDebtFunctions` - Functions either increase collateral or reduce debt
  - `paused_noChange` - No state changes when paused
  - `frozen_onlyReduceDebtAndCollateral` - Frozen reserves only allow debt/collateral reduction
  - `updateUserRiskPremium_preservesPremiumDebt` - Risk premium updates preserve premium debt
  - `noCollateralNoDebt` - User with no collateral cannot have debt (critical safety property)
  - `collateralFactorNotZero` - Borrowed reserves must have non-zero collateral factor
  - `deterministicUserDebtValue` - User debt calculation is deterministic
- **Key Invariants:**
  - `isBorrowingIFFdrawnShares` - Borrowing flag set iff user has drawn shares
  - `drawnSharesZero` - Zero drawn shares implies zero premium shares
  - `validReserveId` - Reserve ID validity and consistency
  - `validReserveId_single` - Single reserve ID validity
  - `validReserveId_singleUser` - Reserve ID validity for single user
  - `uniqueAssetIdPerReserveId` - Each reserve maps to unique asset
  - `realizedPremiumRayConsistency` - Premium offset <= premium shares * drawn index
  - `drawnSharesRiskEQPremiumShares` - Drawn shares * risk premium == premium shares
  - `dynamicConfigKeyConsistency` - User config key <= reserve config key
- **Additional Config:** `Spoke_noCollateralNoDebt.conf` runs `noCollateralNoDebt` with parallel splitting prover args

### `SpokeIntegrity.spec`
**Spoke operation integrity rules.**

- **Config:** `certora/conf/SpokeIntegrity.conf`
- **Imports:** `SpokeBase.spec`, `SymbolicPositionStatus.spec`, `SymbolicHub.spec`
- **Purpose:** Verifies integrity of individual Spoke operations
- **Key Rules:**
  - `nothingForZero_supply` - Supply with zero amount has no effect
  - `nothingForZero_withdraw` - Withdraw with zero amount has no effect
  - `nothingForZero_borrow` - Borrow with zero amount has no effect
  - `nothingForZero_repay` - Repay with zero amount has no effect
  - `supply_noChangeToOther` - Supply doesn't affect other users
  - `withdraw_noChangeToOther` - Withdraw doesn't affect other users
  - `borrow_noChangeToOther` - Borrow doesn't affect other users
  - `repay_noChangeToOther` - Repay doesn't affect other users
  - `onlyPositionManagerCanChange` - Only position manager can modify positions

### `SpokeHealthCheck.spec`
**Health factor verification.**

- **Config:** `certora/conf/SpokeHealthCheck.conf`
- **Imports:** `SpokeBase.spec`, `SymbolicHub.spec`
- **Purpose:** Verifies that health factor is checked after position updates
- **Key Rules:**
  - `userHealthStaysAboveThreshold` - Health factor maintained after operations

### `SpokeHealthFactor.spec`
**Advanced health factor verification with ghost tracking.**

- **Config:** `certora/conf/SpokeHealthFactor.conf`
- **Imports:** `SpokeBaseSummaries.spec`, `SymbolicPositionStatus.spec`
- **Purpose:** Verifies health factor using ghost variables for collateral and debt tracking
- **Key Features:**
  - Ghost variables for total collateral and debt values
  - Hooks on position storage to track value changes
  - Symbolic price functions
- **Key Rules:**
  - `userHealthAboveThreshold` - Health factor stays above liquidation threshold

### `SpokeUserIntegrity.spec`
**User position integrity.**

- **Config:** `certora/conf/SpokeUserIntegrity.conf`
- **Purpose:** Verifies that only one user's account is updated at a time

### `SpokeHubIntegrity.spec`
**Spoke-Hub integration verification.**

- **Config:** `certora/conf/SpokeWithHub.conf`
- **Imports:** `SpokeBase.spec`, `SymbolicPositionStatus.spec`, `HubValidState.spec`
- **Purpose:** Verifies consistency between Spoke user positions and Hub spoke data
- **Key Invariants:**
  - `userDrawnShareConsistency` - User drawn shares match Hub records
  - `userSuppliedShareConsistency` - User supplied shares match Hub records
  - `userPremiumShareConsistency` - Premium shares consistency
  - `userPremiumOffsetConsistency` - Premium offset consistency
  - `underlyingAssetConsistency` - Underlying asset matches Hub asset

---

## Liquidation Specifications

### `Liquidation.spec`
**Liquidation operation verification.**

- **Config:** `certora/conf/Liquidation.conf`
- **Imports:** `SpokeBase.spec`, `SymbolicPositionStatus.spec`, `SymbolicHub.spec`
- **Purpose:** Verifies safety properties of liquidation operations
- **Key Rules:**
  - `sanityCheck` - Basic sanity check for liquidation
  - `borrowingFlagSetIFFdrawnShares_liquidationCall` - Borrowing flag consistency after liquidation
  - `healthyAccountCannotBeLiquidated` - Accounts above health threshold cannot be liquidated
  - `paused_noLiquidation` - No liquidation when paused
  - `monotonicityOfDebtDecrease_liquidationCall` - Liquidation always decreases debt
  - `moreThanOneCollateral_noReportDeficit` - No deficit reported when multiple collaterals exist
  - `noChangeToOtherAccounts_liquidationCall` - Liquidation doesn't affect uninvolved accounts

### `LiquidationUserIntegrity.spec`
**Liquidation user isolation verification.**

- **Config:** `certora/conf/LiquidationUserIntegrity.conf`
- **Imports:** `SpokeBase.spec`, `SymbolicPositionStatus.spec`, `SymbolicHub.spec`
- **Purpose:** Verifies that liquidation only affects the liquidated user
- **Key Rules:**
  - `onlyOneUserDebtChanges_liquidationCall` - Only liquidated user's debt changes

---

## Library Specifications

### `libs/Math.spec`
**Mathematical function verification.**

- **Config:** `certora/conf/libs/Math.conf`
- **Purpose:** Proves CVL representations match Solidity implementations
- **Verified Functions:**
  - `mulDivDown`, `mulDivUp`
  - `rayMulDown`, `rayMulUp`, `rayDivDown`, `rayDivUp`
  - `wadDivDown`, `wadDivUp`
  - `percentMulDown`, `percentMulUp`
  - `fromRayUp`, `toRay`

### `libs/SharesMath.spec`
**Shares math library verification.**

- **Config:** `certora/conf/libs/SharesMath.conf`
- **Purpose:** Proves mathematical properties of share calculations
- **Key Rules:**
  - Monotonicity of `toSharesUp`, `toSharesDown`, `toAssetsUp`, `toAssetsDown`
  - Additivity properties
  - Inverse relationships

### `libs/LiquidationLogic.spec`
**Liquidation amounts calculation verification.**

- **Config:** `certora/conf/libs/LiquidationLogic.conf`
- **Harness:** `LiquidationLogicHarness.sol`
- **Purpose:** Verifies `_calculateLiquidationAmounts` function properties
- **Key Rules:**
  - `sanityCheck` - Basic sanity check
  - `debtToLiquidateNotExceedBalance` - Debt to liquidate bounded by reserve balance
  - `debtToLiquidateNotExceedDebtToCover` - Debt to liquidate bounded by debt to cover
  - `collateralToLiquidatorNotExceedTotal` - Collateral seized bounded by total
  - `collateralToLiquidateValueLessThanDebtToLiquidate_assets` - Collateral value <= debt value (assets)
  - `collateralToLiquidateValueLessThanDebtToLiquidate_shares` - Collateral value <= debt value (shares)
  - `collateralToLiquidateValueLessThanDebtToLiquidate_fullRayDebt` - Collateral value <= debt value (full ray)

### `libs/LiquidationLogic_Bonus.spec`
**Liquidation bonus calculation verification.**

- **Config:** `certora/conf/libs/LiquidationLogic_Bonus.conf`
- **Harness:** `LiquidationLogicHarness.sol`
- **Purpose:** Verifies `calculateLiquidationBonus` function properties
- **Key Rules:**
  - `sanityCheck` - Basic sanity check
  - `maxBonusWhenLowHealthFactor` - Max bonus when health factor <= threshold for max bonus
  - `bonusIsAtLeastNoBonus` - Bonus >= PERCENTAGE_FACTOR (no negative bonus)
  - `bonusDoesNotExceedMax` - Bonus <= max liquidation bonus
  - `monotonicityOfBonus` - Lower health factor → higher bonus
  - `bonusAtThreshold` - Bonus equals PERCENTAGE_FACTOR at liquidation threshold
  - `zeroBonusFactorMeansNoMinBonus` - Zero bonus factor means no minimum bonus

### `libs/DebtToTarget.spec`
**Debt to target health factor calculation verification.**

- **Config:** `certora/conf/libs/DebtToTarget.conf`
- **Harness:** `SpokeHarness.sol`
- **Purpose:** Verifies `_calculateDebtToTargetHealthFactor` function properties

### `libs/ProcessUserAccountData.spec`
**User account data processing verification.**

- **Config:** `certora/conf/libs/ProcessUserAccountData.conf`
- **Harness:** `SpokeHarness.sol`
- **Purpose:** Verifies `_processUserAccountData` function properties

### `libs/LibBit.spec`
**Bit manipulation library verification.**

- **Config:** `certora/conf/libs/LibBit.conf`

### `libs/PositionStatus.spec`
**Position status verification.**

- **Config:** `certora/conf/libs/PositionStatus.conf`

### `libs/Premium.spec`
**Premium calculation verification.**

- **Config:** `certora/conf/libs/Premium.conf`
- **Imports:** `HubBase.spec`, `common.spec`
- **Purpose:** Verifies that `Premium.calculatePremiumRay` matches its CVL summarization
- **Key Rules:**
  - `calculatePremiumRay_equivalence` - Solidity matches CVL implementation

---

## Symbolic Representations

### `symbolicRepresentation/Math_CVL.spec`
**CVL implementations of math functions.**

- **Purpose:** Provides CVL equivalents of Solidity math functions for use in summaries
- **Functions:** `mulDivDownCVL`, `mulDivUpCVL`, `mulDivRayDownCVL`, `mulDivRayUpCVL`, `divRayUpCVL`, `mulRayCVL`

### `symbolicRepresentation/ERC20s_CVL.spec`
**ERC20 symbolic representations.**

- **Purpose:** Symbolic handling of ERC20 token interactions

### `symbolicRepresentation/SymbolicHub.spec`
**Symbolic Hub for Spoke verification.**

- **Purpose:** Allows verifying Spoke independently of Hub implementation
- **Key Features:**
  - Ghost mappings for asset indices per block
  - CVL implementations of Hub functions (add, remove, draw, restore, etc.)
  - Asset underlying address tracking

### `symbolicRepresentation/SymbolicPositionStatus.spec`
**Symbolic position status handling.**

- **Purpose:** Provides ghost mappings and CVL functions for position status
- **Key Features:**
  - `isBorrowing` and `isUsingAsCollateral` ghost mappings
  - `nextBorrowingCVL` and `nextCollateralCVL` iteration functions
  - Method summaries for PositionStatusMap library functions

### `symbolicRepresentation/VerifySymbolicPositionStatus.spec`
**Verification of symbolic position status.**

- **Config:** `certora/conf/libs/VerifySymbolicPositionStatus.conf`
- **Purpose:** Verifies that symbolic representations match actual implementations

---

## Common Specifications

### `common.spec`
**Shared method summaries.**

- **Purpose:** Common summaries used in both Hub and Spoke specifications
- **Key Summaries:**
  - `mulDivDown`, `mulDivUp` → CVL implementations
  - `rayMulDown`, `rayMulUp`, `rayDivDown` → CVL implementations
  - `wadDivUp`, `wadDivDown` → CVL implementations
  - `percentMulDown`, `percentMulUp` → CVL implementations
- **Ghost Variables:**
  - `RAY` = 10^27
  - `WAD` = 10^18
  - `PERCENTAGE_FACTOR` = 10000

---

## Dependency Graph

```
common.spec
    ├── HubBase.spec
    │       ├── Hub.spec
    │       ├── HubValidState.spec
    │       │       ├── HubIntegrityRules.spec
    │       │       └── SpokeHubIntegrity.spec
    │       ├── HubAccrueIntegrity.spec
    │       ├── HubAccrueSupplyRate.spec
    │       ├── HubAccrueUnrealizedFee.spec
    │       └── HubAdditivity.spec (via SharesMath.spec)
    │
    └── SpokeBaseSummaries.spec
            └── SpokeBase.spec
                    ├── Spoke.spec
                    ├── SpokeIntegrity.spec
                    ├── SpokeHealthCheck.spec
                    ├── SpokeHealthFactor.spec
                    ├── SpokeUserIntegrity.spec
                    ├── SpokeHubIntegrity.spec
                    ├── Liquidation.spec
                    └── LiquidationUserIntegrity.spec

symbolicRepresentation/
    ├── Math_CVL.spec (used by most specs)
    ├── ERC20s_CVL.spec (used by most specs)
    ├── SymbolicHub.spec (used by Spoke specs)
    ├── SymbolicPositionStatus.spec (used by Spoke specs)
    └── VerifySymbolicPositionStatus.spec

libs/
    ├── Math.spec
    ├── SharesMath.spec
    ├── LibBit.spec
    ├── PositionStatus.spec
    ├── Premium.spec
    ├── LiquidationLogic.spec
    └── LiquidationLogic_Bonus.spec
```

---

## Harness Contracts

### `HubHarness.sol`
Exposes internal Hub functions for verification:
- `accrueInterest()` - Exposes `AssetLogic.accrue()`

### `MathWrapper.sol`
Wraps math library functions for direct verification:
- Exposes `WadRayMath` functions: `rayMulDown`, `rayMulUp`, `rayDivDown`, `rayDivUp`, `wadDivDown`, `wadDivUp`
- Exposes `MathUtils` functions: `mulDivDown`, `mulDivUp`
- Exposes `PercentageMath` functions: `percentMulDown`, `percentMulUp`

### `LibBitHarness.sol`
Wraps LibBit library for verification.

### `PremiumWrapper.sol`
Wraps Premium library for verification:
- Exposes `Premium.calculatePremiumRay()` for CVL equivalence testing

### `LiquidationLogicHarness.sol`
Wraps LiquidationLogic library for verification:
- Exposes `_calculateLiquidationAmounts()` for liquidation amount verification
- Exposes `calculateLiquidationBonus()` for bonus calculation verification

### `SpokeHarness.sol`
Wraps Spoke functions for verification:
- Exposes `_calculateDebtToTargetHealthFactor()` for debt calculation verification
- Exposes `_processUserAccountData()` for account data processing verification

---

## Tips for Running Verification

1. **Use Build Cache:** Most conf files have `"build_cache": true` to speed up repeated runs.

2. **Split Long-Running Rules:** Use `--split_rules` for rules that may timeout:
   ```bash
   certoraRun certora/conf/Spoke.conf --split_rules drawnSharesZero
   ```

3. **Run Specific Rules:** Use `--rule` to run individual rules:
   ```bash
   certoraRun certora/conf/Hub.conf --rule totalAssetsCompareToSuppliedAmount --msg "Hub totalAssets"
   ```

4. **Check Commented Split Rules:** Some conf files have commented `split_rules`. When running manually, add them as flags:
   ```bash
   # For Hub.conf with //"split_rules": ["noChangeToOtherSpoke","supplyExchangeRateIsMonotonic"]
   certoraRun certora/conf/Hub.conf --split_rules noChangeToOtherSpoke supplyExchangeRateIsMonotonic
   ```

5. View Results: Check the Certora Prover dashboard at https://prover.certora.com

---

## Verification Rules and Invariants

| Spec File | Rule Name | link |
| :--- | :--- | :--- |
| `Spoke.spec` | `increaseCollateralOrReduceDebtFunctions` | |
| `Spoke.spec` | `paused_noChange` | |
| `Spoke.spec` | `frozen_onlyReduceDebtAndCollateral` | |
| `Spoke.spec` | `updateUserRiskPremium_preservesPremiumDebt` | |
| `Spoke.spec` | `isBorrowingIFFdrawnShares` | |
| `Spoke.spec` | `drawnSharesZero` | |
| `Spoke.spec` | `validReserveId` | |
| `Spoke.spec` | `validReserveId_single` | |
| `Spoke.spec` | `validReserveId_singleUser` | |
| `Spoke.spec` | `uniqueAssetIdPerReserveId` | |
| `Spoke.spec` | `realizedPremiumRayConsistency` | |
| `Spoke.spec` | `drawnSharesRiskEQPremiumShares` | |
| `Spoke.spec` | `noCollateralNoDebt` | |
| `Spoke.spec` | `collateralFactorNotZero` | |
| `Spoke.spec` | `deterministicUserDebtValue` | |
| `Spoke.spec` | `dynamicConfigKeyConsistency` | |
| `liquidation.spec` | `sanityCheck` | |
| `liquidation.spec` | `borrowingFlagSetIFFdrawnShares_liquidationCall` | |
| `liquidation.spec` | `healthyAccountCannotBeLiquidated` | |
| `liquidation.spec` | `paused_noLiquidation` | |
| `liquidation.spec` | `monotonicityOfDebtDecrease_liquidationCall` | |
| `liquidation.spec` | `noChangeToOtherAccounts_liquidationCall` | |
| `SpokeHealthFactor.spec` | `belowThresholdReverting` | |
| `SpokeHealthFactor.spec` | `userHealthBelowThresholdCanOnlyIncreaseHealthFactor` | https://prover.certora.com/output/40726/c1df8f0ddf564a41b019f9ec3f2d7d4b/ |
| `SpokeHealthFactor.spec` | `userHealthBelowThresholdCanOnlyIncreaseHealthFactor setUsingAsCollateral` | https://prover.certora.com/output/40726/6d0934d9310244bbb6f98859448f3ae7 |
| `SpokeHealthFactor.spec` | `userHealthAboveThreshold` | |
| `SpokeIntegrity.spec` | `nothingForZero_supply` | |
| `SpokeIntegrity.spec` | `nothingForZero_withdraw` | |
| `SpokeIntegrity.spec` | `nothingForZero_borrow` | |
| `SpokeIntegrity.spec` | `nothingForZero_repay` | |
| `SpokeIntegrity.spec` | `supply_noChangeToOther` | |
| `SpokeIntegrity.spec` | `withdraw_noChangeToOther` | |
| `SpokeIntegrity.spec` | `borrow_noChangeToOther` | |
| `SpokeIntegrity.spec` | `repay_noChangeToOther` | |
| `SpokeIntegrity.spec` | `onlyPositionManagerCanChange` | |
| `SpokeUserIntegrity.spec` | `userIntegrity` | |
| `SpokeHubIntegrity.spec` | `userDrawnShareConsistency` | |
| `SpokeHubIntegrity.spec` | `userPremiumShareConsistency` | |
| `SpokeHubIntegrity.spec` | `userPremiumOffsetConsistency` | |
| `SpokeHubIntegrity.spec` | `userSuppliedShareConsistency` | |
| `SpokeHubIntegrity.spec` | `repay_debtDecrease` | |
| `SpokeHubIntegrity.spec` | `repay_zeroDebt` | |
| `Hub.spec` | `supplyExchangeRateIsMonotonic` | |
| `Hub.spec` | `noChangeToOtherSpoke` | |
| `Hub.spec` | `accrueWasCalled` | |
| `Hub.spec` | `lastUpdateTimestamp_notChanged` | |
| `Hub.spec` | `totalAssetsCompareToSuppliedAmount_virtual` | |
| `Hub.spec` | `totalAssetsCompareToSuppliedAmount_noVirtual` | |
| `HubValidState.spec` | `validAssetId` | |
| `HubValidState.spec` | `sumOfSpokeSupplyShares` | |
| `HubValidState.spec` | `sumOfSpokeDrawnShares` | |
| `HubValidState.spec` | `sumOfSpokePremiumDrawnShares` | |
| `HubValidState.spec` | `sumOfSpokePremiumOffset` | |
| `HubValidState.spec` | `sumOfSpokeDeficit` | |
| `HubValidState.spec` | `drawnIndexMin` | |
| `HubValidState.spec` | `liquidityFee_upper_bound` | |
| `HubValidState.spec` | `premiumOffset_Integrity` | |
| `HubValidState.spec` | `totalAssetsVsShares` | |
| `HubValidState.spec` | `totalAssetsVsShares_eliminateDeficit` | |
| `HubIntegrityRules.spec` | `assetToSpokesIntegrity` | |
| `HubIntegrityRules.spec` | `underlyingAssetsIntegrity` | |
| `HubIntegrityRules.spec` | `nothingForZero_add` | |
| `HubIntegrityRules.spec` | `nothingForZero_remove` | |
| `HubIntegrityRules.spec` | `nothingForZero_draw` | |
| `HubIntegrityRules.spec` | `nothingForZero_restore` | |
| `HubIntegrityRules.spec` | `nothingForZero_reportDeficit` | |
| `HubIntegrityRules.spec` | `nothingForZero_eliminateDeficit` | |
| `HubIntegrityRules.spec` | `nothing_for_zero_sweep` | |
| `HubIntegrityRules.spec` | `nothing_for_zero_reclaim` | |
| `HubIntegrityRules.spec` | `add_integrity` | |
| `HubIntegrityRules.spec` | `remove_integrity` | |
| `HubIntegrityRules.spec` | `draw_integrity` | |
| `HubIntegrityRules.spec` | `restore_integrity` | |
| `HubIntegrityRules.spec` | `reportDeficit_integrity` | |
| `HubIntegrityRules.spec` | `eliminateDeficit_integrity` | |
| `HubIntegrityRules.spec` | `sweep_integrity` | |
| `HubIntegrityRules.spec` | `reclaim_integrity` | |
| `HubIntegrityRules.spec` | `reportDeficitSameAsPreviewRestoreByAssets` | |
| `HubIntegrityRules.spec` | `validSpokeOnly` | |
| `HubIntegrityRules.spec` | `frontRunOnRefreshPremium` | |
| `HubAdditivity.spec` | `addAdditivity` | |
| `HubAdditivity.spec` | `removeAdditivity` | |
| `HubAdditivity.spec` | `drawAdditivity` | |
| `HubAdditivity.spec` | `restoreAdditivity` | |
| `HubAdditivity.spec` | `reportDeficitAdditivity` | |
| `HubAdditivity.spec` | `eliminateDeficitAdditivity` | |
| `HubAccrueIntegrity.spec` | `runningTwiceIsEquivalentToOne` | |
| `HubAccrueIntegrity.spec` | `baseDebtIndexMin_accrue` | |
| `HubAccrueIntegrity.spec` | `lastUpdateTimestamp_notInFuture` | |
| `HubAccrueIntegrity.spec` | `noChangeToOtherFields_accrue` | |
| `HubAccrueIntegrity.spec` | `baseDebtIndex_increasing` | |
| `HubAccrueIntegrity.spec` | `premiumOffset_Integrity_accrue` | |
| `HubAccrueIntegrity.spec` | `viewFunctionsIntegrity` | |
| `HubAccrueIntegrity.spec` | `viewFunctionsRevertIntegrity` | |
| `HubAccrueSupplyRate.spec` | `accrueSupplyRate` | |
| `HubAccrueUnrealizedFee.spec` | `checkAssumptionTotalAddedShares` | |
| `HubAccrueUnrealizedFee.spec` | `shareRate_withoutAccrue_time_monotonic` | |
| `HubAccrueUnrealizedFee.spec` | `previewRemoveByShares_withoutAccrue_time_monotonic` | |
| `HubAccrueUnrealizedFee.spec` | `previewAddByAssets_withoutAccrue_time_monotonic` | |
| `HubAccrueUnrealizedFee.spec` | `previewAddByShares_withoutAccrue_time_monotonic` | |
| `HubAccrueUnrealizedFee.spec` | `previewRemoveByAssets_withoutAccrue_time_monotonic` | |
| `HubAccrueUnrealizedFee.spec` | `previewDrawByAssets_withoutAccrue_time_monotonic` | |
| `HubAccrueUnrealizedFee.spec` | `previewDrawByShares_withoutAccrue_time_monotonic` | |
| `HubAccrueUnrealizedFee.spec` | `previewRestoreByAssets_withoutAccrue_time_monotonic` | |
| `HubAccrueUnrealizedFee.spec` | `previewRestoreByShares_withoutAccrue_time_monotonic` | |
| `HubAccrueUnrealizedFee.spec` | `feeAmountIncrease` | |
| `HubAccrueUnrealizedFee.spec` | `maxgetUnrealizedFees` | |
| `HubAccrueUnrealizedFee.spec` | `lastUpdateTimestampSameAsBlockTimestamp` | |
| `LiquidationRepotDeficit.spec` | `moreThanOneCollateral_noReportDeficit` | https://prover.certora.com/output/40726/521bb07a52de477ba0fa27cfc787fc2f/|
| `LiquidationUserIntegrity.spec` | `onlyOneUserDebtChanges_liquidationCall` | |
| `libs/LiquidationLogic.spec` | `sanityCheck` | |
| `libs/LiquidationLogic.spec` | `debtToLiquidateNotExceedBalance` | |
| `libs/LiquidationLogic.spec` | `debtToLiquidateNotExceedDebtToCover` | |
| `libs/LiquidationLogic.spec` | `collateralToLiquidatorNotExceedTotal` | |
| `libs/LiquidationLogic.spec` | `collateralToLiquidateValueLessThanDebtToLiquidate_assets` | |
| `libs/LiquidationLogic.spec` | `collateralToLiquidateValueLessThanDebtToLiquidate_shares` | |
| `libs/LiquidationLogic.spec` | `collateralToLiquidateValueLessThanDebtToLiquidate_fullRayDebt` | |
| `libs/LiquidationLogic_Bonus.spec` | `sanityCheck` | |
| `libs/LiquidationLogic_Bonus.spec` | `maxBonusWhenLowHealthFactor` | |
| `libs/LiquidationLogic_Bonus.spec` | `bonusIsAtLeastNoBonus` | |
| `libs/LiquidationLogic_Bonus.spec` | `bonusDoesNotExceedMax` | |
| `libs/LiquidationLogic_Bonus.spec` | `monotonicityOfBonus` | |
| `libs/LiquidationLogic_Bonus.spec` | `bonusAtThreshold` | |
| `libs/LiquidationLogic_Bonus.spec` | `zeroBonusFactorMeansNoMinBonus` | |
| `libs/DebtToTarget.spec` | `sanityCheck` | |
| `libs/DebtToTarget.spec` | `zeroDebtIfHealthFactorAtTarget` | |
| `libs/DebtToTarget.spec` | `monotonicityOfHealthFactor` | |
| `libs/DebtToTarget.spec` | `monotonicityOfTargetHealthFactor` | |
| `libs/ProcessUserAccountData.spec` | `sanityCheck` | |
| `libs/ProcessUserAccountData.spec` | `zeroDataIfNoPositions` | |
| `libs/ProcessUserAccountData.spec` | `collateralValueIntegrity` | |

