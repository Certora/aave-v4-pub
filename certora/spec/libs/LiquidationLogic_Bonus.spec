/**
 * @title LiquidationLogic Bonus Specification
 * @notice Formal verification of LiquidationLogic.calculateLiquidationBonus.
 * @dev This spec verifies how the liquidation bonus is calculated based on the user's health factor.
 * 
 * The function logic:
 * - If healthFactor <= healthFactorForMaxBonus: returns maxLiquidationBonus.
 * - Otherwise: linear interpolation between minLiquidationBonus and maxLiquidationBonus.
 * 
 * Verification Scope:
 * - Functional correctness: Bonus matches expected values at boundaries (max bonus and threshold).
 * - Monotonicity: Higher health factor should result in a lower or equal bonus.
 * - Bounds: Bonus should never exceed the maximum or fall below the base (100%).
 */

using LiquidationLogicHarness as harness;

////////////////////////////////////////////////////////////////////////////
//                                METHODS                                 //
////////////////////////////////////////////////////////////////////////////

methods {
    function calculateLiquidationBonus(
        uint256 healthFactorForMaxBonus,
        uint256 liquidationBonusFactor,
        uint256 healthFactor,
        uint256 maxLiquidationBonus
    ) external returns (uint256) envfree;
}

////////////////////////////////////////////////////////////////////////////
//                               DEFINITIONS                               //
////////////////////////////////////////////////////////////////////////////

definition PERCENTAGE_FACTOR() returns uint256 = 10000; // 100% in BPS
definition HEALTH_FACTOR_LIQUIDATION_THRESHOLD() returns uint256 = 10^18;

////////////////////////////////////////////////////////////////////////////
//                                 RULES                                  //
////////////////////////////////////////////////////////////////////////////

/**
 * @title Sanity Check
 * @notice Verifies that calculateLiquidationBonus can succeed for at least one set of parameters.
 */
rule sanityCheck() {
    uint256 healthFactorForMaxBonus;
    uint256 liquidationBonusFactor;
    uint256 healthFactor;
    uint256 maxLiquidationBonus;
    
    harness.calculateLiquidationBonus(
        healthFactorForMaxBonus,
        liquidationBonusFactor,
        healthFactor,
        maxLiquidationBonus
    );
    
    satisfy true;
}

/**
 * @title Max Bonus at Low Health Factor
 * @notice Verifies that when the health factor is below or equal to the max bonus threshold, the maximum bonus is returned.
 */
rule maxBonusWhenLowHealthFactor() {
    uint256 healthFactorForMaxBonus;
    uint256 liquidationBonusFactor;
    uint256 healthFactor;
    uint256 maxLiquidationBonus;
    
    require healthFactor <= healthFactorForMaxBonus;
    
    uint256 result = harness.calculateLiquidationBonus(
        healthFactorForMaxBonus,
        liquidationBonusFactor,
        healthFactor,
        maxLiquidationBonus
    );
    
    assert result == maxLiquidationBonus, "Should return max bonus for low health factor";
}

/**
 * @title Minimum Bonus Bound
 * @notice Ensures that the calculated bonus is never less than 100% (PERCENTAGE_FACTOR).
 */
rule bonusIsAtLeastNoBonus() {
    uint256 healthFactorForMaxBonus;
    uint256 liquidationBonusFactor;
    uint256 healthFactor;
    uint256 maxLiquidationBonus;
    
    // Preconditions for valid inputs
    require maxLiquidationBonus >= PERCENTAGE_FACTOR();
    require healthFactorForMaxBonus < HEALTH_FACTOR_LIQUIDATION_THRESHOLD();
    require healthFactor <= HEALTH_FACTOR_LIQUIDATION_THRESHOLD();
    
    uint256 result = harness.calculateLiquidationBonus(
        healthFactorForMaxBonus,
        liquidationBonusFactor,
        healthFactor,
        maxLiquidationBonus
    );
    
    assert result >= PERCENTAGE_FACTOR(), "Bonus cannot be negative (less than 100%)";
}

/**
 * @title Maximum Bonus Bound
 * @notice Ensures that the calculated bonus never exceeds the specified maximum liquidation bonus.
 */
rule bonusDoesNotExceedMax() {
    uint256 healthFactorForMaxBonus;
    uint256 liquidationBonusFactor;
    uint256 healthFactor;
    uint256 maxLiquidationBonus;
    
    uint256 result = harness.calculateLiquidationBonus(
        healthFactorForMaxBonus,
        liquidationBonusFactor,
        healthFactor,
        maxLiquidationBonus
    );
    
    assert result <= maxLiquidationBonus, "Bonus exceeds specified maximum";
}

/**
 * @title Bonus Monotonicity
 * @notice Verifies that as the health factor increases, the liquidation bonus decreases or stays the same.
 */
rule monotonicityOfBonus() {
    uint256 healthFactorForMaxBonus;
    uint256 liquidationBonusFactor;
    uint256 healthFactor1;
    uint256 healthFactor2;
    uint256 maxLiquidationBonus;
    
    require healthFactor1 < healthFactor2;
    require healthFactor2 <= HEALTH_FACTOR_LIQUIDATION_THRESHOLD();
    require healthFactorForMaxBonus < HEALTH_FACTOR_LIQUIDATION_THRESHOLD();
    
    uint256 result1 = harness.calculateLiquidationBonus(
        healthFactorForMaxBonus,
        liquidationBonusFactor,
        healthFactor1,
        maxLiquidationBonus
    );
    
    uint256 result2 = harness.calculateLiquidationBonus(
        healthFactorForMaxBonus,
        liquidationBonusFactor,
        healthFactor2,
        maxLiquidationBonus
    );
    
    assert result1 >= result2, "Bonus should not increase with higher health factor";
}

/**
 * @title Bonus at Liquidation Threshold
 * @notice Verifies that at the liquidation threshold (1.0), the bonus equals the minimum calculated bonus.
 */
rule bonusAtThreshold() {
    uint256 healthFactorForMaxBonus;
    uint256 liquidationBonusFactor;
    uint256 maxLiquidationBonus;
    
    require healthFactorForMaxBonus < HEALTH_FACTOR_LIQUIDATION_THRESHOLD();
    require maxLiquidationBonus >= PERCENTAGE_FACTOR();
    
    uint256 result = harness.calculateLiquidationBonus(
        healthFactorForMaxBonus,
        liquidationBonusFactor,
        HEALTH_FACTOR_LIQUIDATION_THRESHOLD(),
        maxLiquidationBonus
    );
    
    // At threshold, should return minLiquidationBonus which is computed as:
    // (maxLiquidationBonus - PERCENTAGE_FACTOR).percentMulDown(liquidationBonusFactor) + PERCENTAGE_FACTOR
    mathint expectedMin = ((maxLiquidationBonus - PERCENTAGE_FACTOR()) * liquidationBonusFactor / PERCENTAGE_FACTOR()) + PERCENTAGE_FACTOR();
    
    assert result == assert_uint256(expectedMin), "Bonus at threshold mismatch";
}

/**
 * @title Zero Bonus Factor Impact
 * @notice Verifies that if the bonus factor is zero, the minimum bonus at the threshold is exactly 100% (no bonus).
 */
rule zeroBonusFactorMeansNoMinBonus() {
    uint256 healthFactorForMaxBonus;
    uint256 healthFactor;
    uint256 maxLiquidationBonus;
    
    require healthFactor > healthFactorForMaxBonus;
    require healthFactor == HEALTH_FACTOR_LIQUIDATION_THRESHOLD();
    require maxLiquidationBonus >= PERCENTAGE_FACTOR();
    
    uint256 result = harness.calculateLiquidationBonus(
        healthFactorForMaxBonus,
        0, // zero bonus factor
        healthFactor,
        maxLiquidationBonus
    );
    
    assert result == PERCENTAGE_FACTOR(), "Zero bonus factor should result in 100% bonus at threshold";
}
