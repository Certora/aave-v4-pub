
import "./SpokeBase.spec";
import "./symbolicRepresentation/SymbolicHub.spec";
import "./symbolicRepresentation/SymbolicPositionStatus.spec";

using SpokeInstance as spoke;
// Spoke independent spec file. No link to hub and other contracts.

// Methods block for Spoke contract
methods {
    
    
    // View Functions - Reserve Data
    function _.getSpokeOwed(uint256 assetId, address _spoke) external => HAVOC_ECF;
    function _.getSpokeAddedAssets(uint256 assetId, address _spoke) external => HAVOC_ECF;
    function _.getSpokeAddedShares(uint256 assetId, address _spoke) external => HAVOC_ECF;
    function _.getSpokeTotalOwed(uint256 assetId, address _spoke) external => HAVOC_ECF;
    
    // Spoke contract view functions
    function _.getReserveDebt(uint256 reserveId) external => HAVOC_ECF;
    function _.getReserveTotalDebt(uint256 reserveId) external => HAVOC_ECF;
    function _.getReserve(uint256 reserveId) external => HAVOC_ECF;
    function _.getDynamicReserveConfig(uint256 reserveId) external => HAVOC_ECF;

    

    function isBorrowing(uint256 reserveId, address user) external returns (bool) envfree;
    function isUsingAsCollateral(uint256 reserveId, address user) external returns (bool) envfree;

    function LiquidationLogic._calculateLiquidationAmounts(
    LiquidationLogic.CalculateLiquidationAmountsParams memory params
  ) internal returns (uint256, uint256, uint256) => NONDET ALL; 

    // here we assume this has not change anything 
    // todo - can be checked independently 
    function Spoke._notifyRiskPremiumUpdate(address user, uint256 newUserRiskPremium) internal => NONDET ALL;
}

use builtin rule sanity;

// Enhanced ghost mirror for _userPositions[user][reserveId].suppliedShares
persistent ghost mapping(address /*user*/ => mapping(uint256 /*reserveId*/ => uint256 /*suppliedShares*/)) userSuppliedSharePerReserveId {
    init_state axiom forall address user. forall uint256 reserveId. userSuppliedSharePerReserveId[user][reserveId]==0;
}

// Hook on sstore and sload to synchronize the ghost with storage changes
hook Sstore _userPositions[KEY address user][KEY uint256 reserveId].suppliedShares uint120 newValue (uint120 oldValue) {
    userSuppliedSharePerReserveId[user][reserveId] = newValue;  
    require userGhost == user;
}

hook Sload uint120 value _userPositions[KEY address user][KEY uint256 reserveId].suppliedShares {
    require userSuppliedSharePerReserveId[user][reserveId] == value;
    require userGhost == user;
}

// Enhanced ghost mirror for _userPositions[user][reserveId].drawnShares
persistent ghost mapping(address /*user*/ => mapping(uint256 /*reserveId*/ => uint256 /*drawnShares*/)) userDrawnSharePerReserveId {
    init_state axiom forall address user. forall uint256 reserveId. userDrawnSharePerReserveId[user][reserveId]==0;
}

// Hook on sstore and sload to synchronize the ghost with storage changes
hook Sstore _userPositions[KEY address user][KEY uint256 reserveId].drawnShares uint120 newValue (uint120 oldValue) {
    userDrawnSharePerReserveId[user][reserveId] = newValue;
    require userGhost == user;
}

hook Sload uint120 value _userPositions[KEY address user][KEY uint256 reserveId].drawnShares {
    require userDrawnSharePerReserveId[user][reserveId] == value;
    require userGhost == user;
}



rule checkUserHealth(method f) filtered {f -> f.selector != sig:multicall(bytes[]).selector && !increaseCollateralOrReduceDebtFunctions(f)}  {
    uint256 HEALTH_FACTOR_LIQUIDATION_THRESHOLD = 10 ^ 18;
    // Get the user address from the method call
    address user;
    env e;
    setup();
    require userGhost == user;
    
    // Check health factor before the operation
    ISpoke.UserAccountData beforeUserAccountData = getUserAccountData(e,user);
    require beforeUserAccountData.healthFactor >= HEALTH_FACTOR_LIQUIDATION_THRESHOLD;
    
    // Execute the operation 
    calldataarg args;
    f(e, args);
    
    // If the operation succeeded, check health factor after
    ISpoke.UserAccountData afterUserAccountData = getUserAccountData(e,user);
    assert afterUserAccountData.healthFactor >= HEALTH_FACTOR_LIQUIDATION_THRESHOLD;
}

definition increaseCollateralOrReduceDebtFunctions(method f) returns bool =
    f.selector != sig:withdraw(uint256, uint256, address).selector && 
    f.selector != sig:liquidationCall(uint256, uint256, address, uint256, bool).selector &&
    f.selector != sig:borrow(uint256, uint256, address).selector &&
    f.selector != sig:setUsingAsCollateral(uint256, bool, address).selector && 
    f.selector != sig:repay(uint256,uint256,address).selector &&
    f.selector != sig:updateUserDynamicConfig(address).selector;


rule increaseCollateralOrReduceDebtFunctions(method f) filtered {f -> f.selector != sig:multicall(bytes[]).selector && !f.isView && increaseCollateralOrReduceDebtFunctions(f)}  {
    uint256 reserveId; uint256 slot;
    address user;
    env e;
    setup();
    require userGhost == user;

    //user state before the operation
    bool beforePositionStatus_borrowing = isBorrowing[user][reserveId];
    bool beforePositionStatus_usingAsCollateral = isUsingAsCollateral[user][reserveId];
    uint120 beforeUserPosition_drawnShares = spoke._userPositions[user][reserveId].drawnShares;
    uint120 beforeUserPosition_realizedPremium = spoke._userPositions[user][reserveId].realizedPremium; 
    uint120 beforeUserPosition_premiumShares = spoke._userPositions[user][reserveId].premiumShares;
    uint120 beforeUserPosition_premiumOffset = spoke._userPositions[user][reserveId].premiumOffset;
    uint120 beforeUserPosition_suppliedShares = spoke._userPositions[user][reserveId].suppliedShares;
    uint24 beforeUserPosition_dynamicConfigKey = spoke._userPositions[user][reserveId].dynamicConfigKey;
    // Execute the operation 
    calldataarg args;
    f(e, args);
    
    // user state after the operation
    bool afterPositionStatus_borrowing = isBorrowing[user][reserveId];
    bool afterPositionStatus_usingAsCollateral = isUsingAsCollateral[user][reserveId];
    uint120 afterUserPosition_drawnShares = spoke._userPositions[user][reserveId].drawnShares;
    uint120 afterUserPosition_realizedPremium = spoke._userPositions[user][reserveId].realizedPremium;
    uint120 afterUserPosition_premiumShares = spoke._userPositions[user][reserveId].premiumShares;
    uint120 afterUserPosition_premiumOffset = spoke._userPositions[user][reserveId].premiumOffset;
    uint120 afterUserPosition_suppliedShares = spoke._userPositions[user][reserveId].suppliedShares;
    uint24 afterUserPosition_dynamicConfigKey = spoke._userPositions[user][reserveId].dynamicConfigKey;
    
    assert beforePositionStatus_borrowing == afterPositionStatus_borrowing && 
    beforePositionStatus_usingAsCollateral == afterPositionStatus_usingAsCollateral && 
    beforeUserPosition_drawnShares >= afterUserPosition_drawnShares && 
    beforeUserPosition_realizedPremium >= afterUserPosition_realizedPremium && 
    beforeUserPosition_premiumShares >= afterUserPosition_premiumShares && 
    beforeUserPosition_premiumOffset >= afterUserPosition_premiumOffset && 
    beforeUserPosition_suppliedShares <= afterUserPosition_suppliedShares && 
    beforeUserPosition_dynamicConfigKey == afterUserPosition_dynamicConfigKey;
}


/* todo: check if need to report the zero-out in reportDeficit 
https://prover.certora.com/output/40726/71dcf10e79fd42b39f508dc122b6fdfb/ 
*/
invariant isBorrowingIFFdrawnShares()  
forall uint256 reserveId. forall address user.
    spoke._userPositions[user][reserveId].drawnShares > 0   <=>  isBorrowing[user][reserveId]
filtered {f -> f.selector != sig:multicall(bytes[]).selector}

invariant drawnSharesZero(address user, uint256 reserveId) 
    spoke._userPositions[user][reserveId].drawnShares == 0 => (  spoke._userPositions[user][reserveId].premiumShares == 0 && spoke._userPositions[user][reserveId].premiumOffset == 0 && spoke._userPositions[user][reserveId].realizedPremium == 0) filtered {f -> f.selector != sig:multicall(bytes[]).selector}
    {
        preserved with (env e) {
            setup();
        }
    }
    

invariant validReserveId()
forall uint256 reserveId. forall address user.
    // exists
    (reserveId < spoke._reserveCount  => 
    // has underlying and hub
    (spoke._reserves[reserveId].underlying != 0 && spoke._reserves[reserveId].hub != 0 && spoke._reserveExists[spoke._reserves[reserveId].hub][spoke._reserves[reserveId].assetId] )
    &&
    // not exists
    (reserveId >= spoke._reserveCount => ( 
    // no one borrowed or used as collateral
    !isBorrowing[user][reserveId] && !isUsingAsCollateral[user][reserveId]
    // no supplied or drawn shares
    && userSuppliedSharePerReserveId[user][reserveId] == 0 && userDrawnSharePerReserveId[user][reserveId] == 0 &&
    // no premium shares or offset
    spoke._userPositions[user][reserveId].premiumShares == 0 && spoke._userPositions[user][reserveId].premiumOffset == 0 &&
    // no realized premium
    spoke._userPositions[user][reserveId].realizedPremium == 0 &&

    // has no underlying, hub, assetId
    spoke._reserves[reserveId].underlying == 0 && spoke._reserves[reserveId].assetId == 0 && spoke._reserves[reserveId].hub == 0  && spoke._reserves[reserveId].dynamicConfigKey == 0 && !spoke._reserves[reserveId].paused && !spoke._reserves[reserveId].frozen && !spoke._reserves[reserveId].borrowable && spoke._reserves[reserveId].collateralRisk == 0 )))

    filtered {f -> f.selector != sig:multicall(bytes[]).selector}



invariant validReserveId_single(uint256 reserveId)
 
    // exists
    (reserveId < spoke._reserveCount  => 
    // has underlying and hub
    (spoke._reserves[reserveId].underlying != 0 && spoke._reserves[reserveId].hub != 0 && spoke._reserveExists[spoke._reserves[reserveId].hub][spoke._reserves[reserveId].assetId] ))
    &&
    // not exists
    (reserveId >= spoke._reserveCount =>
    // has no underlying, hub, assetId
    spoke._reserves[reserveId].underlying == 0 && spoke._reserves[reserveId].assetId == 0 && spoke._reserves[reserveId].hub == 0  && spoke._reserves[reserveId].dynamicConfigKey == 0 && !spoke._reserves[reserveId].paused && !spoke._reserves[reserveId].frozen && !spoke._reserves[reserveId].borrowable && spoke._reserves[reserveId].collateralRisk == 0 && 
    
    (forall address user. 
    // no one borrowed or used as collateral
    !isBorrowing[user][reserveId] && !isUsingAsCollateral[user][reserveId]
    // no supplied or drawn shares
    && userSuppliedSharePerReserveId[user][reserveId] == 0 && userDrawnSharePerReserveId[user][reserveId] == 0 &&
    // no premium shares or offset
    spoke._userPositions[user][reserveId].premiumShares == 0 && spoke._userPositions[user][reserveId].premiumOffset == 0 &&
    // no realized premium
    spoke._userPositions[user][reserveId].realizedPremium == 0 ))

    filtered {f -> f.selector != sig:multicall(bytes[]).selector}

invariant uniqueAssetIdPerReserveId(uint256 reserveId, uint256 otherReserveId) 
    (reserveId < spoke._reserveCount && otherReserveId < spoke._reserveCount  && reserveId != otherReserveId ) => (spoke._reserves[reserveId].assetId != spoke._reserves[otherReserveId].assetId  || spoke._reserves[reserveId].hub != spoke._reserves[otherReserveId].hub)
    filtered {f -> f.selector != sig:multicall(bytes[]).selector && f.contract == spoke}
    {
        preserved {
            requireInvariant validReserveId_single(reserveId);
            requireInvariant validReserveId_single(otherReserveId);
        }

    }

        
    

invariant userCollateralCount() 
    reserveCountGhost <= spoke._reserveCount 
        filtered {f -> f.selector != sig:multicall(bytes[]).selector }
    {
    
        preserved setUsingAsCollateral(uint256 reserveId, bool usingAsCollateral, address onBehalfOf) with (env e) {
            setup();
            require userGhost == onBehalfOf;
        }
        preserved borrow(uint256 reserveId,uint256 amount,address onBehalfOf) with (env e)  {
            setup();
            require userGhost == onBehalfOf;
        }
    
    }
    
/* todo: failing when collateralFactor becomes 0 
https://prover.certora.com/output/40726/b077c5f4ef564ee2936a9532c6c246f8/
*/
rule noCollateralNoDebt_simple_cases(uint256 reserveIdUsed, address user, method f) 
    filtered {f -> f.selector != sig:multicall(bytes[]).selector && !f.isView && increaseCollateralOrReduceDebtFunctions(f)} {
    env e;
    setup();
    require userGhost == user;
    ISpoke.UserAccountData beforeUserAccountData = getUserAccountData(e,user);
    require beforeUserAccountData.totalCollateralValue == 0 => beforeUserAccountData.totalDebtValue == 0;
    
    calldataarg args;
    f(e, args);
    ISpoke.UserAccountData afterUserAccountData = getUserAccountData(e,user);
    assert afterUserAccountData.totalCollateralValue == 0 => afterUserAccountData.totalDebtValue == 0;
}

/* todo: almost done, need to work on liquidation 
https://prover.certora.com/output/40726/d4544a33a4cf4e71b823f33d79c06d2e/
*/
rule noCollateralNoDebt_complex_cases(uint256 reserveIdUsed, address user, method f) 
    filtered {f -> f.selector != sig:multicall(bytes[]).selector && !f.isView && !increaseCollateralOrReduceDebtFunctions(f)} {
    env e;
    setup();
    require userGhost == user;
    ISpoke.UserAccountData beforeUserAccountData = getUserAccountData(e,user);
    require beforeUserAccountData.totalCollateralValue == 0 => beforeUserAccountData.totalDebtValue == 0;
    
    calldataarg args;
    f(e, args);
    ISpoke.UserAccountData afterUserAccountData = getUserAccountData(e,user);
    assert afterUserAccountData.totalCollateralValue == 0 => afterUserAccountData.totalDebtValue == 0;
}

function setup() {
    requireInvariant validReserveId();
    //requireInvariant userCollateralCount();
    requireInvariant isBorrowingIFFdrawnShares();
}