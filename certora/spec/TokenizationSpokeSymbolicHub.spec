/**
 * @title TokenizationSpoke Contract Specification
 * @notice Verify TokenizationSpokeInstance with a symbolic representation of the Hub
 *
 * To run this spec:
 * certoraRun certora/conf/TokenizationSpokeSymbolicHub.conf
 */

import "./symbolicRepresentation/ERC20s_CVL.spec";
import "./TokenizationSpokeBase.spec";
import "./symbolicRepresentation/SymbolicHub.spec";

using TokenizationSpokeInstance as tokenizationSpoke;

////////////////////////////////////////////////////////////////////////////
//                              GHOSTS                                    //
////////////////////////////////////////////////////////////////////////////

// RAY (1e27) used by SymbolicHub ghost axioms; WadRayMath constant
ghost uint256 RAY {
    axiom RAY == 10^27;
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
 * @title Deposit then redeem of those shares does not drain pool (symbolic hub)
 * @notice totalAssets after deposit+redeem is at least totalAssets before (rounding favors vault)
 * @link_property TokenizationSpoke integrity
 */
rule dustFavorsTheHouse(uint256 assetsIn) {
    env e;

    require e.msg.sender != currentContract;
    setup();

    uint256 balanceBefore = totalAssets(e);

    uint256 shares = deposit(e, assetsIn, e.msg.sender);
    redeem(e, shares, e.msg.sender, e.msg.sender);

    uint256 balanceAfter = totalAssets(e);

    assert balanceAfter >= balanceBefore;
}

/**
 * @title Redeem call order independence for two users
 * @notice Swapping order of two redeems from same initial state does not make the first revert
 * @link_property TokenizationSpoke front running safety
 */
rule noFrontRunningOnRedeem() {
    env e1;
    env e2;
    uint256 shares1;
    uint256 shares2;

    require e1.msg.sender != hub() && e2.msg.sender != hub();
    storage init_state = lastStorage;
    setup();

    redeem(e1, shares1, e1.msg.sender, e1.msg.sender);
    redeem(e2, shares2, e2.msg.sender, e2.msg.sender);

    // change order - should not fail
    redeem(e2, shares2, e2.msg.sender, e2.msg.sender) at init_state;
    redeem@withrevert(e1, shares1, e1.msg.sender, e1.msg.sender);

    assert !lastReverted;
}

/**
 * @title Withdraw call order independence for two users
 * @notice Swapping order of two withdraws from same initial state does not make the first revert
 * @link_property TokenizationSpoke front running safety
 */
rule noFrontRunningOnWithdraw() {
    env e1;
    env e2;
    uint256 assets1;
    uint256 assets2;

    require e1.msg.sender != hub() && e2.msg.sender != hub();
    storage init_state = lastStorage;
    setup();

    withdraw(e1, assets1, e1.msg.sender, e1.msg.sender);
    withdraw(e2, assets2, e2.msg.sender, e2.msg.sender);

    // change order - should not fail
    withdraw(e2, assets2, e2.msg.sender, e2.msg.sender) at init_state;
    withdraw@withrevert(e1, assets1, e1.msg.sender, e1.msg.sender);

    assert !lastReverted;
}

function setup() {
    requireInvariant totalSupplySumOfBalances();

    // Assuming the asset underlying is not the current contract itself
    require currentContract.ASSET != currentContract;

    // HUB._assets[ASSET_ID].underlying == TokenizationSpoke.asset() != address(this)
    require assetUnderlying[currentContract.ASSET_ID] == currentContract.ASSET;
}
