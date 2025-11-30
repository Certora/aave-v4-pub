
/***

Verify Hub - valid state properties 
Where we assume a given single drawnIndex and that accrue was called on the asset

To run this spec file:
 certoraRun certora/conf/HubValidState.conf 
***/

import "./symbolicRepresentation/ERC20s_CVL.spec";
import "./symbolicRepresentation/Math_CVL.spec";
import "./HubBase.spec";


using Hub as hub;


methods {

    // assume that drawn rate was already updated.
    //rules concerning updateDrawnRate are in HubAccrueIntegrity.spec
    function AssetLogic.updateDrawnRate(
        IHub.Asset storage asset,
        uint256 assetId
    ) internal => NONDET;

    //assume a given single drawnIndex
    //rules concerning getDrawnIndex are in HubAccrueIntegrity.spec
    function AssetLogic.getDrawnIndex(IHub.Asset storage   asset) internal returns (uint256) => cachedIndex;

    //rules concerning accrue are in HubAccrueIntegrity.spec
    function AssetLogic.accrue(IHub.Asset storage asset) internal => accrueCalled();

}

/************ Ghost Variables ************/

// assume a given single drawnIndex
ghost uint256 cachedIndex;


ghost mapping(uint256 /*assetId*/  => mapping(address /*spoke*/ => uint256 )) spokeSupplyPerAssetMirror {
    init_state axiom forall uint256 X. forall address Y. spokeSupplyPerAssetMirror[X][Y] == 0 ;
    init_state axiom forall uint256 X. (usum address a. spokeSupplyPerAssetMirror[X][a]) == 0; 
}

ghost mapping(uint256 /*assetId*/  => mapping(address /*spoke*/ => uint256 )) spokePremiumDrawnSharesPerAssetMirror {
    init_state axiom forall uint256 X. forall address Y. spokePremiumDrawnSharesPerAssetMirror[X][Y] == 0 ;
    init_state axiom forall uint256 X. (usum address a. spokePremiumDrawnSharesPerAssetMirror[X][a]) == 0; 
}

ghost mapping(uint256 /*assetId*/  => mapping(address /*spoke*/ => uint256 )) spokeBaseDrawnPerAssetMirror {
    init_state axiom forall uint256 X. forall address Y. spokeBaseDrawnPerAssetMirror[X][Y] == 0 ;
    init_state axiom forall uint256 X. (usum address a. spokeBaseDrawnPerAssetMirror[X][a]) == 0; 
}

ghost mapping(uint256 /*assetId*/  => mapping(address /*spoke*/ => int200 )) spokePremiumOffsetPerAssetMirror {
    init_state axiom forall uint256 X. forall address Y. spokePremiumOffsetPerAssetMirror[X][Y] == 0 ;
    init_state axiom forall uint256 X. (sum address a. spokePremiumOffsetPerAssetMirror[X][a]) == 0; 
}

ghost mapping(uint256 /*assetId*/  => mapping(address /*spoke*/ => uint256 )) spokeDeficitPerAssetMirror {
    init_state axiom forall uint256 X. forall address Y. spokeDeficitPerAssetMirror[X][Y] == 0 ;
    init_state axiom forall uint256 X. (usum address a. spokeDeficitPerAssetMirror[X][a]) == 0; 
}
ghost bool accrueCalledOnAsset;
//record accessed to debt fields before accrue
ghost bool unsafeAccessBeforeAccrue;

/********** Function summary *****/
function accrueCalled() {
    accrueCalledOnAsset = true; 
} 

/************ Hooks  ************/

hook Sstore _assets[KEY uint256 assetId].drawnIndex uint120 new_value (uint120 old_value) {
    unsafeAccessBeforeAccrue = unsafeAccessBeforeAccrue || !accrueCalledOnAsset;
}

hook Sload uint120 value _assets[KEY uint256 assetId].drawnIndex  {
    unsafeAccessBeforeAccrue = unsafeAccessBeforeAccrue || !accrueCalledOnAsset;
}
hook Sstore _assets[KEY uint256 assetId].addedShares uint120 new_value (uint120 old_value) {
    unsafeAccessBeforeAccrue = unsafeAccessBeforeAccrue || !accrueCalledOnAsset;
}

hook Sload uint120 value _assets[KEY uint256 assetId].addedShares  {
    unsafeAccessBeforeAccrue = unsafeAccessBeforeAccrue || !accrueCalledOnAsset;
}

hook Sstore hub._spokes[KEY uint256 assetId][KEY address spoke].drawnShares uint120 new_value (uint120 old_value) {
    spokeBaseDrawnPerAssetMirror[assetId][spoke] = new_value;
    unsafeAccessBeforeAccrue = unsafeAccessBeforeAccrue || !accrueCalledOnAsset;
}

hook Sload uint120 value hub._spokes[KEY uint256 assetId][KEY address spoke].drawnShares {
    require spokeBaseDrawnPerAssetMirror[assetId][spoke] == value;
    unsafeAccessBeforeAccrue = unsafeAccessBeforeAccrue || !accrueCalledOnAsset;
}

hook Sstore hub._spokes[KEY uint256 assetId][KEY address spoke].addedShares uint120 new_value (uint120 old_value) {
    spokeSupplyPerAssetMirror[assetId][spoke] = new_value;
    unsafeAccessBeforeAccrue = unsafeAccessBeforeAccrue || !accrueCalledOnAsset;
}

hook Sload uint120 value hub._spokes[KEY uint256 assetId][KEY address spoke].addedShares {
    require spokeSupplyPerAssetMirror[assetId][spoke] == value;
    unsafeAccessBeforeAccrue = unsafeAccessBeforeAccrue || !accrueCalledOnAsset;
}

hook Sstore hub._spokes[KEY uint256 assetId][KEY address spoke].premiumShares uint120 new_value (uint120 old_value) {
    spokePremiumDrawnSharesPerAssetMirror[assetId][spoke] = new_value;
    unsafeAccessBeforeAccrue = unsafeAccessBeforeAccrue || !accrueCalledOnAsset;
}

hook Sload uint120 value hub._spokes[KEY uint256 assetId][KEY address spoke].premiumShares {
    require spokePremiumDrawnSharesPerAssetMirror[assetId][spoke] == value;
    unsafeAccessBeforeAccrue = unsafeAccessBeforeAccrue || !accrueCalledOnAsset;
}

hook Sstore hub._spokes[KEY uint256 assetId][KEY address spoke].premiumOffsetRay int200 new_value (int200 old_value) {
    spokePremiumOffsetPerAssetMirror[assetId][spoke] = new_value;
    unsafeAccessBeforeAccrue = unsafeAccessBeforeAccrue || !accrueCalledOnAsset;
}

hook Sload int200 value hub._spokes[KEY uint256 assetId][KEY address spoke].premiumOffsetRay {
    require spokePremiumOffsetPerAssetMirror[assetId][spoke] == value;
    unsafeAccessBeforeAccrue = unsafeAccessBeforeAccrue || !accrueCalledOnAsset;
}

hook Sstore hub._spokes[KEY uint256 assetId][KEY address spoke].deficitRay uint200 new_value (uint200 old_value) {
    spokeDeficitPerAssetMirror[assetId][spoke] = new_value;
    unsafeAccessBeforeAccrue = unsafeAccessBeforeAccrue || !accrueCalledOnAsset;
}

hook Sload uint200 value hub._spokes[KEY uint256 assetId][KEY address spoke].deficitRay {
    require spokeDeficitPerAssetMirror[assetId][spoke] == value;
    unsafeAccessBeforeAccrue = unsafeAccessBeforeAccrue || !accrueCalledOnAsset;
}
/**** Valid State Rules *******/


definition emptyAsset(uint256 assetId) returns bool =
    hub._assets[assetId].addedShares == 0 &&
        hub._assets[assetId].liquidity == 0 &&
        hub._assets[assetId].addedShares == 0 &&
        hub._assets[assetId].deficitRay == 0 &&
        hub._assets[assetId].swept == 0 &&
        hub._assets[assetId].premiumShares == 0 &&
        hub._assets[assetId].premiumOffsetRay == 0 &&
        hub._assets[assetId].drawnShares == 0 &&
        hub._assets[assetId].drawnIndex == 0 &&
        hub._assets[assetId].drawnRate == 0 &&
        hub._assets[assetId].lastUpdateTimestamp == 0 &&
        hub._assets[assetId].underlying == 0 &&
        ( forall address spoke. 
            hub._spokes[assetId][spoke].addedShares == 0 &&
            hub._spokes[assetId][spoke].drawnShares == 0 &&
            hub._spokes[assetId][spoke].premiumShares == 0  &&
            hub._spokes[assetId][spoke].premiumOffsetRay == 0 &&
            !hub._spokes[assetId][spoke].active &&
            assetToSpokeIndexes[assetId][to_bytes32(spoke)] == 0
        );
        


/** @title integrity of a validAsset 
**/
invariant validAssetId(uint256 assetId, address asset )  
    // ensure that the asset is empty
    (assetId >= hub._assetCount => emptyAsset(assetId)) &&
    // existence of the asset
    (assetId < hub._assetCount => 
        // uniqueness of underlying
        (forall uint256 otherAssetId. otherAssetId != assetId => hub._assets[assetId].underlying != hub._assets[otherAssetId].underlying ) &&
        // in list of underlying assets
        (underlyingAssetsIndexes[to_bytes32(hub._assets[assetId].underlying)] != 0)) &&
    // not in underlyingAssetsIndexes implies no assetId with this underlying
     (forall address asset1. asset1!=0 && underlyingAssetsIndexes[to_bytes32(asset1)] == 0 => (forall uint256 anyAssetId. hub._assets[anyAssetId].underlying != asset1 ))
    {
        preserved {
            requireInvariant assetToSpokesIntegrity(assetId);
            requireInvariant underlyingAssetsIntegrity();
            //requireInvariant validAssetId(otherAssetId, assetId);
        }
        preserved addAsset(address underlying, uint8 _decimals, address _feeReceiver, address _irStrategy, bytes _irData) with (env e) {
            requireInvariant assetToSpokesIntegrity(assetId);
            requireInvariant underlyingAssetsIntegrity();
            require underlying == asset;
        }
    }




/**
* @title the sum of  hub._spokes[assetId][spoke].addedShares for all spoke equals to hub._assets[assetId].addedShares
*/
invariant sumOfSpokeSupplyShares(uint256 assetId) 
    hub._assets[assetId].addedShares == (usum address spoke. spokeSupplyPerAssetMirror[assetId][spoke]) 
    {
        preserved {
            address anyAsset;
            requireInvariant validAssetId(assetId, anyAsset);
        }
    }

/**
* @title the sum of  hub._spokes[assetId][spoke].drawnShares for all spoke equals to hub._assets[assetId].drawnShares
*/
invariant sumOfSpokeDrawnShares(uint256 assetId) 
    hub._assets[assetId].drawnShares == (usum address spoke. spokeBaseDrawnPerAssetMirror[assetId][spoke]) 
    {
        preserved {
            address anyAsset;   
            requireInvariant validAssetId(assetId, anyAsset);
        }
    }

/**
* @title the sum of  hub._spokes[assetId][spoke].premiumShares for all spoke equals to hub._assets[assetId].premiumShares
*/
invariant sumOfSpokePremiumDrawnShares(uint256 assetId) 
    hub._assets[assetId].premiumShares == (usum address spoke. spokePremiumDrawnSharesPerAssetMirror[assetId][spoke]) 
    {
        preserved {
            address anyAsset;
            requireInvariant validAssetId(assetId, anyAsset);
        }
    }

/**
* @title the sum of  hub._spokes[assetId][spoke].premiumOffsetRay for all spoke equals to hub._assets[assetId].premiumOffsetRay
*/
invariant sumOfSpokePremiumOffset(uint256 assetId) 
    hub._assets[assetId].premiumOffsetRay == (sum address spoke. spokePremiumOffsetPerAssetMirror[assetId][spoke]) 
    {
        preserved {
            address anyAsset;
            requireInvariant validAssetId(assetId, anyAsset);
        }
    }

/**
* @title the sum of  hub._spokes[assetId][spoke].deficitRay for all spoke equals to hub._assets[assetId].deficitRay
*/
invariant sumOfSpokeDeficit(uint256 assetId) 
    hub._assets[assetId].deficitRay == (usum address spoke. spokeDeficitPerAssetMirror[assetId][spoke]) 
    {
        preserved {
            address anyAsset;
            requireInvariant validAssetId(assetId, anyAsset);
        }
    }

/**
* @title drawnIndex is greater than or equal to RAY on regular assets
**/
invariant drawnIndexMin(uint256 assetId) 
    assetId < hub._assetCount => hub._assets[assetId].drawnIndex >= RAY
    {
        preserved {
            address anyAsset;
            requireInvariant validAssetId(assetId, anyAsset);
        }
    }

/**
 * @title liquidityFee upper bound: config.liquidityFee must not exceed PercentageMathExtended.PERCENTAGE_FACTOR
 */
invariant liquidityFee_upper_bound(uint256 assetId) 
    hub._assets[assetId].liquidityFee <= PERCENTAGE_FACTOR;


/**
 * @title premiumOffsetRay integrity: premiumOffsetRay must not exceed the premiumShares when converted to assets rounding up
 */
invariant premiumOffset_Integrity(uint256 assetId, address spokeId, env e) 
    previewRestoreByShares(e,assetId,hub._assets[assetId].premiumShares) * hub._assets[assetId].drawnIndex >=  hub._assets[assetId].premiumOffsetRay && 
    previewRestoreByShares(e,assetId,hub._spokes[assetId][spokeId].premiumShares) * hub._assets[assetId].drawnIndex >=  hub._spokes[assetId][spokeId].premiumOffsetRay 
    {
        preserved  with (env e1) {
            requireAllInvariants(assetId, e1);
        }

    }


/**
@title External balance is at least as internal accounting 
**/
strong invariant solvency_external(uint256 assetId )
    balanceByToken[hub._assets[assetId].underlying][hub] >=  hub._assets[assetId].liquidity
    {
        preserved  with (env e1) {
            requireAllInvariants(assetId, e1);
        }
        preserved reclaim(uint256 assetId2, uint256 amount) with (env e2)
        {
            require hub._assets[assetId2].reinvestmentController != hub;
            requireAllInvariants(assetId, e2);
        }

    }

/**
* @title the sum of added assets is greater than or equal to the sum of added shares
*/
invariant totalAssetsVsShares(uint256 assetId, env e) 
    getAddedAssets(e,assetId) >=  getAddedShares(e,assetId) {

        preserved with (env eInv) {
            require eInv.block.timestamp == e.block.timestamp;
            requireAllInvariants(assetId, e);
        }
    }

rule totalAssetsVsShares_eliminateDeficit(uint256 assetId, uint256 amount, address spoke) {
    env e;
    requireAllInvariants(assetId, e);
    eliminateDeficit(e, assetId, amount, spoke);
    assert getAddedAssets(e,assetId) >= getAddedShares(e,assetId);
}


///@title ghosts for _assetToSpokes EnumerableSet to keep track of the spokes for an asset
// part of proving validAssetId invariant
// For every storage variable we add a ghost field that is kept synchronized by hooks.
// The ghost fields can be accessed by the spec, even inside quantifiers.

// ghost field for the _values array
ghost mapping(uint256 => mapping(mathint => bytes32)) assetToSpokeValues {
    init_state axiom forall uint256 assetId. forall mathint x. assetToSpokeValues[assetId][x] == to_bytes32(0);
}
// ghost field for the _positions map
ghost mapping(uint256 => mapping(bytes32 => uint256)) assetToSpokeIndexes {
    init_state axiom forall uint256 assetId. forall bytes32 x. assetToSpokeIndexes[assetId][x] == 0;
}
// ghost field for the length of the values array (stored in offset 0)
ghost mapping(uint256 => uint256) assetToSpokeLength {
    init_state axiom forall uint256 assetId. assetToSpokeLength[assetId] == 0;
    // assumption: it's infeasible to grow the list to these many elements.
    axiom forall uint256 assetId. assetToSpokeLength[assetId] < max_uint256;
}

ghost mapping(bytes32 => uint256) underlyingAssetsIndexes {
    init_state axiom forall bytes32 x. underlyingAssetsIndexes[x] == 0;
}
ghost mapping(mathint => bytes32) underlyingAssetsValues {
    init_state axiom forall mathint x. underlyingAssetsValues[x] == to_bytes32(0);
}
ghost uint256 underlyingAssetsLength {
    init_state axiom underlyingAssetsLength == 0;
    // assumption: it's infeasible to grow the list to these many elements.
    axiom underlyingAssetsLength < max_uint256;
}

// HOOKS
// Store hook to synchronize assetToSpokeLength with the length of the set._inner._values array.
hook Sstore hub._assetToSpokes[KEY uint256 assetId]._inner._values.length uint256 newLength {
    assetToSpokeLength[assetId] = newLength;
}
// Store hook to synchronize assetToSpokeValues array with set._inner._values.
hook Sstore hub._assetToSpokes[KEY uint256 assetId]._inner._values[INDEX uint256 index] bytes32 newValue {
    assetToSpokeValues[assetId][index] = newValue;
}
// Store hook to synchronize assetToSpokeIndexes array with set._inner._positions.
hook Sstore hub._assetToSpokes[KEY uint256 assetId]._inner._positions[KEY bytes32 value] uint256 newIndex {
    assetToSpokeIndexes[assetId][value] = newIndex;
}

// The load hooks can use require to ensure that the ghost field has the same information as the storage.
// The require is sound, since the store hooks ensure the contents are always the same.  However we cannot
// prove that with invariants, since this would require the invariant to read the storage for all elements
// and neither storage access nor function calls are allowed in quantifiers.
//
// By following this simple pattern it is ensured that the ghost state and the storage are always the same
// and that the solver can use this knowledge in the proofs.

// Load hook to synchronize assetToSpokeLength with the length of the set._inner._values array.
hook Sload uint256 length hub._assetToSpokes[KEY uint256 assetId]._inner._values.length {
    require assetToSpokeLength[assetId] == length;
}
hook Sload bytes32 value hub._assetToSpokes[KEY uint256 assetId]._inner._values[INDEX uint256 index] {
    require assetToSpokeValues[assetId][index] == value;
}
hook Sload uint256 index hub._assetToSpokes[KEY uint256 assetId]._inner._positions[KEY bytes32 value] {
    require assetToSpokeIndexes[assetId][value] == index;
}


// Store hook to synchronize underlyingAssetsLength with the length of the set._inner._values array.
hook Sstore hub._underlyingAssets._inner._values.length uint256 newLength {
    underlyingAssetsLength = newLength;
}
// Store hook to synchronize underlyingAssetsValues array with set._inner._values.
hook Sstore hub._underlyingAssets._inner._values[INDEX uint256 index] bytes32 newValue {
    underlyingAssetsValues[index] = newValue;
}
// Store hook to synchronize underlyingAssetsIndexes array with set._inner._positions.
hook Sstore hub._underlyingAssets._inner._positions[KEY bytes32 value] uint256 newIndex {
    underlyingAssetsIndexes[value] = newIndex;
}

hook Sload uint256 length hub._underlyingAssets._inner._values.length {
    require underlyingAssetsLength == length;
}
hook Sload bytes32 value hub._underlyingAssets._inner._values[INDEX uint256 index] {
    require underlyingAssetsValues[index] == value;
}
hook Sload uint256 index hub._underlyingAssets._inner._positions[KEY bytes32 value] {
    require underlyingAssetsIndexes[value] == index;
}

// INVARIANTS

//  This is the main invariant stating that the indexes and values always match:
//        values[indexes[v] - 1] = v for all values v in the set
//    and indexes[values[i]] = i+1 for all valid indexes i.

invariant assetToSpokesIntegrity(uint256 assetId)
    (forall uint256 index. 0 <= index && index < assetToSpokeLength[assetId] => to_mathint(assetToSpokeIndexes[assetId][assetToSpokeValues[assetId][index]]) == index + 1)
    && (forall bytes32 value. assetToSpokeIndexes[assetId][value] == 0 ||
         (assetToSpokeValues[assetId][assetToSpokeIndexes[assetId][value] - 1] == value && assetToSpokeIndexes[assetId][value] >= 1 && assetToSpokeIndexes[assetId][value] <= assetToSpokeLength[assetId]));

invariant underlyingAssetsIntegrity()
    (forall uint256 index. 0 <= index && index < underlyingAssetsLength => to_mathint(underlyingAssetsIndexes[underlyingAssetsValues[index]]) == index + 1)
    && (forall bytes32 value. underlyingAssetsIndexes[value] == 0 ||
         (underlyingAssetsValues[underlyingAssetsIndexes[value] - 1] == value && underlyingAssetsIndexes[value] >= 1 && underlyingAssetsIndexes[value] <= underlyingAssetsLength));



// optimize the calls to certain function and save in ghost (global) variable) 
ghost uint256 addedAssetsBefore; 
ghost uint256 supplyShareBefore;

function requireAllInvariants(uint256 assetId, env e)  {
    // optimize (reuse) the calls to getAddedAssets() and getTotalAddedShares()
    addedAssetsBefore = getAddedAssets(e,assetId);
    supplyShareBefore = getAddedShares(e,assetId); 
    requireInvariant totalAssetsVsShares(assetId,e);
    require addedAssetsBefore >= supplyShareBefore, "optimization";
    

    requireInvariant solvency_external(assetId);
    requireInvariant sumOfSpokeDrawnShares(assetId);
    requireInvariant sumOfSpokeSupplyShares(assetId);
    requireInvariant sumOfSpokePremiumDrawnShares(assetId);
    requireInvariant sumOfSpokePremiumOffset(assetId);
    requireInvariant drawnIndexMin(assetId);
    requireInvariant assetToSpokesIntegrity(assetId);
    address anyAsset;   
    requireInvariant validAssetId(assetId, anyAsset);
    requireInvariant liquidityFee_upper_bound(assetId);
    requireInvariant premiumOffset_Integrity(assetId, e.msg.sender,e);
    requireInvariant underlyingAssetsIntegrity();
    require cachedIndex == hub._assets[assetId].drawnIndex;

} 