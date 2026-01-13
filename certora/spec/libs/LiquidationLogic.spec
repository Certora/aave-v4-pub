/**
 * @title LiquidationLogic Spec
 * @notice Specification for LiquidationLogic._calculateLiquidationAmounts
 */

import "../symbolicRepresentation/SymbolicHub.spec";
import "../common.spec";
import "../symbolicRepresentation/Math_CVL.spec";

using LiquidationLogicHarness as harness;

methods {
    function calculateLiquidationAmounts(
        LiquidationLogic.CalculateLiquidationAmountsParams params
    ) external returns (LiquidationLogic.LiquidationAmounts) envfree;

    function LiquidationLogic.calculateLiquidationBonus(uint256, uint256, uint256, uint256) internal returns (uint256) => PERCENTAGE_FACTOR;
}


/// @title Sanity check - function can succeed
rule sanityCheck() {
    env e;
    LiquidationLogic.CalculateLiquidationAmountsParams params;
    
    LiquidationLogic.LiquidationAmounts result = harness.calculateLiquidationAmounts(params);
    
    satisfy true;
}

/// @title Debt to liquidate cannot exceed debt reserve balance
rule debtToLiquidateNotExceedBalance() {
    LiquidationLogic.CalculateLiquidationAmountsParams params;
    
    LiquidationLogic.LiquidationAmounts result = harness.calculateLiquidationAmounts(params);
    
    assert result.debtToLiquidate <= params.debtReserveBalance;
}

/// @title Debt to liquidate cannot exceed debt to cover
rule debtToLiquidateNotExceedDebtToCover() {
    LiquidationLogic.CalculateLiquidationAmountsParams params;
    
    LiquidationLogic.LiquidationAmounts result = harness.calculateLiquidationAmounts(params);
    
    assert result.debtToLiquidate <= params.debtToCover;
}



/// @title Collateral to liquidator cannot exceed collateral to liquidate
rule collateralToLiquidatorNotExceedTotal() {
    LiquidationLogic.CalculateLiquidationAmountsParams params;
    
    LiquidationLogic.LiquidationAmounts result = harness.calculateLiquidationAmounts(params);
    
    assert result.collateralToLiquidator <= result.collateralToLiquidate;
    assert result.collateralToLiquidate <= params.collateralReserveBalance;
}




    //assumes liquidationBonus is none ( PERCENTAGE_FACTOR )
rule collateralToLiquidateValueLessThanDebtToLiquidate_assets(uint256 userCollateralShares, uint256 userDebtShares) {
    uint256 assetId;
    env e;
    LiquidationLogic.CalculateLiquidationAmountsParams params;
    require params.debtAssetUnit == 18;
    require params.collateralAssetUnit == 18;
    require params.debtAssetPrice > 0;
    require params.collateralAssetPrice > 0;
    
    require params.totalDebtValue >=  mulDivUpCVL(params.debtReserveBalance,WAD,params.debtAssetPrice);  

    uint256 totalCollateralValue = previewRemoveBySharesCVL(assetId,userCollateralShares, e);
    require params.collateralReserveBalance == totalCollateralValue;


    LiquidationLogic.LiquidationAmounts result = harness.calculateLiquidationAmounts(params);
    
    
    assert result.collateralToLiquidate * params.collateralAssetPrice <= result.debtToLiquidate * params.debtAssetPrice;
}

    
/*
function getDebt() {
    ...
}*/

rule collateralToLiquidateValueLessThanDebtToLiquidate_shares(uint256 userCollateralShares, uint256 userDebtShares) {
    uint256 assetId;
    env e;
    LiquidationLogic.CalculateLiquidationAmountsParams params;
    require params.debtAssetUnit == 18;
    require params.collateralAssetUnit == 18;

    require params.debtAssetPrice > 0;
    require params.collateralAssetPrice > 0;
    
    require params.totalDebtValue >=  mulDivUpCVL(params.debtReserveBalance,WAD,params.debtAssetPrice);  


    uint256 totalCollateralValue = previewRemoveBySharesCVL(assetId,userCollateralShares, e);
    require params.collateralReserveBalance == totalCollateralValue;
    uint256 totalDebtValue = previewRestoreBySharesCVL(assetId,userDebtShares, e);
    require params.debtReserveBalance == totalDebtValue;

    LiquidationLogic.LiquidationAmounts result = harness.calculateLiquidationAmounts(params);

    uint256 debtSharesToLiquidate = previewRestoreByAssetsCVL(assetId, result.debtToLiquidate, e);
    uint256 debtAssetsToLiquidate = previewDrawBySharesCVL(assetId, debtSharesToLiquidate, e);
    //uint256 debtSharesAfter = userDebtShares - debtSharesToLiquidate;
    
    uint256 sharesToLiquidate = previewRemoveByAssetsCVL(assetId, result.collateralToLiquidate, e);
    //uint256 

    uint256 actualCollateralLiquidated = previewAddBySharesCVL(assetId,sharesToLiquidate, e);
    
    assert actualCollateralLiquidated * params.collateralAssetPrice <= debtAssetsToLiquidate * params.debtAssetPrice;
}


rule collateralToLiquidateValueLessThanDebtToLiquidate_fullRayDebt(uint256 userCollateralShares, uint256 userDebtShares) {
    uint256 assetId;
    env e;
    LiquidationLogic.CalculateLiquidationAmountsParams params;
    require params.debtAssetUnit == 18;
    require params.collateralAssetUnit == 18;

    require params.debtAssetPrice > 0;
    require params.collateralAssetPrice > 0;
    
    require params.totalDebtValue >=  mulDivUpCVL(params.debtReserveBalance,WAD,params.debtAssetPrice);  


    uint256 totalCollateralValue = previewRemoveBySharesCVL(assetId,userCollateralShares, e);
    require params.collateralReserveBalance == totalCollateralValue;
    uint256 totalDebtValue = previewRestoreBySharesCVL(assetId,userDebtShares, e);
    require params.debtReserveBalance == totalDebtValue;

    LiquidationLogic.LiquidationAmounts result = harness.calculateLiquidationAmounts(params);

    uint256 debtSharesToLiquidate = previewRestoreByAssetsCVL(assetId, result.debtToLiquidate, e);
    mathint debtAssetsToLiquidate = debtSharesToLiquidate * indexOfAssetPerBlock[assetId][e.block.timestamp];
    //uint256 debtSharesAfter = userDebtShares - debtSharesToLiquidate;
    
    uint256 sharesToLiquidate = previewRemoveByAssetsCVL(assetId, result.collateralToLiquidate, e);
    //uint256 

    uint256 actualCollateralLiquidated = previewAddBySharesCVL(assetId,sharesToLiquidate, e);
    
    assert actualCollateralLiquidated * params.collateralAssetPrice <= debtAssetsToLiquidate * params.debtAssetPrice / RAY;
}