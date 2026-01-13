import "./SpokeBaseSummaries.spec";

using SpokeInstance as spoke;

/***

Base definitions used in all of Spoke spec files

***/
methods {
    function isPositionManager(address user, address positionManager) external returns (bool) envfree;

    // todo - check with mod and dev operation instead of summary 
    function _.paused(ISpoke.ReserveFlags) internal => pausedGhost expect bool;
    function _.frozen(ISpoke.ReserveFlags) internal => frozenGhost expect bool;
}

persistent ghost bool pausedGhost;
persistent ghost bool frozenGhost;



definition increaseCollateralOrReduceDebtFunctions(method f) returns bool =
    f.selector != sig:withdraw(uint256, uint256, address).selector && 
    f.selector != sig:liquidationCall(uint256, uint256, address, uint256, bool).selector &&
    f.selector != sig:borrow(uint256, uint256, address).selector &&
    f.selector != sig:setUsingAsCollateral(uint256, bool, address).selector && 
    f.selector != sig:updateUserDynamicConfig(address).selector;


function setup() {
    require spoke._reserveCount < max_uint256; // safe assumption 
    //requireInvariant validReserveId();
    require forall uint256 reserveId. forall address user.
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
    && spoke._userPositions[user][reserveId].suppliedShares == 0 && spoke._userPositions[user][reserveId].drawnShares == 0 &&
    // no premium shares or offset
    spoke._userPositions[user][reserveId].premiumShares == 0 && spoke._userPositions[user][reserveId].premiumOffsetRay == 0 &&

    // has no underlying, hub, assetId
    spoke._reserves[reserveId].underlying == 0 && spoke._reserves[reserveId].assetId == 0 && spoke._reserves[reserveId].hub == 0  && spoke._reserves[reserveId].dynamicConfigKey == 0 && spoke._reserves[reserveId].flags == 0 && spoke._reserves[reserveId].collateralRisk == 0 )));
    
    //requireInvariant isBorrowingIFFdrawnShares();
    require forall uint256 reserveId. forall address user.
    spoke._userPositions[user][reserveId].drawnShares > 0   <=>  isBorrowing[user][reserveId];

}