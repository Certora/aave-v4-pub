
import "./SpokeBase.spec";
import "./SymbolicHub.spec";
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
hook Sstore _userPositions[KEY address user][KEY uint256 reserveId].suppliedShares uint128 newValue (uint128 oldValue) {
    userSuppliedSharePerReserveId[user][reserveId] = newValue;  
    require userGhost == user;
}

hook Sload uint128 value _userPositions[KEY address user][KEY uint256 reserveId].suppliedShares {
    require userSuppliedSharePerReserveId[user][reserveId] == value;
    require userGhost == user;
}

// Enhanced ghost mirror for _userPositions[user][reserveId].drawnShares
persistent ghost mapping(address /*user*/ => mapping(uint256 /*reserveId*/ => uint256 /*drawnShares*/)) userDrawnSharePerReserveId {
    init_state axiom forall address user. forall uint256 reserveId. userDrawnSharePerReserveId[user][reserveId]==0;
}

// Hook on sstore and sload to synchronize the ghost with storage changes
hook Sstore _userPositions[KEY address user][KEY uint256 reserveId].drawnShares uint128 newValue (uint128 oldValue) {
    userDrawnSharePerReserveId[user][reserveId] = newValue;
    require userGhost == user;
}

hook Sload uint128 value _userPositions[KEY address user][KEY uint256 reserveId].drawnShares {
    require userDrawnSharePerReserveId[user][reserveId] == value;
    require userGhost == user;
}



rule checkUserHealth(method f) filtered {f -> f.selector != sig:multicall(bytes[]).selector}  {
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
    f.selector != sig:liquidationCall(uint256, uint256, address, uint256).selector &&
    f.selector != sig:borrow(uint256, uint256, address).selector &&
    f.selector != sig:setUsingAsCollateral(uint256, bool, address).selector;

rule increaseCollateralOrReduceDebtFunctions(method f) filtered {f -> f.selector != sig:multicall(bytes[]).selector && !f.isView && increaseCollateralOrReduceDebtFunctions(f)}  {
    uint256 reserveId;
    address user;
    env e;
    setup();
    require userGhost == user;

    //user state before the operation
    ISpoke.PositionStatus beforePositionStatus =spoke._positionStatus[user];
    ISpoke.UserPosition beforeUserPosition = spoke._userPositions[user][reserveId];
    
    // Execute the operation 
    calldataarg args;
    f(e, args);
    
    // user state after the operation
    ISpoke.PositionStatus afterPositionStatus =spoke._positionStatus[user];
    ISpoke.UserPosition afterUserPosition = spoke._userPositions[user][reserveId];
    assert beforePositionStatus == afterPositionStatus && beforeUserPosition == afterUserPosition;
}



function setup() {
    requireInvariant validReserveId();
    //requireInvariant userCollateralCount();
    requireInvariant isBorrowingIFFdrawnShares();
}