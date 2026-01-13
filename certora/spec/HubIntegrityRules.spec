/**
Hub verification integrity rules that verify that change is consistent.
Accrue is assumed to be called already.

To run this spec file:
 certoraRun certora/conf/HubIntegrityRules.conf 
**/

import "./symbolicRepresentation/ERC20s_CVL.spec";
import "./symbolicRepresentation/Math_CVL.spec";
import "./HubValidState.spec";


/** @title Add operation increases external balances and increases internal accounting 
while decreasing from balance */
rule nothingForZero_add(uint256 assetId, uint256 amount, address from) {

    env e;
    address asset = hub._assets[assetId].underlying;
    address spoke = e.msg.sender;
    uint256 internalBalanceBefore = hub._assets[assetId].liquidity;
    uint256 spokeSharesBefore = hub._spokes[assetId][spoke].addedShares;

    uint256 sharesAdded =add(e, assetId, amount);

    assert hub._assets[assetId].liquidity > internalBalanceBefore && hub._spokes[assetId][spoke].addedShares == spokeSharesBefore + sharesAdded;
}


/** @title Remove operation decreases external balances and decreases internal accounting while increasing to balance*/
rule nothingForZero_remove(uint256 assetId, uint256 amount, address to) {

    env e;
    address asset = hub._assets[assetId].underlying;
    address spoke = e.msg.sender;
    uint256 externalBalanceBefore = balanceByToken[asset][hub]; 
    uint256 toBalanceBefore = balanceByToken[asset][to];
    uint256 spokeSharesBefore = hub._spokes[assetId][spoke].addedShares;

    remove(e, assetId, amount, to);

    assert balanceByToken[asset][hub] < externalBalanceBefore && hub._spokes[assetId][spoke].addedShares < spokeSharesBefore && toBalanceBefore < balanceByToken[asset][to];
    // no fee and no asset lost
    assert balanceByToken[asset][hub] + balanceByToken[asset][to] == externalBalanceBefore + toBalanceBefore; 
}

/** @title Draw operation increases debt shares and transfers assets to recipient */
rule nothingForZero_draw(uint256 assetId, uint256 amount, address to) {
    env e;
    address asset = hub._assets[assetId].underlying;
    address spoke = e.msg.sender;
    uint256 drawnSharesBefore = hub._spokes[assetId][spoke].drawnShares;
    uint256 externalBalanceBefore = balanceByToken[asset][hub]; 
    uint256 toBalanceBefore = balanceByToken[asset][to];
    uint256 liquidityBefore = hub._assets[assetId].liquidity;

    draw(e,assetId,amount,to);

    assert hub._spokes[assetId][spoke].drawnShares > drawnSharesBefore &&
            balanceByToken[asset][hub] < externalBalanceBefore &&
            balanceByToken[asset][to] > toBalanceBefore &&
            hub._assets[assetId].liquidity < liquidityBefore;
}

/** @title Restore operation decreases debt shares and increases liquidity */
rule nothingForZero_restore(uint256 assetId, uint256 drawnAmount, IHubBase.PremiumDelta premiumDelta) {
    env e;
    requireAllInvariants(assetId,e);
    address spoke = e.msg.sender;
    uint256 drawnSharesBefore = hub._spokes[assetId][spoke].drawnShares;
    mathint premiumRayBefore = hub._spokes[assetId][spoke].premiumShares * hub._assets[assetId].drawnIndex - hub._spokes[assetId][spoke].premiumOffsetRay;
    uint256 liquidityBefore = hub._assets[assetId].liquidity;
    
    restore(e, assetId, drawnAmount, premiumDelta);

    mathint premiumRayAfter = hub._spokes[assetId][spoke].premiumShares * hub._assets[assetId].drawnIndex - hub._spokes[assetId][spoke].premiumOffsetRay;
    assert (drawnSharesBefore > hub._spokes[assetId][spoke].drawnShares ||
            premiumRayBefore > premiumRayAfter) && 
            hub._assets[assetId].liquidity > liquidityBefore ;
}

rule nothingForZero_reportDeficit(uint256 assetId, uint256 drawnAmount, IHubBase.PremiumDelta premiumDelta) {
    env e;
    requireAllInvariants(assetId,e);
    address spoke = e.msg.sender;
    uint256 drawnSharesBefore = hub._spokes[assetId][spoke].drawnShares;
    mathint premiumRayBefore = hub._spokes[assetId][spoke].premiumShares * hub._assets[assetId].drawnIndex - hub._spokes[assetId][spoke].premiumOffsetRay;
    uint256 deficitRayBefore = hub._spokes[assetId][spoke].deficitRay;

    reportDeficit(e, assetId, drawnAmount, premiumDelta);

    mathint premiumRayAfter = hub._spokes[assetId][spoke].premiumShares * hub._assets[assetId].drawnIndex - hub._spokes[assetId][spoke].premiumOffsetRay;
    uint256 deficitRayAfter = hub._spokes[assetId][spoke].deficitRay;

    assert (drawnSharesBefore > hub._spokes[assetId][spoke].drawnShares ||
            premiumRayBefore > premiumRayAfter) && 
            deficitRayBefore < deficitRayAfter;
}

rule nothingForZero_eliminateDeficit(uint256 assetId, uint256 amount, address spoke) {
    env e;
    requireAllInvariants(assetId,e);

    uint256 senderAddedSharesBefore = hub._spokes[assetId][e.msg.sender].addedShares;
    uint256 deficitRayBefore = hub._spokes[assetId][spoke].deficitRay;
    
    eliminateDeficit(e, assetId, amount, spoke);

    uint256 deficitRayAfter = hub._spokes[assetId][spoke].deficitRay;
    assert (senderAddedSharesBefore > hub._spokes[assetId][e.msg.sender].addedShares &&
            deficitRayBefore > deficitRayAfter);
}

rule nothing_for_zero_sweep(uint256 assetId, uint256 amount) {
    env e;
    requireAllInvariants(assetId,e);
    sweep(e, assetId, amount);
    assert amount > 0 ;
}

rule nothing_for_zero_reclaim(uint256 assetId, uint256 amount) {
    env e;
    requireAllInvariants(assetId,e);
    reclaim(e, assetId, amount);
    assert amount > 0 ;
}

rule add_integrity(uint256 assetId, uint256 amount) {
    env e;
    requireAllInvariants(assetId,e);
    address spoke = e.msg.sender;

    uint256 drawnSharesBefore = hub._spokes[assetId][spoke].drawnShares;
    uint256 premiumSharesBefore = hub._spokes[assetId][spoke].premiumShares;    
    int200 premiumOffsetRayBefore = hub._spokes[assetId][spoke].premiumOffsetRay;
    uint256 deficitRayBefore = hub._spokes[assetId][spoke].deficitRay;
    uint256 spokeAddedShares_ = hub._spokes[assetId][spoke].addedShares;
    uint256 liquidityBefore = hub._assets[assetId].liquidity;

    add(e, assetId, amount);

    assert liquidityBefore == hub._assets[assetId].liquidity - amount;
    assert spokeAddedShares_ < hub._spokes[assetId][spoke].addedShares;
    assert premiumSharesBefore == hub._spokes[assetId][spoke].premiumShares;
    assert premiumOffsetRayBefore == hub._spokes[assetId][spoke].premiumOffsetRay;
    assert deficitRayBefore == hub._spokes[assetId][spoke].deficitRay;
    assert drawnSharesBefore == hub._spokes[assetId][spoke].drawnShares;
}

rule remove_integrity(uint256 assetId, uint256 amount, address to) {
    env e;
    requireAllInvariants(assetId,e);
    address spoke = e.msg.sender;
    address asset = hub._assets[assetId].underlying;
    uint256 drawnSharesBefore = hub._spokes[assetId][spoke].drawnShares;
    uint256 premiumSharesBefore = hub._spokes[assetId][spoke].premiumShares;    
    int200 premiumOffsetRayBefore = hub._spokes[assetId][spoke].premiumOffsetRay;
    uint256 deficitRayBefore = hub._spokes[assetId][spoke].deficitRay;
    uint256 spokeAddedShares_ = hub._spokes[assetId][spoke].addedShares;
    uint256 liquidityBefore = hub._assets[assetId].liquidity;
    uint256 externalBalanceBefore = balanceByToken[asset][hub]; 
    uint256 toBalanceBefore = balanceByToken[asset][to];

    remove(e, assetId, amount, to);

    assert drawnSharesBefore == hub._spokes[assetId][spoke].drawnShares;
    assert premiumSharesBefore == hub._spokes[assetId][spoke].premiumShares;
    assert premiumOffsetRayBefore == hub._spokes[assetId][spoke].premiumOffsetRay;
    assert deficitRayBefore == hub._spokes[assetId][spoke].deficitRay;
    assert spokeAddedShares_ > hub._spokes[assetId][spoke].addedShares;
    assert liquidityBefore == hub._assets[assetId].liquidity + amount;
    assert to!=hub => externalBalanceBefore == balanceByToken[asset][hub] + amount;
    assert to!=hub => toBalanceBefore == balanceByToken[asset][to] - amount;
}

rule draw_integrity(uint256 assetId, uint256 amount, address to) {
    env e;
    requireAllInvariants(assetId,e);
    address spoke = e.msg.sender;
    address asset = hub._assets[assetId].underlying;
    uint256 drawnSharesBefore = hub._spokes[assetId][spoke].drawnShares;
    mathint premiumRayBefore = hub._spokes[assetId][spoke].premiumShares * hub._assets[assetId].drawnIndex - hub._spokes[assetId][spoke].premiumOffsetRay;
    uint256 spokeAddedShares_ = hub._spokes[assetId][spoke].addedShares;
    uint256 deficitRayBefore = hub._spokes[assetId][spoke].deficitRay;
    uint256 liquidityBefore = hub._assets[assetId].liquidity;
    uint256 externalBalanceBefore = balanceByToken[asset][hub]; 
    uint256 toBalanceBefore = balanceByToken[asset][to];

    draw(e, assetId, amount, to);

    assert drawnSharesBefore < hub._spokes[assetId][spoke].drawnShares;
    assert premiumRayBefore == hub._spokes[assetId][spoke].premiumShares * hub._assets[assetId].drawnIndex - hub._spokes[assetId][spoke].premiumOffsetRay;
    assert spokeAddedShares_ == hub._spokes[assetId][spoke].addedShares;
    assert deficitRayBefore == hub._spokes[assetId][spoke].deficitRay;
    assert liquidityBefore == hub._assets[assetId].liquidity + amount;
    assert to!=hub => externalBalanceBefore == balanceByToken[asset][hub] +  amount;
    assert to!=hub => toBalanceBefore == balanceByToken[asset][to] - amount;
}

/** @title Draw operation increases debt shares and transfers assets to recipient */
rule restore_integrity(uint256 assetId, uint256 drawnAmount, IHubBase.PremiumDelta premiumDelta) {
    env e;
    requireAllInvariants(assetId,e);
    address spoke = e.msg.sender;
    uint256 beforeDebt = getSpokeTotalOwed(e, assetId, spoke);
    uint256 drawnSharesBefore = hub._spokes[assetId][spoke].drawnShares;
    mathint premiumRayBefore = hub._spokes[assetId][spoke].premiumShares * hub._assets[assetId].drawnIndex - hub._spokes[assetId][spoke].premiumOffsetRay;
    uint256 deficitRayBefore = hub._spokes[assetId][spoke].deficitRay;
    uint256 spokeAddedShares_ = hub._spokes[assetId][spoke].addedShares;
    uint256 liquidityBefore = hub._assets[assetId].liquidity;

    restore(e, assetId, drawnAmount, premiumDelta);
    
    uint256 afterDebt = getSpokeTotalOwed(e, assetId, spoke);
    assert beforeDebt >= afterDebt;
    assert drawnSharesBefore >= hub._spokes[assetId][spoke].drawnShares;
    assert premiumRayBefore >= hub._spokes[assetId][spoke].premiumShares * hub._assets[assetId].drawnIndex - hub._spokes[assetId][spoke].premiumOffsetRay;
    assert deficitRayBefore == hub._spokes[assetId][spoke].deficitRay;
    assert spokeAddedShares_ == hub._spokes[assetId][spoke].addedShares;
    // liquidity can increase by more than the drawn amount due to Premium
    assert liquidityBefore <= hub._assets[assetId].liquidity - drawnAmount;
}

rule reportDeficit_integrity(uint256 assetId, uint256 drawnAmount, IHubBase.PremiumDelta premiumDelta) {
    env e;
    requireAllInvariants(assetId,e);
    address spoke = e.msg.sender;
    uint256 drawnSharesBefore = hub._spokes[assetId][spoke].drawnShares;
    mathint premiumRayBefore = hub._spokes[assetId][spoke].premiumShares * hub._assets[assetId].drawnIndex - hub._spokes[assetId][spoke].premiumOffsetRay;
    uint256 deficitRayBefore = hub._spokes[assetId][spoke].deficitRay;
    uint256 spokeAddedShares_ = hub._spokes[assetId][spoke].addedShares;
    uint256 liquidityBefore = hub._assets[assetId].liquidity;

    reportDeficit(e, assetId, drawnAmount, premiumDelta);

    assert drawnSharesBefore >= hub._spokes[assetId][spoke].drawnShares;
    assert premiumRayBefore >= hub._spokes[assetId][spoke].premiumShares * hub._assets[assetId].drawnIndex - hub._spokes[assetId][spoke].premiumOffsetRay;
    assert deficitRayBefore <= hub._spokes[assetId][spoke].deficitRay;
    assert spokeAddedShares_ == hub._spokes[assetId][spoke].addedShares;
    assert liquidityBefore == hub._assets[assetId].liquidity;
}

rule eliminateDeficit_integrity(uint256 assetId, uint256 amount, address spoke) {
    env e;
    requireAllInvariants(assetId,e);
    uint256 spokeAddedShares_ = hub._spokes[assetId][e.msg.sender].addedShares;
    uint256 liquidityBefore = hub._assets[assetId].liquidity;
    uint256 drawnSharesBefore = hub._spokes[assetId][e.msg.sender].drawnShares;
    uint256 premiumSharesBefore = hub._spokes[assetId][e.msg.sender].premiumShares;    
    int200 premiumOffsetRayBefore = hub._spokes[assetId][e.msg.sender].premiumOffsetRay;
    uint256 deficitRayBefore = hub._spokes[assetId][spoke].deficitRay;
    uint256 senderDeficitRayBefore = hub._spokes[assetId][e.msg.sender].deficitRay;

    eliminateDeficit(e, assetId, amount, spoke);

    assert spokeAddedShares_ >= hub._spokes[assetId][e.msg.sender].addedShares;
    assert liquidityBefore == hub._assets[assetId].liquidity ;
    assert drawnSharesBefore == hub._spokes[assetId][e.msg.sender].drawnShares;
    assert premiumSharesBefore == hub._spokes[assetId][e.msg.sender].premiumShares;
    assert premiumOffsetRayBefore == hub._spokes[assetId][e.msg.sender].premiumOffsetRay;
    assert deficitRayBefore > hub._spokes[assetId][spoke].deficitRay;
    assert e.msg.sender != spoke => senderDeficitRayBefore == hub._spokes[assetId][e.msg.sender].deficitRay;
}

rule sweep_integrity(uint256 assetId, uint256 amount) {
    env e;
    requireAllInvariants(assetId,e);
    address asset = hub._assets[assetId].underlying;
    uint256 liquidityBefore = hub._assets[assetId].liquidity;
    uint256 externalBalanceBefore = balanceByToken[asset][hub]; 
    uint256 toBalanceBefore = balanceByToken[asset][e.msg.sender];
    uint256 sweptBefore = hub._assets[assetId].swept;
    uint256 spokeAddedShares_ = hub._spokes[assetId][e.msg.sender].addedShares;
    uint256 drawnSharesBefore = hub._spokes[assetId][e.msg.sender].drawnShares;
    uint256 premiumSharesBefore = hub._spokes[assetId][e.msg.sender].premiumShares;    
    int200 premiumOffsetRayBefore = hub._spokes[assetId][e.msg.sender].premiumOffsetRay;
    uint256 deficitRayBefore = hub._spokes[assetId][e.msg.sender].deficitRay;

    sweep(e, assetId, amount);

    assert liquidityBefore == hub._assets[assetId].liquidity + amount;
    assert e.msg.sender!=hub => externalBalanceBefore == balanceByToken[asset][hub] + amount;
    assert e.msg.sender!=hub => toBalanceBefore == balanceByToken[asset][e.msg.sender] - amount;
    assert sweptBefore == hub._assets[assetId].swept - amount;
    assert spokeAddedShares_ == hub._spokes[assetId][e.msg.sender].addedShares;
    assert drawnSharesBefore == hub._spokes[assetId][e.msg.sender].drawnShares;
    assert premiumSharesBefore == hub._spokes[assetId][e.msg.sender].premiumShares;
    assert premiumOffsetRayBefore == hub._spokes[assetId][e.msg.sender].premiumOffsetRay;
    assert deficitRayBefore == hub._spokes[assetId][e.msg.sender].deficitRay;
    assert e.msg.sender == hub._assets[assetId].reinvestmentController;
}

rule reclaim_integrity(uint256 assetId, uint256 amount) {
    env e;
    requireAllInvariants(assetId,e);
    address asset = hub._assets[assetId].underlying;
    uint256 liquidityBefore = hub._assets[assetId].liquidity;
    uint256 externalBalanceBefore = balanceByToken[asset][hub]; 
    uint256 fromBalanceBefore = balanceByToken[asset][e.msg.sender];
    uint256 sweptBefore = hub._assets[assetId].swept;
    uint256 spokeAddedShares_ = hub._spokes[assetId][e.msg.sender].addedShares;
    uint256 drawnSharesBefore = hub._spokes[assetId][e.msg.sender].drawnShares;
    uint256 premiumSharesBefore = hub._spokes[assetId][e.msg.sender].premiumShares;    
    int200 premiumOffsetRayBefore = hub._spokes[assetId][e.msg.sender].premiumOffsetRay;
    uint256 deficitRayBefore = hub._spokes[assetId][e.msg.sender].deficitRay;

    reclaim(e, assetId, amount);

    assert liquidityBefore == hub._assets[assetId].liquidity - amount;
    assert e.msg.sender!=hub => externalBalanceBefore == balanceByToken[asset][hub] - amount;
    assert e.msg.sender!=hub => fromBalanceBefore == balanceByToken[asset][e.msg.sender] + amount;
    assert sweptBefore == hub._assets[assetId].swept + amount;
    assert spokeAddedShares_ == hub._spokes[assetId][e.msg.sender].addedShares;
    assert drawnSharesBefore == hub._spokes[assetId][e.msg.sender].drawnShares;
    assert premiumSharesBefore == hub._spokes[assetId][e.msg.sender].premiumShares;
    assert premiumOffsetRayBefore == hub._spokes[assetId][e.msg.sender].premiumOffsetRay;
    assert deficitRayBefore == hub._spokes[assetId][e.msg.sender].deficitRay;
    assert e.msg.sender == hub._assets[assetId].reinvestmentController;
}

/// @title reportDeficit return same value as previewRestoreByAssetsCVL
rule reportDeficitSameAsPreviewRestoreByAssets(uint256 assetId, uint256 drawnAmount) {
    env e;
    address spoke = e.msg.sender;
    IHubBase.PremiumDelta premiumDelta;
    requireAllInvariants(assetId,e);
    storage init = lastStorage;
    uint256 resultPreview = previewRestoreByAssets(e, assetId, drawnAmount);
    uint256 resultReportDeficit = reportDeficit(e, assetId, drawnAmount, premiumDelta);
    assert resultReportDeficit == resultPreview;
}

/// @title only valid spoke can call the function
rule validSpokeOnly(uint256 assetId, method f) {
    env e;
    calldataarg args;
    address spoke = e.msg.sender;
    uint256 drawnShares = hub._spokes[assetId][spoke].drawnShares;
    uint256 addedShares = hub._spokes[assetId][spoke].addedShares;
    uint256 premiumShares = hub._spokes[assetId][spoke].premiumShares;
    int200 premiumOffsetRay = hub._spokes[assetId][spoke].premiumOffsetRay;
    uint200 deficitRay = hub._spokes[assetId][spoke].deficitRay;
    bool active = hub._spokes[assetId][spoke].active;
    
    f(e,args);

    assert drawnShares != hub._spokes[assetId][spoke].drawnShares => active ;
    assert addedShares != hub._spokes[assetId][spoke].addedShares => (active || (hub._assets[assetId].feeReceiver == spoke && f.selector == sig:payFeeShares(uint256,uint256).selector));
    assert premiumShares != hub._spokes[assetId][spoke].premiumShares => active ;
    assert deficitRay != hub._spokes[assetId][spoke].deficitRay => active ;
    assert premiumOffsetRay != hub._spokes[assetId][spoke].premiumOffsetRay => active ;
}

rule frontRunOnRefreshPremium(uint256 assetId) {
    env e;
    env eBefore; calldataarg args; 

    require eBefore.msg.sender != e.msg.sender;
    require eBefore.block.timestamp <=  e.block.timestamp;

    requireAllInvariants(assetId,eBefore);
    requireInvariant premiumOffset_Integrity(assetId, e.msg.sender);
    calldataarg argsRefresh;
    storage init_state = lastStorage;
    refreshPremium(e,argsRefresh);
    refreshPremium(eBefore,args);
    refreshPremium(eBefore,args) at init_state;
    //just to avoid overflows
    require getAddedAssets(e,assetId) >= getAddedShares(e,assetId);
    refreshPremium@withrevert(e,argsRefresh);
    assert !lastReverted;
}