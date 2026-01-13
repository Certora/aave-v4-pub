import "./SpokeUserIntegrity.spec";


methods {

    // non deterministic behaviour for pure functions that don't read or modify state - they only perform calculations on the input parameters.
    function LiquidationLogic.calculateLiquidationBonus(uint256, uint256, uint256, uint256) internal returns (uint256) => NONDET;
    function LiquidationLogic._validateLiquidationCall(LiquidationLogic.ValidateLiquidationCallParams memory) internal => NONDET;
    function LiquidationLogic._calculateDebtToLiquidate(LiquidationLogic.CalculateDebtToLiquidateParams memory) internal returns (uint256) => NONDET;
    function LiquidationLogic._calculateDebtToTargetHealthFactor(LiquidationLogic.CalculateDebtToTargetHealthFactorParams memory) internal returns (uint256) => NONDET;
    function LiquidationLogic._evaluateDeficit(bool, bool, uint256, uint256) internal returns (bool) => NONDET;
}


rule onlyOneUserDebtChanges_liquidationCall(uint256 reserveId, address user1, address user2) {
    env e;

    uint256 collateralReserveId;
    uint256 debtReserveId;
    address userLiquidated;
    uint256 debtToCover;
    bool receiveShares;

    uint256 beforeDrawnShares1 = spoke._userPositions[user1][reserveId].drawnShares;
    uint256 beforeDrawnShares2 = spoke._userPositions[user2][reserveId].drawnShares;

    liquidationCall(e, collateralReserveId, debtReserveId, userLiquidated, debtToCover, receiveShares);   
    assert beforeDrawnShares1 != spoke._userPositions[user1][reserveId].drawnShares && 
    beforeDrawnShares2 != spoke._userPositions[user2][reserveId].drawnShares => (user1 == user2 && user1 == userLiquidated);
}


