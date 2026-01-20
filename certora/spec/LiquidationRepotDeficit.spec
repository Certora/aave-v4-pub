

import "./SpokeHealthFactor.spec";



methods {
    // pure functions - safe to assume NONDET
    function LiquidationLogic.calculateLiquidationBonus(uint256, uint256, uint256, uint256) internal returns (uint256) => NONDET;
    
    function LiquidationLogic._calculateDebtToTargetHealthFactor(LiquidationLogic.CalculateDebtToTargetHealthFactorParams memory) internal returns (uint256) => NONDET;
}

rule moreThanOneCollateral_noReportDeficit(uint256 reserveId, address userLiquidated, address liquidator) {
    env e;
    setup();
    require e.msg.sender == liquidator;
    uint256 debtReserveId;
    uint256 debtToCover;
    bool receiveShares;
    require currentTime == e.block.timestamp;
    require currentUser == userLiquidated;


    require !deficitReportedFlag;
    mathint collateralIDValueBefore = collateralIDValue(collateralReserveId_1); 
    require totalCollateralValueGhost == collateralIDValueBefore + collateralIDValue(collateralReserveId_2) + collateralIDValue(collateralReserveId_3);

    mathint totalCollateralValueBefore = totalCollateralValueGhost;

    liquidationCall(e, collateralReserveId_1, debtReserveId, userLiquidated, debtToCover, receiveShares);
    assert totalCollateralValueBefore > collateralIDValueBefore => !deficitReportedFlag;
}
