import "./symbolicRepresentation/Math_CVL.spec";
import "./symbolicRepresentation/SymbolicPositionStatus.spec";
import "./symbolicRepresentation/ERC20s_CVL.spec";

using WadRayMathWrapper as wadRayMath;
using SpokeInstance as spoke;

/***

Base definitions used in all of Spoke spec files

Here we have only safe assumptions, safe summarization that are either proved in math.spec or a nondet summary

***/
methods {
    

    function _.sortByKey(KeyValueList.List memory array) internal
        => CVL_sort(array) expect void;

    function _._hashTypedData(bytes32 structHash) internal => NONDET;

    function _.getReservePrice(uint256 reserveId) external with (env e)=> symbolicPrice(reserveId, e.block.timestamp) expect uint256;

    function MathUtils.uncheckedExp(uint256 a, uint256 b) internal returns (uint256) => limitedExp(a,b);

    function _.consumeScheduledOp(address caller, bytes data) external => NONDET ALL;
    function _.setReserveSource(uint256 reserveId, address source) external => NONDET ALL;


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



    function AuthorityUtils.canCallWithDelay(
    address authority,
    address caller,
    address target,
    bytes4 selector
  ) internal returns (bool, uint32) => NONDET ALL;

    function SignatureChecker.isValidERC1271SignatureNow(
    address signer,
    bytes32 hash,
    bytes memory signature
  ) internal returns (bool) => NONDET ALL;
}


definition increaseCollateralOrReduceDebtFunctions(method f) returns bool =
    f.selector != sig:withdraw(uint256, uint256, address).selector && 
    f.selector != sig:liquidationCall(uint256, uint256, address, uint256, bool).selector &&
    f.selector != sig:borrow(uint256, uint256, address).selector &&
    f.selector != sig:setUsingAsCollateral(uint256, bool, address).selector && 
    //f.selector != sig:repay(uint256,uint256,address).selector &&
    f.selector != sig:updateUserDynamicConfig(address).selector;


function my_nondet() returns (ISpoke.UserAccountData) {
    ISpoke.UserAccountData userAccountData;
    return userAccountData;
}

function CVL_sort(KeyValueList.List array) {
    if (array._inner.length > 1) {
        require(array._inner[0] < array._inner[1]);
    }
    if (array._inner.length > 2) {
        require(array._inner[1] < array._inner[2]);
    }
    if (array._inner.length > 3) {
        require(array._inner[2] < array._inner[3]);
    }
}


//deterministic non-zero value for each reserveId and timestamp
ghost symbolicPrice(uint256 /*reserveId*/, uint256 /*timestamp*/) returns uint256 {
    axiom forall uint256 reserveId. forall uint256 timestamp. symbolicPrice(reserveId,timestamp) > 0;
}

function mulDivCheckRounding(uint256 x, uint256 y, uint256 z, Math.Rounding rounding) returns (uint256){
    if (rounding == Math.Rounding.Floor) {
        return mulDivDownCVL(x,y,z);
    }
    else if (rounding == Math.Rounding.Ceil) {
        return mulDivUpCVL(x,y,z);
    }
    else {
        assert false; 
    }
    return 0;
}

function limitedExp(uint256 a, uint256 b) returns (uint256){
    // todo prove that b is always the decimals of an asset
    assert a == 10;
    require ( b == 1 || b == 2 || b == 6 || b == 128, "limiting exp, used as decimals only");
    if (b == 1) {
        return 10;
    }
    else if (b == 2) {
        return 100;
    }
    else if (b == 6) {
        return 1000000;
    }
    else if (b == 128) {
        return require_uint256(10 ^ 128);
    }
    else {
        require false;
        return 0;
    }
}

invariant isBorrowingIFFdrawnShares()  
forall uint256 reserveId. forall address user.
    spoke._userPositions[user][reserveId].drawnShares > 0   <=>  isBorrowing[user][reserveId]
filtered {f -> !outOfScopeFunctions(f)}

definition outOfScopeFunctions(method f) returns bool =
    f.selector == sig:multicall(bytes[]).selector ||
    f.selector == sig:liquidationCall(uint256, uint256, address, uint256, bool).selector;


function setup() {
    //requireInvariant validReserveId();
    //invariant validReserveId()
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
    requireInvariant isBorrowingIFFdrawnShares();
}