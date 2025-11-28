
import "./SpokeBase.spec";
//import "./symbolicRepresentation/SymbolicHub.spec";

// Spoke independent spec file. No link to hub and other contracts.
//////// symbolic hub starts here ////////
methods {
    
    function _.previewRemoveByShares(uint256 assetId, uint256 shares) external with (env e) => previewRemoveBySharesCVL(assetId, shares, e) expect uint256;

    function _.previewAddByAssets(uint256 assetId, uint256 assets) external with (env e) => previewAddByAssetsCVL(assetId, assets, e) expect uint256;

    function _.previewRemoveByAssets(uint256 assetId, uint256 assets) external with (env e) => previewRemoveByAssetsCVL(assetId, assets, e) expect uint256;

    function _.previewDrawByShares(uint256 assetId, uint256 shares) external with (env e) => previewDrawBySharesCVL(assetId, shares, e) expect uint256;

    function _.previewRestoreByShares(uint256 assetId, uint256 shares) external with (env e) => previewRestoreBySharesCVL(assetId, shares, e) expect uint256;

    function _.getAssetDrawnIndex(uint256 assetId) external with (env e) => getAssetDrawnIndexCVL(assetId, e) expect uint256;


// Supply Operations
    function _.add(uint256 assetId, uint256 amount) external with (env e) => addSummaryCVL(assetId, amount, e) expect uint256;
// Withdraw Operations  
    function _.remove(uint256 assetId, uint256 amount, address to) external with (env e) => removeSummaryCVL(assetId, amount, to, e) expect uint256;
// Borrow Operations
    function _.draw(uint256 assetId, uint256 amount, address to) external with (env e) => drawSummaryCVL(assetId, amount, to, e) expect uint256;
// Repay Operations
    function _.restore(uint256 assetId, uint256 drawnAmount, IHubBase.PremiumDelta premiumDelta) external with (env e) => restoreSummaryCVL(assetId, drawnAmount, premiumDelta, e) expect uint256;
// Report Deficit Operations
    function _.reportDeficit(uint256 assetId, uint256 drawnAmount, IHubBase.PremiumDelta premiumDelta) external with (env e) => previewRestoreByAssetsCVL(assetId, drawnAmount, e) expect uint256;
// Eliminate Deficit Operations
    function _.eliminateDeficit(uint256 assetId, uint256 amount, address spokeAddress) external with (env e)  => previewRemoveByAssetsCVL(assetId, amount, e) expect uint256; 
//refresh premium
    function _.refreshPremium(uint256 assetId, IHubBase.PremiumDelta premiumDelta) external => HAVOC_ECF;

// Pay Fee Shares Operations
    function _.payFeeShares(uint256 assetId, uint256 shares) external => NONDET;

    function _.getAssetUnderlyingAndDecimals(uint256 assetId) external => getAssetUnderlyingAndDecimalsCVL(assetId) expect (address, uint8);

}



persistent ghost uint256 RAY {
    axiom RAY == 10^27;
    init_state axiom RAY == 10^27;
    }

// symbolic debt index: for each assetId and block timestamp there is an index
// the index is monotonic increasing
persistent ghost mapping(uint256 /*assetId */ => mapping(uint256 /* blockTimestamp */ => uint256)) indexOfAssetPerBlock {
    axiom forall uint256 assetId. forall uint256 blockTimestamp. forall uint256 blockTimestamp2.
        blockTimestamp < blockTimestamp2 => indexOfAssetPerBlock[assetId][blockTimestamp] <= indexOfAssetPerBlock[assetId][blockTimestamp2];
    axiom forall uint256 assetId. forall uint256 blockTimestamp. indexOfAssetPerBlock[assetId][blockTimestamp] >= RAY;
}

// symbolic assets to share ratio:
persistent ghost mapping(uint256 /*assetId */ => mapping(uint256 /*blockTimestamp*/ => uint256)) shareToAssetsRatio {
    axiom forall uint256 assetId. forall uint256 blockTimestamp. forall uint256 blockTimestamp2.
        blockTimestamp < blockTimestamp2 => shareToAssetsRatio[assetId][blockTimestamp] <= shareToAssetsRatio[assetId][blockTimestamp2];
    // al least RAY assets per share
    axiom forall uint256 assetId. forall uint256 blockTimestamp. shareToAssetsRatio[assetId][blockTimestamp] >= RAY;
}

// toAddedSharesDown : assets.toSharesDown(asset.totalAddedAssets(), asset.totalAddedShares());
function previewAddByAssetsCVL(uint256 assetId, uint256 assets, env e) returns (uint256) {
    uint256 ratio = shareToAssetsRatio[assetId][e.block.timestamp];
    return require_uint256(((assets * RAY) + ratio -1) / ratio);
}

// toAddedAssetsDown : shares.toAssetsDown(asset.totalAddedAssets(), asset.totalAddedShares());
function previewRemoveBySharesCVL(uint256 assetId, uint256 shares, env e) returns (uint256) {
    uint256 ratio = shareToAssetsRatio[assetId][e.block.timestamp];
    return require_uint256(shares * ratio / RAY);
}

// toAddedSharesUp :assets.toSharesUp(asset.totalAddedAssets(), asset.totalAddedShares());
function previewRemoveByAssetsCVL(uint256 assetId, uint256 assets, env e) returns (uint256) {
    uint256 ratio = shareToAssetsRatio[assetId][e.block.timestamp];
    return require_uint256(((assets * RAY) + ratio -1) / ratio);
}

// toDrawnAssetsDown : shares.rayMulDown(asset.getDrawnIndex())
function previewDrawBySharesCVL(uint256 assetId, uint256 shares, env e) returns (uint256) {
    uint256 ratio = indexOfAssetPerBlock[assetId][e.block.timestamp];
    return require_uint256((shares * ratio) / RAY);
}

// toDrawnSharesUp : assets.rayDivUp(asset.getDrawnIndex())
function previewDrawByAssetsCVL(uint256 assetId, uint256 assets, env e) returns (uint256) {
    uint256 ratio = indexOfAssetPerBlock[assetId][e.block.timestamp];
    return require_uint256(((assets * RAY) + ratio -1) / ratio);

}
// toDrawnAssetsUp : shares.rayMulUp(asset.getDrawnIndex());
function previewRestoreBySharesCVL(uint256 assetId, uint256 shares, env e) returns (uint256) {
    uint256 ratio = indexOfAssetPerBlock[assetId][e.block.timestamp];
    return require_uint256(((shares * ratio) + RAY - 1) / RAY);
}

// toDrawnSharesDown : assets.rayDivDown(asset.getDrawnIndex());
function previewRestoreByAssetsCVL(uint256 assetId, uint256 assets, env e) returns (uint256) {
    uint256 ratio = indexOfAssetPerBlock[assetId][e.block.timestamp];
    return require_uint256(((assets * RAY) + ratio -1) / ratio);
}

// getAssetDrawnIndex: returns the drawn index for an asset at a given block timestamp
function getAssetDrawnIndexCVL(uint256 assetId, env e) returns (uint256) {
    return indexOfAssetPerBlock[assetId][e.block.timestamp];
}

// CVL function summarizations for Hub operations with zero amount checks
function addSummaryCVL(uint256 assetId, uint256 amount, env e) returns (uint256) {
    require amount > 0;
    // Return computed shares based on amount and asset using existing preview function
    return previewAddByAssetsCVL(assetId, amount, e);
}

function removeSummaryCVL(uint256 assetId, uint256 amount, address to, env e) returns (uint256) {
    require amount > 0;
    // Return computed shares based on amount and asset using existing preview function
    return previewRemoveByAssetsCVL(assetId, amount, e);
}

function drawSummaryCVL(uint256 assetId, uint256 amount, address to, env e) returns (uint256) {
    require amount > 0;
    // Return computed drawn shares based on amount and asset using existing preview function
    return previewDrawByAssetsCVL(assetId, amount, e);
}

function restoreSummaryCVL(uint256 assetId, uint256 drawnAmount, IHubBase.PremiumDelta premiumDelta,  env e) returns (uint256) {
    require drawnAmount > 0 ;
    // Return computed restored shares based on drawn amount using existing preview function
    return previewRestoreByAssetsCVL(assetId, drawnAmount, e);
}


ghost mapping(uint256 /*assetId*/ => address /*underlying*/) assetUnderlying;

ghost mapping(uint256 /*assetId*/ => uint8 /*decimals*/) assetDecimals;

function getAssetUnderlyingAndDecimalsCVL(uint256 assetId) returns (address, uint8) {
    return (assetUnderlying[assetId], assetDecimals[assetId]);
}


// Hooks to track userGhost for suppliedShares
hook Sstore _userPositions[KEY address user][KEY uint256 reserveId].suppliedShares uint120 newValue (uint120 oldValue) {
    require userGhost == user;
}

hook Sload uint120 value _userPositions[KEY address user][KEY uint256 reserveId].suppliedShares {
    require userGhost == user;
}

// Hooks to track userGhost for drawnShares
hook Sstore _userPositions[KEY address user][KEY uint256 reserveId].drawnShares uint120 newValue (uint120 oldValue) {
    require userGhost == user;
}

hook Sload uint120 value _userPositions[KEY address user][KEY uint256 reserveId].drawnShares {
    require userGhost == user;
}




rule increaseCollateralOrReduceDebtFunctions(method f) filtered {f -> !outOfScopeFunctions(f) && !f.isView && increaseCollateralOrReduceDebtFunctions(f)}  {
    uint256 reserveId; uint256 slot;
    address user;
    env e;
    setup();
    require userGhost == user;

    //user state before the operation
    bool beforePositionStatus_borrowing = isBorrowing[user][reserveId];
    bool beforePositionStatus_usingAsCollateral = isUsingAsCollateral[user][reserveId];
    uint120 beforeUserPosition_drawnShares = spoke._userPositions[user][reserveId].drawnShares;
    uint200 beforeUserPosition_realizedPremiumRay = spoke._userPositions[user][reserveId].realizedPremiumRay; 
    uint120 beforeUserPosition_premiumShares = spoke._userPositions[user][reserveId].premiumShares;
    uint200 beforeUserPosition_premiumOffsetRay = spoke._userPositions[user][reserveId].premiumOffsetRay;
    uint120 beforeUserPosition_suppliedShares = spoke._userPositions[user][reserveId].suppliedShares;
    uint24 beforeUserPosition_dynamicConfigKey = spoke._userPositions[user][reserveId].dynamicConfigKey;
    // Execute the operation 
    calldataarg args;
    f(e, args);
    
    // user state after the operation
    bool afterPositionStatus_borrowing = isBorrowing[user][reserveId];
    bool afterPositionStatus_usingAsCollateral = isUsingAsCollateral[user][reserveId];
    uint120 afterUserPosition_drawnShares = spoke._userPositions[user][reserveId].drawnShares;
    uint200 afterUserPosition_realizedPremiumRay = spoke._userPositions[user][reserveId].realizedPremiumRay;
    uint120 afterUserPosition_premiumShares = spoke._userPositions[user][reserveId].premiumShares;
    uint200 afterUserPosition_premiumOffsetRay = spoke._userPositions[user][reserveId].premiumOffsetRay;
    uint120 afterUserPosition_suppliedShares = spoke._userPositions[user][reserveId].suppliedShares;
    uint24 afterUserPosition_dynamicConfigKey = spoke._userPositions[user][reserveId].dynamicConfigKey;
    
    assert beforePositionStatus_borrowing == afterPositionStatus_borrowing || 
    (beforePositionStatus_borrowing && !afterPositionStatus_borrowing && afterUserPosition_drawnShares == 0 && afterUserPosition_realizedPremiumRay == 0 && afterUserPosition_premiumShares == 0 && afterUserPosition_premiumOffsetRay == 0);
    assert beforePositionStatus_usingAsCollateral == afterPositionStatus_usingAsCollateral;
    assert beforeUserPosition_drawnShares >= afterUserPosition_drawnShares;
    assert beforeUserPosition_realizedPremiumRay >= afterUserPosition_realizedPremiumRay;
    assert beforeUserPosition_premiumShares >= afterUserPosition_premiumShares;
    assert beforeUserPosition_premiumOffsetRay >= afterUserPosition_premiumOffsetRay;
    assert beforeUserPosition_suppliedShares <= afterUserPosition_suppliedShares;
    assert beforeUserPosition_dynamicConfigKey == afterUserPosition_dynamicConfigKey;
}


use invariant isBorrowingIFFdrawnShares;
// Note: validReserveId is now a require statement in setup() function in SpokeBase.spec


invariant drawnSharesZero(address user, uint256 reserveId) 
    spoke._userPositions[user][reserveId].drawnShares == 0 => (  spoke._userPositions[user][reserveId].premiumShares == 0 && spoke._userPositions[user][reserveId].premiumOffsetRay == 0 && spoke._userPositions[user][reserveId].realizedPremiumRay == 0) 
    filtered {f -> !outOfScopeFunctions(f) && 
    // repay is proved in SpokeHubIntegrity.spec
    f.selector != sig:repay(uint256, uint256, address).selector
    }
    {
        preserved with (env e) {
            setup();
        }
    }
    


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
    && spoke._userPositions[user][reserveId].suppliedShares == 0 && spoke._userPositions[user][reserveId].drawnShares == 0 &&
    // no premium shares or offset
    spoke._userPositions[user][reserveId].premiumShares == 0 && spoke._userPositions[user][reserveId].premiumOffsetRay == 0 &&
    // no realized premium
    spoke._userPositions[user][reserveId].realizedPremiumRay == 0 ))

    filtered {f -> !outOfScopeFunctions(f)}
    {
        preserved {
            requireInvariant validReserveId_single(reserveId);
        }
    }

// need to help the grounding, proven in validReserveId_single
function validReserveId_singleUser(uint256 reserveId, address user)  {
    require
    (reserveId < spoke._reserveCount  => 
    // has underlying and hub
    (spoke._reserves[reserveId].underlying != 0 && spoke._reserves[reserveId].hub != 0 && spoke._reserveExists[spoke._reserves[reserveId].hub][spoke._reserves[reserveId].assetId] ))
    &&
    // not exists
    (reserveId >= spoke._reserveCount =>
    // has no underlying, hub, assetId
    spoke._reserves[reserveId].underlying == 0 && spoke._reserves[reserveId].assetId == 0 && spoke._reserves[reserveId].hub == 0  && spoke._reserves[reserveId].dynamicConfigKey == 0 && !spoke._reserves[reserveId].paused && !spoke._reserves[reserveId].frozen && !spoke._reserves[reserveId].borrowable && spoke._reserves[reserveId].collateralRisk == 0 && 
    spoke._dynamicConfig[reserveId][0].collateralFactor == 0 &&
    // no one borrowed or used as collateral
    !isBorrowing[user][reserveId] && !isUsingAsCollateral[user][reserveId]
    // no supplied or drawn shares
    && spoke._userPositions[user][reserveId].suppliedShares == 0 && spoke._userPositions[user][reserveId].drawnShares == 0 &&
    // no premium shares or offset
    spoke._userPositions[user][reserveId].premiumShares == 0 && spoke._userPositions[user][reserveId].premiumOffsetRay == 0 &&
    // no realized premium
    spoke._userPositions[user][reserveId].realizedPremiumRay == 0 );
}


invariant uniqueAssetIdPerReserveId(uint256 reserveId, uint256 otherReserveId) 
    (reserveId < spoke._reserveCount && otherReserveId < spoke._reserveCount  && reserveId != otherReserveId ) => (spoke._reserves[reserveId].assetId != spoke._reserves[otherReserveId].assetId  || spoke._reserves[reserveId].hub != spoke._reserves[otherReserveId].hub)
    filtered {f -> !outOfScopeFunctions(f)}
    {
        preserved {
            requireInvariant validReserveId_single(reserveId);
            requireInvariant validReserveId_single(otherReserveId);
        }

    }


rule realizedPremiumRayConsistency(uint256 reserveId, address user, method f)
    filtered {f -> !outOfScopeFunctions(f) && !f.isView}
{
    env e;
    setup();
    requireInvariant validReserveId_single(reserveId);
    require userGhost == user;
    require spoke._userPositions[user][reserveId].realizedPremiumRay == spoke._userPositions[user][reserveId].premiumShares * getAssetDrawnIndexCVL(spoke._reserves[reserveId].assetId, e);
    calldataarg args;
    f(e, args);
    assert spoke._userPositions[user][reserveId].realizedPremiumRay == spoke._userPositions[user][reserveId].premiumShares * getAssetDrawnIndexCVL(spoke._reserves[reserveId].assetId, e);
}


    
/* todo: failing when collateralFactor becomes 0 
https://prover.certora.com/output/40726/b077c5f4ef564ee2936a9532c6c246f8/
*/
rule noCollateralNoDebt(uint256 reserveIdUsed, address user, method f) 
    filtered {f -> !outOfScopeFunctions(f) && !f.isView && increaseCollateralOrReduceDebtFunctions(f)} {
    env e;
    setup();
    requireInvariant validReserveId_single(reserveIdUsed);
    requireInvariant dynamicConfigKeyConsistency(reserveIdUsed,user);
    validReserveId_singleUser(reserveIdUsed, user);
    validReserveId_singleUser(spoke._reserveCount, user);
    require userGhost == user;
    ISpoke.UserAccountData beforeUserAccountData = getUserAccountData(e,user);
    uint24 dynamicConfigKey = spoke._reserves[reserveIdUsed].dynamicConfigKey;
    uint16 beforeCollateralFactor = spoke._dynamicConfig[reserveIdUsed][dynamicConfigKey].collateralFactor;
    require beforeUserAccountData.totalCollateralValue == 0 => beforeUserAccountData.totalDebtValue == 0;

    calldataarg args;
    f(e, args);

    ISpoke.UserAccountData afterUserAccountData = getUserAccountData(e,user);
    uint24 dynamicConfigKeyAfter = spoke._reserves[reserveIdUsed].dynamicConfigKey;
    uint16 afterCollateralFactor = spoke._dynamicConfig[reserveIdUsed][dynamicConfigKeyAfter].collateralFactor;
    if (f.selector == sig:addDynamicReserveConfig(uint256, ISpoke.DynamicReserveConfig).selector) {
        // assume we are working on reserveIdUsed
        require dynamicConfigKeyAfter != dynamicConfigKey;
    }
    require  beforeCollateralFactor > 0 => afterCollateralFactor > 0, "rule collateralFactorNotZero";
    assert afterUserAccountData.totalCollateralValue == 0 => afterUserAccountData.totalDebtValue == 0;
}

// need this to prove noCollateralNoDebt
rule collateralFactorNotZero(uint256 reserveId, address user, method f) filtered {f -> !outOfScopeFunctions(f) && !f.isView} {
    env e;
    setup();
    requireInvariant dynamicConfigKeyConsistency(reserveId,user);
    validReserveId_singleUser(reserveId, user);
    require userGhost == user;
    uint24 dynamicConfigKey;
    require dynamicConfigKey <= spoke._reserves[reserveId].dynamicConfigKey;
    require spoke._dynamicConfig[reserveId][dynamicConfigKey].collateralFactor > 0;
    calldataarg args;
    f(e, args);
    assert spoke._dynamicConfig[reserveId][dynamicConfigKey].collateralFactor > 0;
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
    && spoke._userPositions[user][reserveId].suppliedShares == 0 && spoke._userPositions[user][reserveId].drawnShares == 0 &&
    // no premium shares or offset
    spoke._userPositions[user][reserveId].premiumShares == 0 && spoke._userPositions[user][reserveId].premiumOffsetRay == 0 &&
    // no realized premium
    spoke._userPositions[user][reserveId].realizedPremiumRay == 0 &&

    // has no underlying, hub, assetId
    spoke._reserves[reserveId].underlying == 0 && spoke._reserves[reserveId].assetId == 0 && spoke._reserves[reserveId].hub == 0  && spoke._reserves[reserveId].dynamicConfigKey == 0 && !spoke._reserves[reserveId].paused && !spoke._reserves[reserveId].frozen && !spoke._reserves[reserveId].borrowable && spoke._reserves[reserveId].collateralRisk == 0 )))

    filtered {f -> f.selector != sig:multicall(bytes[]).selector && f.selector != sig:liquidationCall(uint256, uint256, address, uint256, bool).selector}



rule deterministicUserDebtValue(uint256 reserveId, address user) {
    env e;
    setup();
    require userGhost == user;
    uint256 drawnDebt; uint256 premiumDebt;
    (drawnDebt, premiumDebt) = spoke.getUserDebt(e, reserveId, user);
    uint256 drawnDebt2; uint256 premiumDebt2;
    (drawnDebt2, premiumDebt2) = spoke.getUserDebt(e, reserveId, user);
    assert drawnDebt == drawnDebt2;
    assert premiumDebt == premiumDebt2;
}

invariant dynamicConfigKeyConsistency(uint256 reserveId, address user)
    spoke._userPositions[user][reserveId].dynamicConfigKey <= spoke._reserves[reserveId].dynamicConfigKey
    filtered {f -> !outOfScopeFunctions(f)}
{
    preserved {
        setup();
        requireInvariant validReserveId_single(reserveId);
    }
}


