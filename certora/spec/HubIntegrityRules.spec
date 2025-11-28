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

    add(e, assetId, amount);

    assert hub._assets[assetId].liquidity > internalBalanceBefore && hub._spokes[assetId][spoke].addedShares > spokeSharesBefore;
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
    uint256 spokeDrawnSharesBefore = hub._spokes[assetId][spoke].drawnShares;
    uint256 externalBalanceBefore = balanceByToken[asset][hub]; 
    uint256 toBalanceBefore = balanceByToken[asset][to];
    uint256 liquidityBefore = hub._assets[assetId].liquidity;

    draw(e,assetId,amount,to);

    assert hub._spokes[assetId][spoke].drawnShares > spokeDrawnSharesBefore &&
            balanceByToken[asset][hub] < externalBalanceBefore &&
            balanceByToken[asset][to] > toBalanceBefore &&
            hub._assets[assetId].liquidity < liquidityBefore;
}

/** @title Draw operation increases debt shares and transfers assets to recipient */
rule restore_debtDecrease(uint256 assetId, uint256 drawnAmount, IHubBase.PremiumDelta premiumDelta) {
    env e;
    requireAllInvariants(assetId,e);
    address spoke = e.msg.sender;
    uint256 beforeDebt = getSpokeTotalOwed(e, assetId, spoke);

    restore(e, assetId, drawnAmount, premiumDelta);
    
    uint256 afterDebt = getSpokeTotalOwed(e, assetId, spoke);
    assert beforeDebt >= afterDebt;
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
    uint256 premiumOffsetRay = hub._spokes[assetId][spoke].premiumOffsetRay;
    uint256 realizedPremiumRay = hub._spokes[assetId][spoke].realizedPremiumRay;
    
    bool active = hub._spokes[assetId][spoke].active;
    f(e,args);
    assert drawnShares < hub._spokes[assetId][spoke].drawnShares => active ;
    assert addedShares < hub._spokes[assetId][spoke].addedShares => active ;
    assert premiumShares < hub._spokes[assetId][spoke].premiumShares => active ;
    assert premiumOffsetRay < hub._spokes[assetId][spoke].premiumOffsetRay => active ;
    assert realizedPremiumRay < hub._spokes[assetId][spoke].realizedPremiumRay => active ;
}


/// @title spoke can not go over max allowed cap
rule spokeMaxCap(uint256 assetId, method f)
filtered { f -> !f.isView && 
        f.selector != sig:addSpoke(uint256,address,IHub.SpokeConfig).selector && 
        f.selector  != sig:updateSpokeConfig(uint256,address,IHub.SpokeConfig).selector &&
        f.selector != sig:updateAssetConfig(uint256,IHub.AssetConfig,bytes).selector } {
    env e;
    calldataarg args;
    address spoke = e.msg.sender;
    requireAllInvariants(assetId,e);
    require hub._assets[assetId].decimals == 1;
    uint256 addCapBefore = hub._spokes[assetId][spoke].addCap;
    uint256 drawCapBefore = hub._spokes[assetId][spoke].drawCap;
    require hub._spokes[assetId][spoke].addedShares <=  addCapBefore * 10; 
    require hub._spokes[assetId][spoke].drawnShares <=  drawCapBefore * 10; 
    
    require hub._assets[assetId].feeReceiver != spoke;
    f(e,args);

    uint256 addCapAfter = hub._spokes[assetId][spoke].addCap;
    uint256 drawCapAfter = hub._spokes[assetId][spoke].drawCap;
    assert addCapAfter == max_uint40 || hub._spokes[assetId][spoke].addedShares <=  addCapAfter * 10; 
    assert drawCapAfter == max_uint40 || hub._spokes[assetId][spoke].drawnShares <=  drawCapAfter * 10; 
}