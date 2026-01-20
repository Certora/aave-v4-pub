import "../common.spec";
import "../SpokeBaseSummaries.spec";
import "../symbolicRepresentation/SymbolicHub.spec";
import "../symbolicRepresentation/SymbolicPositionStatus.spec";


// TODO - continue this spec

using SpokeHarness as harness;

methods {
    function processUserAccountData(address user, bool refreshConfig) external returns (ISpoke.UserAccountData);
}

/**
 * @title Sanity check for processUserAccountData
 */
rule sanityCheck() {
    address user;
    bool refreshConfig;
    env e;
    harness.processUserAccountData(e, user, refreshConfig);
    satisfy true;
}

/**
 * @title Verify that if a user has no positions, account data should be zero
 */
rule zeroDataIfNoPositions() {
    address user;
    bool refreshConfig;
    env e;

    // Assume user has no positions
    require (forall uint256 reserveId. !isBorrowing[user][reserveId] && !isUsingAsCollateral[user][reserveId]);

    ISpoke.UserAccountData data = harness.processUserAccountData(e, user, refreshConfig);

    assert data.totalCollateralValue == 0;
    assert data.totalDebtValue == 0;
    assert data.activeCollateralCount == 0;
    assert data.borrowedCount == 0;
}

/**
 * @title Verify that totalCollateralValue is the sum of collateral values of active collateral positions
 */
rule collateralValueIntegrity() {
    address user;
    bool refreshConfig;
    env e;

    // Consider a user with potentially some collateral
    ISpoke.UserAccountData data = harness.processUserAccountData(e, user, refreshConfig);

    // If total collateral value is > 0, then at least one position must be marked as collateral and have shares
    assert data.totalCollateralValue > 0 => (exists uint256 r. isUsingAsCollateral[user][r] && harness._userPositions[user][r].suppliedShares > 0);
}
