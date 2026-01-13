

import "./SpokeBase.spec";
import "./symbolicRepresentation/SymbolicPositionStatus.spec";
import "./symbolicRepresentation/SymbolicHub.spec";

persistent ghost uint256 HEALTH_FACTOR_LIQUIDATION_THRESHOLD {
    axiom HEALTH_FACTOR_LIQUIDATION_THRESHOLD == 10^18;
}

methods {
    // based on spec LiquidationLogic_Bonus.spec
    function LiquidationLogic.calculateLiquidationBonus(uint256, uint256, uint256, uint256) internal returns (uint256) => CalculateLiquidationBonusGhost;

    function Spoke._processUserAccountData(address user, bool refreshConfig) internal returns (ISpoke.UserAccountData memory) => processUserAccountDataCVL(user, refreshConfig);

    // pure function - safe to assume NONDET
    function LiquidationLogic._calculateDebtToTargetHealthFactor(LiquidationLogic.CalculateDebtToTargetHealthFactorParams memory) internal returns (uint256) => NONDET;
}

// based on bonusIsAtLeastNoBonus 
ghost uint256 CalculateLiquidationBonusGhost {
    axiom CalculateLiquidationBonusGhost >= PERCENTAGE_FACTOR;
}

persistent ghost mapping(address => uint256) ghostHealthFactor {
    init_state axiom forall address user. ghostHealthFactor[user] == 0;
}

function processUserAccountDataCVL(address user, bool refreshConfig) returns (ISpoke.UserAccountData) {
    ISpoke.UserAccountData userAccountData;
    require userAccountData.healthFactor == ghostHealthFactor[user];
    require userAccountData.activeCollateralCount <= reserveCountGhost;
    return userAccountData;
}


rule sanityCheck() {
    env e;
    setup();
    calldataarg args;
    liquidationCall(e, args);
    satisfy true;
}

// assuming one user's borrowing flag is set at a time - proven in LiquidationUserIntegrity.spec
rule borrowingFlagSetIFFdrawnShares_liquidationCall(uint256 reserveId, address user) {
    env e;
    setup();
    require userGhost == user;
    uint256 collateralReserveId;
    uint256 debtReserveId;
    uint256 debtToCover;
    bool receiveShares;

    require spoke._userPositions[user][reserveId].drawnShares > 0 <=> isBorrowing[user][reserveId];
    liquidationCall(e, collateralReserveId, debtReserveId, user, debtToCover, receiveShares);
    assert spoke._userPositions[user][reserveId].drawnShares > 0 <=> isBorrowing[user][reserveId];
}

//* an account that is health can not be liquidated 
rule healthyAccountCannotBeLiquidated(uint256 reserveId, address user) {
    env e;
    setup();
    require userGhost == user;
    uint256 collateralReserveId;
    uint256 debtReserveId;
    uint256 debtToCover;
    bool receiveShares;
    require ghostHealthFactor[user] >= HEALTH_FACTOR_LIQUIDATION_THRESHOLD;
    liquidationCall@withrevert(e, collateralReserveId, debtReserveId, user, debtToCover, receiveShares);
    assert lastReverted;
}   

//* @title When paused (collateral of debt) then no liquidation
rule paused_noLiquidation(uint256 reserveId, address userLiquidated, address liquidator) {
    env e;
    setup();
    require e.msg.sender == liquidator;
    uint256 collateralReserveId;
    uint256 debtReserveId;
    uint256 debtToCover;
    bool receiveShares;
    require liquidator != spoke._reserves[collateralReserveId].hub;
    require pausedGhost;
    liquidationCall@withrevert(e, collateralReserveId, debtReserveId, userLiquidated, debtToCover, receiveShares);
    assert lastReverted;
}

rule monotonicityOfDebtDecrease_liquidationCall(uint256 reserveId, address userLiquidated, address liquidator) {
    env e;
    setup();
    require e.msg.sender == liquidator;
    uint256 collateralReserveId;
    uint256 debtReserveId;
    uint256 debtToCover;
    bool receiveShares;
    require liquidator != spoke._reserves[collateralReserveId].hub;

    require spoke._userPositions[userLiquidated][debtReserveId].drawnShares > 0 <=> isBorrowing[userLiquidated][debtReserveId];
    
    
    address underlyingCollateral = spoke._reserves[collateralReserveId].underlying;
    require underlyingCollateral == assetUnderlying[spoke._reserves[collateralReserveId].assetId];

    uint256 beforeDrawnShares = spoke._userPositions[userLiquidated][debtReserveId].drawnShares;
    uint256 beforeUnderlyingCollateralBalance = tokenBalanceOf(underlyingCollateral, liquidator);
    uint256 beforeCollateral = spoke._userPositions[liquidator][collateralReserveId].suppliedShares;

    mathint beforePremiumDebt = (spoke._userPositions[userLiquidated][debtReserveId].premiumShares * getAssetDrawnIndexCVL(spoke._reserves[debtReserveId].assetId, e))- spoke._userPositions[userLiquidated][debtReserveId].premiumOffsetRay;

    liquidationCall(e, collateralReserveId, debtReserveId, userLiquidated, debtToCover, receiveShares);
    
    uint256 afterDrawnShares = spoke._userPositions[userLiquidated][debtReserveId].drawnShares;
    uint256 afterUnderlyingCollateralBalance = tokenBalanceOf(underlyingCollateral, liquidator);
    uint256 afterCollateral = spoke._userPositions[liquidator][collateralReserveId].suppliedShares;

    mathint afterPremiumDebt = (spoke._userPositions[userLiquidated][debtReserveId].premiumShares * getAssetDrawnIndexCVL(spoke._reserves[debtReserveId].assetId, e))- spoke._userPositions[userLiquidated][debtReserveId].premiumOffsetRay;
    
    assert 
    (beforeCollateral < afterCollateral || beforeUnderlyingCollateralBalance < afterUnderlyingCollateralBalance) =>
    (afterDrawnShares < beforeDrawnShares   || afterPremiumDebt < beforePremiumDebt);

}   

rule moreThanOneCollateral_noReportDeficit(uint256 reserveId, address userLiquidated, address liquidator) {
    env e;
    setup();
    require e.msg.sender == liquidator;
    uint256 collateralReserveId;
    uint256 debtReserveId;
    uint256 debtToCover;
    bool receiveShares;
    uint256 otherCollateralReserveId;
    require otherCollateralReserveId != collateralReserveId;

    require liquidator != spoke._reserves[collateralReserveId].hub;
    require spoke._userPositions[userLiquidated][collateralReserveId].suppliedShares > 0;
    require spoke._userPositions[userLiquidated][otherCollateralReserveId].suppliedShares > 0;
    require reserveCountGhost > 1; // total collateral in position status 

    //todo - try to run with original processUserAccountDataCVL function
    require isUsingAsCollateral[userLiquidated][otherCollateralReserveId] && isUsingAsCollateral[userLiquidated][collateralReserveId];
    uint256 collateralFactorCollateralReserveId = spoke._dynamicConfig[collateralReserveId][spoke._userPositions[userLiquidated][collateralReserveId].dynamicConfigKey].collateralFactor;
    require collateralFactorCollateralReserveId > 0;
    uint256 collateralFactorOtherCollateralReserveId = spoke._dynamicConfig[otherCollateralReserveId][spoke._userPositions[userLiquidated][otherCollateralReserveId].dynamicConfigKey].collateralFactor;
    require collateralFactorOtherCollateralReserveId > 0;
    
    require spoke._userPositions[userLiquidated][debtReserveId].drawnShares > 0 <=> isBorrowing[userLiquidated][debtReserveId];

    require !deficitReportedFlag;
    liquidationCall(e, collateralReserveId, debtReserveId, userLiquidated, debtToCover, receiveShares);
    assert !deficitReportedFlag;
}


//@title During liquidation no change to other accounts. In the liquidated account debt can be decrease to zero on report deficit, however other collateral can not change at all
rule noChangeToOtherAccounts_liquidationCall(uint256 reserveId, address userLiquidated, address liquidator, address user) {
    env e;
    setup();
    require e.msg.sender == liquidator;
    uint256 collateralReserveId;
    uint256 debtReserveId;
    uint256 debtToCover;
    bool receiveShares;

    uint256 drawnSharesBefore = spoke._userPositions[user][reserveId].drawnShares;
    uint256 premiumSharesBefore = spoke._userPositions[user][reserveId].premiumShares;
    int256 premiumOffsetRayBefore = spoke._userPositions[user][reserveId].premiumOffsetRay;
    uint256 suppliedSharesBefore = spoke._userPositions[user][reserveId].suppliedShares;

    liquidationCall(e, collateralReserveId, debtReserveId, userLiquidated, debtToCover, receiveShares);

    assert spoke._userPositions[user][reserveId].drawnShares != drawnSharesBefore => (user == userLiquidated);
    assert spoke._userPositions[user][reserveId].premiumShares != premiumSharesBefore =>
            (user == userLiquidated );
    assert spoke._userPositions[user][reserveId].premiumOffsetRay != premiumOffsetRayBefore =>
            (user == userLiquidated );
    assert spoke._userPositions[user][reserveId].suppliedShares != suppliedSharesBefore =>
            (reserveId == collateralReserveId &&
             ( (user == userLiquidated && spoke._userPositions[user][reserveId].suppliedShares < suppliedSharesBefore) ||
             (user == liquidator && spoke._userPositions[user][reserveId].suppliedShares > suppliedSharesBefore && receiveShares && !frozenGhost) ));
}
