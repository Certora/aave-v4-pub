/**
 * @title LiquidationLogic Library Specification
 * @notice Formal verification of LiquidationLogic._calculateLiquidationAmounts.
 * @dev This spec verifies the core liquidation calculation logic by comparing it against symbolic representations.
 * 
 * Verification Scope:
 * - Liquidation amount bounds: Ensuring debt and collateral to liquidate are within reasonable limits.
 * - Value preservation: Verifying that the value of collateral seized does not exceed the value of debt covered (given no bonus).
 * - Functional correctness: Ensuring the logic correctly handles various user position scenarios.
 */

import "../symbolicRepresentation/SymbolicHub.spec";
import "../common.spec";
import "../symbolicRepresentation/Math_CVL.spec";

using LiquidationLogicHarness as harness;

////////////////////////////////////////////////////////////////////////////
//                                METHODS                                 //
////////////////////////////////////////////////////////////////////////////

methods {
    function calculateLiquidationAmounts(
        LiquidationLogic.CalculateLiquidationAmountsParams params
    ) external returns (LiquidationLogic.LiquidationAmounts) envfree;

    function LiquidationLogic.calculateLiquidationBonus(uint256, uint256, uint256, uint256) internal returns (uint256) => PERCENTAGE_FACTOR;
}

////////////////////////////////////////////////////////////////////////////
//                                 RULES                                  //
////////////////////////////////////////////////////////////////////////////

/**
 * @title Sanity Check
 * @notice Verifies that the calculateLiquidationAmounts function can succeed for at least one set of parameters.
 */
rule sanityCheck() {
    LiquidationLogic.CalculateLiquidationAmountsParams params;
    harness.calculateLiquidationAmounts(params);
    satisfy true;
}

/**
 * @title Debt to Liquidate Bounds
 * @notice Ensures that the debt to liquidate does not exceed the available debt reserve balance or the requested debt to cover.
 */
rule debtToLiquidateBounds() {
    LiquidationLogic.CalculateLiquidationAmountsParams params;
    LiquidationLogic.LiquidationAmounts result = harness.calculateLiquidationAmounts(params);
    
    assert result.debtToLiquidate <= params.debtReserveBalance, "Debt to liquidate exceeds reserve balance";
    assert result.debtToLiquidate <= params.debtToCover, "Debt to liquidate exceeds debt to cover";
}

/**
 * @title Collateral to Liquidate Bounds
 * @notice Ensures that the collateral seized by the liquidator does not exceed the total collateral to liquidate or the reserve balance.
 */
rule collateralToLiquidateBounds() {
    LiquidationLogic.CalculateLiquidationAmountsParams params;
    LiquidationLogic.LiquidationAmounts result = harness.calculateLiquidationAmounts(params);
    
    assert result.collateralToLiquidator <= result.collateralToLiquidate, "Liquidator collateral exceeds total liquidated";
    assert result.collateralToLiquidate <= params.collateralReserveBalance, "Collateral to liquidate exceeds reserve balance";
}

/**
 * @title Collateral Value vs Debt Value (Assets)
 * @notice Verifies that the value of seized collateral is less than or equal to the value of debt covered (assuming no bonus).
 */
rule collateralToLiquidateValueLessThanDebtToLiquidate_assets(uint256 userCollateralShares, uint256 userDebtShares) {
    uint256 assetId;
    env e;
    LiquidationLogic.CalculateLiquidationAmountsParams params;
    
    require params.debtAssetUnit == 18;
    require params.collateralAssetUnit == 18;
    require params.debtAssetPrice > 0;
    require params.collateralAssetPrice > 0;
    
    require params.totalDebtValue >= mulDivUpCVL(params.debtReserveBalance, WAD, params.debtAssetPrice);  

    uint256 totalCollateralValue = previewRemoveBySharesCVL(assetId, userCollateralShares, e);
    require params.collateralReserveBalance == totalCollateralValue;

    LiquidationLogic.LiquidationAmounts result = harness.calculateLiquidationAmounts(params);
    
    assert result.collateralToLiquidate * params.collateralAssetPrice <= result.debtToLiquidate * params.debtAssetPrice, "Collateral value exceeds debt value";
}

/**
 * @title Collateral Value vs Debt Value (Shares)
 * @notice Verifies value preservation using share-to-asset conversions.
 */
rule collateralToLiquidateValueLessThanDebtToLiquidate_shares(uint256 userCollateralShares, uint256 userDebtShares) {
    uint256 assetId;
    env e;
    LiquidationLogic.CalculateLiquidationAmountsParams params;
    
    require params.debtAssetUnit == 18;
    require params.collateralAssetUnit == 18;
    require params.debtAssetPrice > 0;
    require params.collateralAssetPrice > 0;
    
    require params.totalDebtValue >= mulDivUpCVL(params.debtReserveBalance, WAD, params.debtAssetPrice);  

    uint256 totalCollateralValue = previewRemoveBySharesCVL(assetId, userCollateralShares, e);
    require params.collateralReserveBalance == totalCollateralValue;
    uint256 totalDebtValue = previewRestoreBySharesCVL(assetId, userDebtShares, e);
    require params.debtReserveBalance == totalDebtValue;

    LiquidationLogic.LiquidationAmounts result = harness.calculateLiquidationAmounts(params);

    uint256 debtSharesToLiquidate = previewRestoreByAssetsCVL(assetId, result.debtToLiquidate, e);
    uint256 debtAssetsToLiquidate = previewDrawBySharesCVL(assetId, debtSharesToLiquidate, e);
    
    uint256 sharesToLiquidate = previewRemoveByAssetsCVL(assetId, result.collateralToLiquidate, e);
    uint256 actualCollateralLiquidated = previewAddBySharesCVL(assetId, sharesToLiquidate, e);
    
    assert actualCollateralLiquidated * params.collateralAssetPrice <= debtAssetsToLiquidate * params.debtAssetPrice, "Collateral share value exceeds debt share value";
}

/**
 * @title Collateral Value vs Debt Value (Full Ray Debt)
 * @notice Verifies value preservation using full ray precision for debt calculations.
 */
rule collateralToLiquidateValueLessThanDebtToLiquidate_fullRayDebt(uint256 userCollateralShares, uint256 userDebtShares) {
    uint256 assetId;
    env e;
    LiquidationLogic.CalculateLiquidationAmountsParams params;
    
    require params.debtAssetUnit == 18;
    require params.collateralAssetUnit == 18;
    require params.debtAssetPrice > 0;
    require params.collateralAssetPrice > 0;
    
    require params.totalDebtValue >= mulDivUpCVL(params.debtReserveBalance, WAD, params.debtAssetPrice);  

    uint256 totalCollateralValue = previewRemoveBySharesCVL(assetId, userCollateralShares, e);
    require params.collateralReserveBalance == totalCollateralValue;
    uint256 totalDebtValue = previewRestoreBySharesCVL(assetId, userDebtShares, e);
    require params.debtReserveBalance == totalDebtValue;

    LiquidationLogic.LiquidationAmounts result = harness.calculateLiquidationAmounts(params);

    uint256 debtSharesToLiquidate = previewRestoreByAssetsCVL(assetId, result.debtToLiquidate, e);
    mathint debtAssetsToLiquidate = debtSharesToLiquidate * indexOfAssetPerBlock[assetId][e.block.timestamp];
    
    uint256 sharesToLiquidate = previewRemoveByAssetsCVL(assetId, result.collateralToLiquidate, e);
    uint256 actualCollateralLiquidated = previewAddBySharesCVL(assetId, sharesToLiquidate, e);
    
    assert actualCollateralLiquidated * params.collateralAssetPrice <= debtAssetsToLiquidate * params.debtAssetPrice / RAY, "Collateral value exceeds ray-precision debt value";
}
