import "../common.spec";
import "../symbolicRepresentation/Math_CVL.spec";


// TODO - continue this spec - not sure if needed anymore
using SpokeHarness as harness;

methods {
    function calculateDebtToTargetHealthFactor(
        LiquidationLogic.CalculateDebtToTargetHealthFactorParams params
    ) external returns (uint256) envfree;
}

/**
 * @title Sanity check for calculateDebtToTargetHealthFactor
 */
rule sanityCheck() {
    LiquidationLogic.CalculateDebtToTargetHealthFactorParams params;
    uint256 result = harness.calculateDebtToTargetHealthFactor(params);
    satisfy true;
}

/**
 * @title Verify that if health factor is already at or above target, debt to target should be 0 (or at least not positive in logical sense)
 * Note: the implementation does (target - current), so if target <= current, it might underflow or be 0.
 * In the code: params.targetHealthFactor - params.healthFactor
 */
rule zeroDebtIfHealthFactorAtTarget() {
    LiquidationLogic.CalculateDebtToTargetHealthFactorParams params;
    require params.targetHealthFactor <= params.healthFactor;
    
    // The current implementation uses uint256 for subtraction, so it will revert on underflow.
    // We expect it to revert or return 0 if target == healthFactor.
    uint256 result = harness.calculateDebtToTargetHealthFactor@withrevert(params);
    
    assert !lastReverted ||result == 0;
}

/**
 * @title Verify monotonicity: higher current health factor means lower debt needed to reach target
 */
rule monotonicityOfHealthFactor() {
    LiquidationLogic.CalculateDebtToTargetHealthFactorParams params1;
    LiquidationLogic.CalculateDebtToTargetHealthFactorParams params2;
    
    require params1.targetHealthFactor == params2.targetHealthFactor;
    require params1.totalDebtValue == params2.totalDebtValue;
    require params1.debtAssetUnit == params2.debtAssetUnit;
    require params1.debtAssetPrice == params2.debtAssetPrice;
    require params1.collateralFactor == params2.collateralFactor;
    require params1.liquidationBonus == params2.liquidationBonus;
    
    require params1.healthFactor < params2.healthFactor;
    require params2.healthFactor < params1.targetHealthFactor;

    // Fixed values for other params to ensure no overflow and valid state
    require params1.targetHealthFactor > 0;
    require params1.debtAssetPrice > 0;
    
    uint256 result1 = harness.calculateDebtToTargetHealthFactor(params1);
    uint256 result2 = harness.calculateDebtToTargetHealthFactor(params2);
    
    assert result1 >= result2;
}

/**
 * @title Verify that higher target health factor means higher debt needed to reach it
 */
rule monotonicityOfTargetHealthFactor() {
    LiquidationLogic.CalculateDebtToTargetHealthFactorParams params1;
    LiquidationLogic.CalculateDebtToTargetHealthFactorParams params2;
    
    require params1.healthFactor == params2.healthFactor;
    require params1.totalDebtValue == params2.totalDebtValue;
    require params1.debtAssetUnit == params2.debtAssetUnit;
    require params1.debtAssetPrice == params2.debtAssetPrice;
    require params1.collateralFactor == params2.collateralFactor;
    require params1.liquidationBonus == params2.liquidationBonus;
    
    require params1.targetHealthFactor < params2.targetHealthFactor;
    require params1.healthFactor < params1.targetHealthFactor;

    // Fixed values for other params to ensure no overflow and valid state
    require params1.debtAssetPrice > 0;
    
    uint256 result1 = harness.calculateDebtToTargetHealthFactor(params1);
    uint256 result2 = harness.calculateDebtToTargetHealthFactor(params2);
    
    assert result1 <= result2;
}
