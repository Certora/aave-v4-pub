import "./symbolicRepresentation/Math_CVL.spec";
import "./symbolicRepresentation/ERC20s_CVL.spec";
import "./common.spec";



/***

Base definitions used in all of Spoke spec files

***/
methods {
    
    function _.sortByKey(KeyValueList.List memory array) internal
        => CVL_sort(array) expect void;

    // view function
    function _._hashTypedData(bytes32 structHash) internal => NONDET;

    /* assumes a deterministic non-zeroprice for the reserve pre block.timestamp */
    function _.getReservePrice(uint256 reserveId) external with (env e)=> symbolicPrice(reserveId, e.block.timestamp) expect uint256;

    function MathUtils.uncheckedExp(uint256 a, uint256 b) internal returns (uint256) => limitedExp(a,b);

    function _.consumeScheduledOp(address caller, bytes data) external => NONDET ALL;

    // assume setReserveSource is trusted and does not call back into spoke or hub or any of the assets 
    function _.setReserveSource(uint256 reserveId, address source) external => NONDET ALL;

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
//the non-zero assumption is enforced by the oracle 
ghost symbolicPrice(uint256 /*reserveId*/, uint256 /*timestamp*/) returns uint256 {
    axiom forall uint256 reserveId. forall uint256 timestamp. symbolicPrice(reserveId,timestamp) > 0;
}

definition outOfScopeFunctions(method f) returns bool =
    f.selector == sig:multicall(bytes[]).selector ||
    f.selector == sig:liquidationCall(uint256, uint256, address, uint256, bool).selector;


function limitedExp(uint256 a, uint256 b) returns (uint256){
    // assumes that b is always the decimals of an asset
    // computes 10^b
    assert a == 10;
    require ( b == 1 || b == 2 || b == 6 || b == 12 ||b == 18, "limiting exp, used as decimals only");
    if (b == 1) {
        return 10;
    }
    else if (b == 2) {
        return 100;
    }
    else if (b == 6) {
        return 1000000;
    }
    else if (b == 12) {
        return 1000000000000;
    }
    else if (b == 18) {
        return require_uint256(10 ^ 18);
    }
    else {
        require false;
        return 0;
    }
}

