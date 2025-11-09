
import "./SpokeBase.spec";
import "./symbolicRepresentation/SymbolicPositionStatus.spec";
import "./symbolicRepresentation/ERC20s_CVL.spec";

using SpokeInstance as spoke;
using Hub as hub;


// Methods block for Spoke contract
methods {
    

    function LiquidationLogic._calculateLiquidationAmounts(
    LiquidationLogic.CalculateLiquidationAmountsParams memory params
  ) internal returns (uint256, uint256, uint256) => NONDET ALL; 


    function _.setInterestRateData(uint256 assetId, bytes data) external => NONDET; 

    function _._checkCanCall(address caller, bytes calldata data) internal => NONDET; 

    function AssetLogic.getDrawnIndex(IHub.Asset storage   asset) internal returns (uint256) => cachedIndex;
}

// assume a given single drawnIndex
ghost uint256 cachedIndex;



ghost mapping(uint256 /*reserveId*/ => mathint /*source*/) sumUserSuppliedSharesPerReserveId {
    init_state axiom forall uint256 reserveId. sumUserSuppliedSharesPerReserveId[reserveId] == 0;
}

// Hook on sstore and sload to synchronize the ghost with storage changes
hook Sstore _userPositions[KEY address user][KEY uint256 reserveId].suppliedShares uint120 newValue (uint120 oldValue) {
    sumUserSuppliedSharesPerReserveId[reserveId] = sumUserSuppliedSharesPerReserveId[reserveId] + newValue - oldValue;
}

hook Sload uint120 value _userPositions[KEY address user][KEY uint256 reserveId].suppliedShares {
    require sumUserSuppliedSharesPerReserveId[reserveId] >= value;
}


ghost mapping(uint256 /*reserveId*/ => mathint /*source*/) sumUserDrawnSharesPerReserveId {
    init_state axiom forall uint256 reserveId. sumUserDrawnSharesPerReserveId[reserveId] == 0;
}

// Hook on sstore and sload to synchronize the ghost with storage changes
hook Sstore _userPositions[KEY address user][KEY uint256 reserveId].drawnShares uint120 newValue (uint120 oldValue) {
    sumUserDrawnSharesPerReserveId[reserveId] = sumUserDrawnSharesPerReserveId[reserveId] + newValue - oldValue;
}

hook Sload uint120 value _userPositions[KEY address user][KEY uint256 reserveId].drawnShares {

    require sumUserDrawnSharesPerReserveId[reserveId] >= value;
}

ghost mapping(uint256 /*reserveId*/ => mathint /*source*/) sumUserPremiumSharesPerReserveId {
    init_state axiom forall uint256 reserveId. sumUserPremiumSharesPerReserveId[reserveId] == 0;
}

// Hook on sstore and sload to synchronize the ghost with storage changes
hook Sstore _userPositions[KEY address user][KEY uint256 reserveId].premiumShares uint120 newValue (uint120 oldValue) {
    sumUserPremiumSharesPerReserveId[reserveId] = sumUserPremiumSharesPerReserveId[reserveId] + newValue - oldValue;
}

hook Sload uint120 value _userPositions[KEY address user][KEY uint256 reserveId].premiumShares {
    require sumUserPremiumSharesPerReserveId[reserveId] >= value;
}

ghost mapping(uint256 /*reserveId*/ => mathint /*source*/) sumUserPremiumOffsetPerReserveId {
    init_state axiom forall uint256 reserveId. sumUserPremiumOffsetPerReserveId[reserveId] == 0;
}

// Hook on sstore and sload to synchronize the ghost with storage changes
hook Sstore _userPositions[KEY address user][KEY uint256 reserveId].premiumOffset uint120 newValue (uint120 oldValue) {
    sumUserPremiumOffsetPerReserveId[reserveId] = sumUserPremiumOffsetPerReserveId[reserveId] + newValue - oldValue;
}

hook Sload uint120 value _userPositions[KEY address user][KEY uint256 reserveId].premiumOffset {
    require sumUserPremiumOffsetPerReserveId[reserveId] >= value;
}

ghost mapping(uint256 /*reserveId*/ => mathint /*source*/) sumUserRealizedPremiumPerReserveId {
    init_state axiom forall uint256 reserveId. sumUserRealizedPremiumPerReserveId[reserveId] == 0;
}

// Hook on sstore and sload to synchronize the ghost with storage changes
hook Sstore _userPositions[KEY address user][KEY uint256 reserveId].realizedPremium uint120 newValue (uint120 oldValue) {
    sumUserRealizedPremiumPerReserveId[reserveId] = sumUserRealizedPremiumPerReserveId[reserveId] + newValue - oldValue;
}

hook Sload uint120 value _userPositions[KEY address user][KEY uint256 reserveId].realizedPremium {
    require sumUserRealizedPremiumPerReserveId[reserveId] >= value;
}

invariant userDrawnShareConsistency(uint256 reserveId, uint256 assetId_) 
    sumUserDrawnSharesPerReserveId[reserveId] == hub._spokes[spoke._reserves[reserveId].assetId][spoke].drawnShares &&
    ( reserveId >= spoke._reserveCount => 
        sumUserDrawnSharesPerReserveId[reserveId] == 0
    ) &&
    ( !spoke._reserveExists[hub][assetId_] => 
        hub._spokes[assetId_][spoke].drawnShares == 0
    ) 
    filtered {f -> f.selector != sig:multicall(bytes[]).selector}
    {
        preserved  with (env e) {
            require e.msg.sender != spoke;
            safeAssumptions();
        }
        preserved addReserve(address hub_, uint256 assetId_arg, address priceSource, ISpoke.ReserveConfig config, ISpoke.DynamicReserveConfig  dynamicConfig) with (env e) {
            require hub_ == hub && assetId_arg == assetId_;
            safeAssumptions();
        }
        preserved repay(uint256 otherReserveId, uint256 amount, address onBehalfOf) with (env e) {
            safeAssumptions();
            //proved in spoke.spec : uniqueAssetIdPerReserveId
            require (reserveId < spoke._reserveCount && otherReserveId < spoke._reserveCount && reserveId != otherReserveId ) => (spoke._reserves[reserveId].assetId != spoke._reserves[otherReserveId].assetId );
        }
        preserved borrow(uint256 otherReserveId, uint256 amount, address onBehalfOf) with (env e) {
            safeAssumptions();
            //proved in spoke.spec : uniqueAssetIdPerReserveId
            require (reserveId < spoke._reserveCount && otherReserveId < spoke._reserveCount && reserveId != otherReserveId ) => (spoke._reserves[reserveId].assetId != spoke._reserves[otherReserveId].assetId );
        }

    }

invariant userPremiumShareConsistency(uint256 reserveId, uint256 assetId_) 
    sumUserPremiumSharesPerReserveId[reserveId] == hub._spokes[spoke._reserves[reserveId].assetId][spoke].premiumShares &&
    ( reserveId >= spoke._reserveCount => 
        sumUserPremiumSharesPerReserveId[reserveId] == 0
    ) &&
    ( !spoke._reserveExists[hub][assetId_] => 
        hub._spokes[assetId_][spoke].premiumShares == 0
    ) 
    filtered {f -> f.selector != sig:multicall(bytes[]).selector}
    {
        preserved  with (env e) {
            require e.msg.sender != spoke;
            safeAssumptions();
        }
       preserved addReserve(address hub_, uint256 assetId_arg, address priceSource, ISpoke.ReserveConfig config, ISpoke.DynamicReserveConfig  dynamicConfig) with (env e) {
            require hub_ == hub && assetId_arg == assetId_;
            safeAssumptions();
        }
    }

invariant userPremiumOffsetConsistency(uint256 reserveId, uint256 assetId_) 
    sumUserPremiumOffsetPerReserveId[reserveId] == hub._spokes[spoke._reserves[reserveId].assetId][spoke].premiumOffset &&
    ( reserveId >= spoke._reserveCount => 
        sumUserPremiumOffsetPerReserveId[reserveId] == 0
    ) &&
    ( !spoke._reserveExists[hub][assetId_] => 
        hub._spokes[assetId_][spoke].premiumOffset == 0
    ) 
    filtered {f -> f.selector != sig:multicall(bytes[]).selector}
    {
        preserved  with (env e) {
            require e.msg.sender != spoke;
            safeAssumptions();
        }
       preserved addReserve(address hub_, uint256 assetId_arg, address priceSource, ISpoke.ReserveConfig config, ISpoke.DynamicReserveConfig  dynamicConfig) with (env e) {
            require hub_ == hub && assetId_arg == assetId_;
            safeAssumptions();
        }
    }

invariant userRealizedPremiumConsistency(uint256 reserveId, uint256 assetId_) 
    sumUserRealizedPremiumPerReserveId[reserveId] == hub._spokes[spoke._reserves[reserveId].assetId][spoke].realizedPremium &&
    ( reserveId >= spoke._reserveCount => 
        sumUserRealizedPremiumPerReserveId[reserveId] == 0
    ) &&
    ( !spoke._reserveExists[hub][assetId_] => 
        hub._spokes[assetId_][spoke].realizedPremium == 0
    ) 
    filtered {f -> f.selector != sig:multicall(bytes[]).selector}
    {
        preserved  with (env e) {
            require e.msg.sender != spoke;
            safeAssumptions();
        }
        preserved addReserve(address hub_, uint256 assetId_arg, address priceSource, ISpoke.ReserveConfig config, ISpoke.DynamicReserveConfig  dynamicConfig) with (env e) {
            require hub_ == hub && assetId_arg == assetId_;
            safeAssumptions();
        }
    }

// this does not pass because of the fee receiver check and the transferFeeShares which might lock shares
invariant userSuppliedShareConsistency(uint256 reserveId, uint256 assetId_) 
    sumUserSuppliedSharesPerReserveId[reserveId] <= hub._spokes[spoke._reserves[reserveId].assetId][spoke].addedShares
    && 
    ( reserveId >= spoke._reserveCount => 
        sumUserSuppliedSharesPerReserveId[reserveId] == 0
    )/* &&
    ( !spoke._reserveExists[hub][assetId_] => 
        hub._spokes[assetId_][spoke].addedShares == 0
    ) */
    {
        preserved  with (env e) {
            require e.msg.sender != spoke;
            safeAssumptions();
            require hub._assets[spoke._reserves[reserveId].assetId].feeReceiver != spoke;
            require hub._assets[assetId_].feeReceiver != spoke;
        }
        preserved addReserve(address hub_, uint256 assetId_arg, address priceSource, ISpoke.ReserveConfig config, ISpoke.DynamicReserveConfig  dynamicConfig) with (env e) {
            require hub_ == hub && assetId_arg == assetId_;
            safeAssumptions();
            require hub._assets[spoke._reserves[reserveId].assetId].feeReceiver != spoke;
            require hub._assets[assetId_].feeReceiver != spoke;
        }
    }


function safeAssumptions() {
    // rules proved in spoke.spec and assuming one hub
    require forall uint256 reserveId. forall uint256 otherReserveId. 
    (reserveId != otherReserveId ) => spoke._reserves[reserveId].assetId != spoke._reserves[otherReserveId].assetId ;

    // a reservid that exists has underlying and hub
    require forall uint256 reserveId. (reserveId < spoke._reserveCount  => 
    // has underlying and hub
    (spoke._reserves[reserveId].underlying != 0 && spoke._reserves[reserveId].hub == hub && spoke._reserveExists[spoke._reserves[reserveId].hub][spoke._reserves[reserveId].assetId] ));

    // a reservid that does not exist has no underlying, hub, assetId
    require forall uint256 reserveId. reserveId >= spoke._reserveCount => (
    // has no underlying, hub, assetId
    spoke._reserves[reserveId].underlying == 0 && spoke._reserves[reserveId].assetId == 0 && spoke._reserves[reserveId].hub == 0  && spoke._reserves[reserveId].dynamicConfigKey == 0); 

    // based on hubValidState.spec : validAssetId 
    require forall uint256 assetId. assetId >= hub._assetCount => (
        hub._assets[assetId].addedShares == 0 &&
        hub._assets[assetId].drawnShares == 0 &&
        hub._assets[assetId].premiumShares == 0 &&
        hub._assets[assetId].premiumOffset == 0 &&
        hub._assets[assetId].realizedPremium == 0 &&
        hub._assets[assetId].drawnIndex == 0 &&
        hub._assets[assetId].drawnRate == 0 &&
        hub._assets[assetId].lastUpdateTimestamp == 0 &&
        hub._spokes[assetId][spoke].addedShares == 0 &&
        hub._spokes[assetId][spoke].drawnShares == 0 &&
        hub._spokes[assetId][spoke].premiumShares == 0  &&
        hub._spokes[assetId][spoke].premiumOffset == 0 &&
        hub._spokes[assetId][spoke].realizedPremium == 0 &&
        !hub._spokes[assetId][spoke].active
        );

}