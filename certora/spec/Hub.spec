
/***

Verify Hub 

State changes rules in which the validate functions are ignored.
Assuming accrue has been called on the current block timestamp.


***/

import "./symbolicRepresentation/ERC20s_CVL.spec";
import "./symbolicRepresentation/Math_CVL.spec";
import "./HubValidState.spec";

methods {
    function _validateAdd(
        IHub.Asset storage asset,
        IHub.SpokeData storage spoke,
        uint256 amount
    ) internal => NONDET;

    function _validateRemove(
        IHub.SpokeData storage spoke,
        uint256 amount,
        address to
    ) internal => NONDET;

    function _validateDraw(
        IHub.Asset storage asset,
        IHub.SpokeData storage spoke,
        uint256 amount,
        address to
    ) internal => NONDET;

    function _validateRestore(
        IHub.Asset storage asset,
        IHub.SpokeData storage spoke,
        uint256 drawnAmount,
        uint256 premiumAmountRay
    ) internal => NONDET;

    function _validateReportDeficit(
        IHub.Asset storage asset,
        IHub.SpokeData storage spoke,
        uint256 drawnAmount,
        uint256 premiumAmountRay
    ) internal => NONDET;

    function _validateEliminateDeficit(
        IHub.SpokeData storage spoke,
        uint256 amount
    ) internal => NONDET;

    function _validatePayFeeShares(
        IHub.SpokeData storage senderSpoke,
        uint256 feeShares
    ) internal => NONDET;

    function _validateTransferShares(
        IHub.Asset storage asset,
        IHub.SpokeData storage sender,
        IHub.SpokeData storage receiver,
        uint256 shares
    ) internal => NONDET;

    function _validateSweep(
        IHub.Asset storage asset,
        address caller,
        uint256 amount
    ) internal => NONDET;

    function _validateReclaim(
        IHub.Asset storage asset,
        address caller,
        uint256 amount
    ) internal => NONDET;
}


/** @title supply rate is never decreasing
when not accruing interest, every function should never decrease supply exchange rate 
*/
rule supplyExchangeRateIsMonotonic(env e, method f, calldataarg args)
filtered {
    f -> !f.isView
}
{
    uint256 assetId;
    uint256 OneM = 1000000;

    requireAllInvariants(assetId, e);
    // use ghost to avoid repeating complex computation
    mathint assetsBefore = addedAssetsBefore;
    mathint sharesBefore = addedSharesBefore;

    require hub._assets[assetId].lastUpdateTimestamp == e.block.timestamp; 


    f(e, args);

    mathint assetsAfter = getAddedAssets(e,assetId);
    mathint sharesAfter = getAddedShares(e,assetId);
    require assetsAfter >= sharesAfter, "based on rule totalAssetsVsShares(assetId,e) and to help the prover";
    assert (assetsAfter + OneM) * (sharesBefore + OneM) >= (assetsBefore + OneM )* (sharesAfter + OneM);
}



/** @title No bad behavior change to a spoke's asset or debt. assume accrue has been called.  
**/
rule noChangeToOtherSpoke(address spoke, uint256 assetId, address otherSpoke, method f) 
    filtered { f -> !f.isView }
    {
    env e;
    
    require otherSpoke != spoke && e.msg.sender == spoke; 
    require hub._assets[assetId].lastUpdateTimestamp == e.block.timestamp; 
    requireAllInvariants(assetId, e);
    
    
    uint256 shares_ = getSpokeAddedShares(e, assetId, otherSpoke);
    uint256 deficit_ = getSpokeDeficitRay(e, assetId, otherSpoke);
    uint256 drawnShares_  = getSpokeDrawnShares(e, assetId, otherSpoke);
    uint256 premiumShares_; int256 premiumOffset_;
    premiumShares_, premiumOffset_ = getSpokePremiumData(e, assetId, otherSpoke);


    calldataarg args; 
    f(e,args);
    
    // shares can increase on feeReceiver or transferShares function 
    assert shares_ <= getSpokeAddedShares(e, assetId, otherSpoke);
    // deficit can decrease on eliminateDeficit function
    assert deficit_ >= getSpokeDeficitRay(e, assetId, otherSpoke);
    // drawn shares can not change
    assert drawnShares_ == getSpokeDrawnShares(e, assetId, otherSpoke);
    // premium shares and offset can not change
    uint256 premiumSharesAfter; int256 premiumOffsetAfter;
    premiumSharesAfter, premiumOffsetAfter = getSpokePremiumData(e, assetId, otherSpoke);
    assert premiumShares_ == premiumSharesAfter;
    assert premiumOffset_ == premiumOffsetAfter;
} 


/**
@title Accrue must be called before updating shares or debt. 
Transferring shares is safe without accrue, as it stays the same behavior 
Also adding an asset is safe without accrue, as there is nothing to update.
*/
rule accrueWasCalled(uint256 assetId, method f) filtered { f-> !f.isView && 
            f.selector != sig:addAsset(address,uint8,address,address,bytes).selector &&
            f.selector != sig:transferShares(uint256,uint256,address).selector}  
{
    require !unsafeAccessBeforeAccrue; 
    
    env e;
    calldataarg args;
    f(e,args);

    assert !unsafeAccessBeforeAccrue; 

}

/**
@title lastUpdateTimestamp is never updated if accrue was called already 
*/
rule lastUpdateTimestamp_notChanged(uint256 assetId, method f) filtered { f-> !f.isView} {
    env e;
    uint before = hub._assets[assetId].lastUpdateTimestamp;
    
    calldataarg args;
    f(e,args);

    assert hub._assets[assetId].lastUpdateTimestamp == before || ( hub._assets[assetId].lastUpdateTimestamp == e.block.timestamp && f.selector == sig:addAsset(address,uint8,address,address,bytes).selector);


}

/**
@title total assets is equal to the supplied amount when taking into account the virtual assets and shares
**/
rule totalAssetsCompareToSuppliedAmount_virtual(uint256 assetId, env e){
    requireAllInvariants(assetId, e); 
    uint256 oneM = 1000000;
    
    mathint addedAssets = getAddedAssets(e,assetId) + oneM;
    mathint addedShares = getAddedShares(e,assetId) + oneM;

    // rounding down
    assert addedAssets == previewRemoveByShares(e, assetId, require_uint256(addedShares));
    // rounding up
    assert addedAssets == previewAddByShares(e, assetId, require_uint256(addedShares));
}

/**
@title total assets is equal to or greater than the supplied amount without taking into account the virtual assets and shares
**/
rule totalAssetsCompareToSuppliedAmount_noVirtual(uint256 assetId, env e){
    requireAllInvariants(assetId, e); 
    mathint addedAssets = getAddedAssets(e,assetId);
    mathint addedShares = getAddedShares(e,assetId);

    assert addedAssets >= previewRemoveByShares(e, assetId, require_uint256(addedShares));
    satisfy addedAssets > previewRemoveByShares(e, assetId, require_uint256(addedShares));
    assert addedAssets >= previewAddByShares(e, assetId, require_uint256(addedShares));
    satisfy addedAssets > previewAddByShares(e, assetId, require_uint256(addedShares));
}