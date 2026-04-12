/**
 * @title TokenizationSpoke Contract Specification
 * @notice Verify TokenizationSpokeInstance ERC4626 compliance and integrity properties (linked HubInstance + HubValidState)
 * @dev This spec verifies ERC4626 vault properties, immutable values, and basic integrity rules
 *
 * Verification Scope:
 * - ERC4626 compliance (convertToShares, convertToAssets, preview functions)
 * - Immutable values integrity
 * - View function integrity
 * - Basic state invariants
 * - Deposit/withdraw integrity (adapted from Spoke rules)
 * - Hub interaction integrity (HubInstance linked via TokenizationSpoke.conf)
 *
 * The following functions are out of scope:
 * - initialize
 * - permit related functions
 * - withSig entry points
 *
 * To run this spec:
 * certoraRun certora/conf/TokenizationSpoke.conf
 */

import "./symbolicRepresentation/ERC20s_CVL.spec";
import "./TokenizationSpokeBase.spec";
import "./HubValidState.spec";

// hub is defined in HubValidState.spec
using TokenizationSpokeInstance as tokenizationSpoke;

methods {
    // HubInstance envfree methods
    function hub.getAssetUnderlyingAndDecimals(uint256 assetId) external returns (address, uint8) envfree;
    function hub.getSpokeAddedShares(uint256 assetId, address spoke) external returns (uint256) envfree;
    function hub.MAX_ALLOWED_SPOKE_CAP() external returns (uint40) envfree;
}

////////////////////////////////////////////////////////////////////////////
//                                 RULES                                  //
////////////////////////////////////////////////////////////////////////////

/**
 * @title Total supply equals sum of per-account share balances
 * @link_property TokenizationSpoke valid state
 */
use invariant totalSupplySumOfBalances;

/**
 * @title Vault total supply matches hub recorded spoke added shares
 * @link_property TokenizationSpoke valid state
 */
invariant totalSupplyHubSupplySharesIntegrity()
    totalSupply() == hub.getSpokeAddedShares(currentContract.ASSET_ID, currentContract)
{
    preserved with (env e) {
        setup(e);
    }
}

/**
 * @title Total assets cover total shares (zero supply iff zero assets)
 * @notice ERC4626-style solvency: totalAssets is at least totalSupply in share units and zeros align
 * @link_property ERC4626 compliance
 */
rule totalAssetsIsAtLeastAsMuchAsTotalSupplyOfShares(env e) {
    setup(e);
    assert totalAssets(e) >= totalSupply();
    assert totalSupply() == 0 <=> totalAssets(e) == 0;
}


/**
 * @title convertToShares and convertToAssets are inverse operations
 * @notice Verifies ERC4626 requirement: convertToAssets(convertToShares(assets)) == assets (within rounding)
 * @link_property ERC4626 compliance
 */
rule convertToSharesAndAssetsInverse(uint256 assets) {
    env e;
    uint256 shares = convertToShares(e, assets);
    uint256 assetsBack = convertToAssets(e, shares);
    
    // Due to rounding, assetsBack may be slightly less than assets
    // But it should never be more than assets
    assert assetsBack <= assets;
    // And the difference should be minimal (within 1 wei per share)
    assert assets - assetsBack <= hub.previewAddByShares(e, currentContract.ASSET_ID, 1);
}

/**
 * @title convertToAssets and convertToShares are inverse operations
 * @notice Verifies ERC4626 requirement: convertToShares(convertToAssets(shares)) == shares (within rounding)
 * @link_property ERC4626 compliance
 */
rule convertToAssetsAndSharesInverse(uint256 shares) {
    env e;
    setup(e);
    uint256 assets = convertToAssets(e, shares);
    uint256 sharesBack = convertToShares(e, assets);
    
    // Due to rounding, sharesBack may be slightly less than shares
    // But it should never be more than shares
    assert sharesBack <= shares;
    // And the difference should be minimal (within 1 share)
    assert shares - sharesBack <= 1;
}

/**
 * @title previewDeposit matches convertToShares
 * @notice Verifies that previewDeposit returns the same value as convertToShares
 * @link_property ERC4626 compliance
 */
rule previewDepositMatchesConvertToShares(uint256 assets) {
    env e;
    uint256 previewShares = previewDeposit(e, assets);
    uint256 convertShares = convertToShares(e, assets);
    
    assert previewShares == convertShares;
}

/**
 * @title previewMint matches convertToAssets
 * @notice Verifies that previewMint returns the same value as convertToAssets within rounding
 * @link_property ERC4626 compliance
 */
rule previewMintMatchesConvertToAssets(uint256 shares) {
    env e;
    uint256 previewAssets = previewMint(e, shares);
    uint256 previewAssetsMax = previewMint(e, require_uint256(shares+1));
    uint256 convertAssets = convertToAssets(e, shares);
    
    assert previewAssets >= convertAssets && previewAssets <= previewAssetsMax;
}

/**
 * @title previewWithdraw matches convertToShares
 * @notice Verifies that previewWithdraw returns the same value as convertToShares within rounding
 * @link_property ERC4626 compliance
 */
rule previewWithdrawMatchesConvertToShares(uint256 assets) {
    env e;
    uint256 previewShares = previewWithdraw(e, assets);
    uint256 convertShares = convertToShares(e, assets);
    
    assert previewShares >= convertShares;
    assert previewShares <= convertShares + 1;
}

/**
 * @title previewRedeem matches convertToAssets
 * @notice Verifies that previewRedeem returns the same value as convertToAssets
 * @link_property ERC4626 compliance
 */
rule previewRedeemMatchesConvertToAssets(uint256 shares) {
    env e;
    uint256 previewAssets = previewRedeem(e, shares);
    uint256 convertAssets = convertToAssets(e, shares);
    
    assert previewAssets == convertAssets;
}

/**
 * @title totalAssets equals redeeming entire supply (ERC4626 accounting view)
 * @notice totalAssets matches previewRedeem(totalSupply()) for the live exchange rate
 * @link_property ERC4626 compliance
 */
rule totalAssets_equalsHubBalance {
    env e;
    uint256 totalAssets = totalAssets(e);
    uint256 totalSupply = totalSupply();
    uint256 previewRedeemTotal = previewRedeem(e, totalSupply);
    
    // totalAssets should equal previewRedeem(totalSupply()) per ERC4626
    assert totalAssets == previewRedeemTotal;
}


/**
 * @title Deposit increases receiver's share balance
 * @notice Verifies that deposit operation increases the receiver's share balance and transfers assets and only within the max deposit limit
 * @link_property TokenizationSpoke integrity
 */
rule deposit_integrity(uint256 assets, address receiver) {
    env e;
    setup(e);
    address asset = asset();
    uint256 sharesBefore = balanceOf(receiver);
    uint256 depositorBalanceBefore = tokenBalanceOf(asset, e.msg.sender);
    uint256 sharesExpected = previewDeposit(e, assets);
    uint256 maxDeposit = maxDeposit(e, e.msg.sender);
    
    uint256 sharesReceived = deposit(e, assets, receiver);
    
    uint256 sharesAfter = balanceOf(receiver);
    uint256 depositorBalanceAfter = tokenBalanceOf(asset, e.msg.sender);
    
    assert sharesReceived <= assets;
    assert sharesAfter == sharesBefore + sharesReceived;
    assert sharesReceived == sharesExpected;
    assert e.msg.sender != hub => depositorBalanceAfter == depositorBalanceBefore - assets;
}

/**
 * @title Zero assets deposit mints zero shares (and conversely)
 * @link_property TokenizationSpoke integrity
 */
rule zeroDepositZeroShares(uint assets, address receiver) {
    env e;

    uint shares = deposit(e, assets, receiver);

    assert shares == 0 <=> assets == 0;
}

/**
 * @title Mint increases receiver's share balance
 * @notice Verifies that mint operation increases the receiver's share balance and transfers assets
 * @link_property TokenizationSpoke integrity
 */
rule mint_integrity(uint256 shares, address receiver) {
    env e;
    setup(e);
    address asset = asset();
    uint256 sharesBefore = balanceOf(receiver);
    uint256 depositorBalanceBefore = tokenBalanceOf(asset, e.msg.sender);
    uint256 assetsExpected = previewMint(e, shares);
    uint256 maxMint = maxMint(e, receiver);

    uint256 assetsDeposited = mint(e, shares, receiver);
    
    uint256 sharesAfter = balanceOf(receiver);
    uint256 depositorBalanceAfter = tokenBalanceOf(asset, e.msg.sender);

    assert shares <= maxMint;
    assert assetsDeposited == assetsExpected;
    assert sharesAfter == sharesBefore + shares;
    assert e.msg.sender != hub => depositorBalanceAfter == depositorBalanceBefore - assetsDeposited;
}

/**
 * @title Withdraw decreases owner's share balance
 * @notice Verifies that withdraw operation decreases the owner's share balance and transfers assets
 * @link_property TokenizationSpoke integrity
 */
rule withdraw_integrity(uint256 assets, address receiver, address owner) {
    env e;
    setup(e);
    address asset = asset();
    uint256 sharesBefore = balanceOf(owner);
    uint256 receiverBalanceBefore = tokenBalanceOf(asset, receiver);
    
    uint256 sharesExpected = previewWithdraw(e, assets);
    uint256 sharesWithdrawn = withdraw(e, assets, receiver, owner);
    
    uint256 sharesAfter = balanceOf(owner);
    uint256 receiverBalanceAfter = tokenBalanceOf(asset, receiver);
    
    assert sharesAfter == sharesBefore - sharesWithdrawn;
    assert sharesWithdrawn == sharesExpected;
    assert receiver != hub => receiverBalanceAfter == receiverBalanceBefore + assets;
}

/**
 * @title Redeem decreases owner's share balance
 * @notice Verifies that redeem operation decreases the owner's share balance and transfers assets
 * @link_property TokenizationSpoke integrity
 */
rule redeem_integrity(uint256 shares, address receiver, address owner) {
    env e;
    setup(e);
    address asset = asset();
    uint256 sharesBefore = balanceOf(owner);
    uint256 receiverBalanceBefore = tokenBalanceOf(asset, receiver);
    
    uint256 assets = convertToAssets(e, shares);
    uint256 assetsRedeemed = redeem(e, shares, receiver, owner);

    uint256 sharesAfter = balanceOf(owner);
    uint256 receiverBalanceAfter = tokenBalanceOf(asset, receiver);
    
    assert sharesAfter == sharesBefore - shares;
    assert receiver != hub => receiverBalanceAfter == receiverBalanceBefore + assetsRedeemed;
    assert assetsRedeemed == assets;
}

/**
 * @title Redeeming full balance zeros the owner's shares
 * @link_property TokenizationSpoke integrity
 */
rule redeemingAllValidity() {
    address owner;
    address receiver;
    uint256 shares; require shares == balanceOf(owner);
    
    env e;
    setup(e);
    redeem(e, shares, receiver, owner);
    uint256 ownerBalanceAfter = balanceOf(owner);
    assert ownerBalanceAfter == 0;
}

// With-sig entry points excluded from onlyIncreaseOtherUsersShares filter
definition WithSigFunctions(method f) returns bool = f.selector == sig:depositWithSig(ITokenizationSpoke.TokenizedDeposit, bytes).selector || f.selector == sig:mintWithSig(ITokenizationSpoke.TokenizedMint, bytes).selector || f.selector == sig:withdrawWithSig(ITokenizationSpoke.TokenizedWithdraw, bytes).selector || f.selector == sig:redeemWithSig(ITokenizationSpoke.TokenizedRedeem, bytes).selector;

/**
 * @title Non-target users' shares and underlying do not decrease on vault ops
 * @notice Third parties (not msg.sender, not hub) never lose shares or asset balance from deposit/mint/withdraw/redeem/transferFrom paths
 * @link_property TokenizationSpoke integrity
 */
rule onlyIncreaseOtherUsersShares(address otherUser, method f) filtered { f -> !f.isView && !WithSigFunctions(f) } {
    env e;
    setup(e);
    require e.msg.sender != otherUser;
    require otherUser != hub;

    uint256 otherUserSharesBefore = balanceOf(otherUser);
    uint256 assetsBalanceBefore = tokenBalanceOf(asset(), otherUser);
    
    callFunctions(e, otherUser, f);
    
    uint256 otherUserSharesAfter = balanceOf(otherUser);
    uint256 assetsBalanceAfter = tokenBalanceOf(asset(), otherUser);

    assert otherUserSharesAfter >= otherUserSharesBefore;
    assert assetsBalanceAfter >= assetsBalanceBefore;
}

function callFunctions(env e, address otherUser, method f) {
    uint256 assets;
    uint256 shares;
    address owner;
    calldataarg args;
    address receiver;
    require owner != otherUser;
    if (f.selector == sig:deposit(uint256, address).selector) {
        deposit(e, assets, receiver);
    } else if (f.selector == sig:mint(uint256, address).selector) {
        mint(e, shares, receiver);
    } else if (f.selector == sig:withdraw(uint256, address, address).selector) {
        withdraw(e, assets, receiver, owner);
    } else if (f.selector == sig:redeem(uint256, address, address).selector) {
        redeem(e, shares, receiver, owner);
    } else if (f.selector == sig:transferFrom(address, address, uint256).selector) {
        address from; require from != otherUser;
        address to;
        uint256 amount;
        transferFrom(e, from, to, amount);
    } else {
        f(e, args);
    }
}

/**
 * @title maxWithdraw and maxRedeem respect redeemable liquidity
 * @notice maxWithdraw and maxRedeem are bounded by previewRedeem(balance) and balance respectively
 * @link_property TokenizationSpoke integrity
 */
rule maxWithdraw_respectsLiquidity(address owner, env e) {
    assert maxWithdraw(e, owner) <= previewRedeem(e, balanceOf(owner)) &&
        maxRedeem(e, owner) <= balanceOf(owner);
}


/**
 * @title convertToAssets is subadditive over share sums (weak additivity)
 * @link_property ERC4626 compliance
 */
rule convertToAssetsWeakAdditivity() {
    env e;
    uint256 sharesA; uint256 sharesB;
    require sharesA + sharesB < max_uint128
         && convertToAssets(e, sharesA) + convertToAssets(e, sharesB) < max_uint256
         && convertToAssets(e, require_uint256(sharesA + sharesB)) < max_uint256;
    assert convertToAssets(e, sharesA) + convertToAssets(e, sharesB) <= convertToAssets(e, require_uint256(sharesA + sharesB)),
        "converting sharesA and sharesB to assets then summing them must yield a smaller or equal result to summing them then converting";
}

/**
 * @title convertToShares is subadditive over asset sums (weak additivity)
 * @link_property ERC4626 compliance
 */
rule convertToSharesWeakAdditivity() {
    env e;
    uint256 assetsA; uint256 assetsB;
    require assetsA + assetsB < max_uint128
         && convertToShares(e, assetsA) + convertToShares(e, assetsB) < max_uint256
         && convertToShares(e, require_uint256(assetsA + assetsB)) < max_uint256;
    assert convertToShares(e, assetsA) + convertToShares(e, assetsB) <= convertToShares(e, require_uint256(assetsA + assetsB)),
        "converting assetsA and assetsB to shares then summing them must yield a smaller or equal result to summing them then converting";
}

/**
 * @title Conversion functions are monotone in shares and assets
 * @link_property ERC4626 compliance
 */
rule conversionWeakMonotonicity {
    env e;
    uint256 smallerShares; uint256 largerShares;
    uint256 smallerAssets; uint256 largerAssets;

    assert smallerShares < largerShares => convertToAssets(e, smallerShares) <= convertToAssets(e, largerShares),
        "converting more shares must yield equal or greater assets";
    assert smallerAssets < largerAssets => convertToShares(e, smallerAssets) <= convertToShares(e, largerAssets),
        "converting more assets must yield equal or greater shares";
}

/**
 * @title Round-trip conversion never inflates amounts (weak integrity)
 * @link_property ERC4626 compliance
 */
rule conversionWeakIntegrity() {
    env e;
    uint256 sharesOrAssets;
    assert convertToShares(e, convertToAssets(e, sharesOrAssets)) <= sharesOrAssets,
        "converting shares to assets then back to shares must return shares less than or equal to the original amount";
    assert convertToAssets(e, convertToShares(e, sharesOrAssets)) <= sharesOrAssets,
        "converting assets to shares then back to assets must return assets less than or equal to the original amount";
}

/**
 * @title convertTo round-trips bound original amount or shares from above
 * @link_property ERC4626 compliance
 */
rule convertToCorrectness(uint256 amount, uint256 shares) {
    env e;
    assert amount >= convertToAssets(e, convertToShares(e, amount));
    assert shares >= convertToShares(e, convertToAssets(e, shares));
}

/**
 * @title With ASSET == self and zero supply, state-changing calls keep zero supply
 * @notice Configuration edge case: no share inflation when underlying is the spoke itself
 * @link_property TokenizationSpoke integrity
 */
rule assetIsThisContract(method f) filtered { f -> !f.isView && !outOfScopeFunctions(f) } {
    require currentContract.ASSET == currentContract;
    requireInvariant totalSupplySumOfBalances();
    require totalSupply() == 0;
    env e;
    calldataarg args;
    f@withrevert(e, args);
    assert totalSupply() == 0;
}

function setup(env e) {
    requireInvariant totalSupplySumOfBalances();
    // Assuming the asset underlying is not the current contract itself
    require currentContract.ASSET != currentContract;
    // HUB._assets[ASSET_ID].underlying == TokenizationSpoke.asset()!= address(this)
    address underlying; uint8 decimals;
    (underlying, decimals) = hub.getAssetUnderlyingAndDecimals(currentContract.ASSET_ID);
    require underlying == currentContract.ASSET;
    require currentContract.ASSET_UNITS == limitedExp(10,decimals);
    require currentContract.MAX_ALLOWED_SPOKE_CAP == hub.MAX_ALLOWED_SPOKE_CAP();
    requireAllInvariants(currentContract.ASSET_ID, e);
    requireInvariant totalSupplyHubSupplySharesIntegrity();
}