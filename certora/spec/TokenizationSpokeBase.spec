/**
 * @title TokenizationSpoke shared CVL summarizations
 * @notice ECDSA / SignatureChecker nondet summaries, ERC20 internal summaries, and shared ghosts for TokenizationSpoke*.spec
 * @dev Import after `./symbolicRepresentation/ERC20s_CVL.spec`. Importing specs add hub envfree methods (if needed) and rules.
 *      Spoke envfree views and `mintCVL` / `burnCVL` live in this file; hub-linked specs extend with additional `methods` entries.
 *      Import `./symbolicRepresentation/ERC20s_CVL.spec` before this file; importing specs must repeat `using TokenizationSpokeInstance as tokenizationSpoke`.
 */

methods {
    // TokenizationSpokeInstance envfree methods
    function asset() external returns (address) envfree;
    function hub() external returns (address) envfree;
    function balanceOf(address account) external returns (uint256) envfree;
    function totalSupply() external returns (uint256) envfree;
    function assetId() external returns (uint256) envfree;

    // ECDSA internal functions => NONDET
    function ECDSA.tryRecover(bytes32, bytes memory) internal returns (address, ECDSA.RecoverError, bytes32) => NONDET;
    function ECDSA.tryRecoverCalldata(bytes32, bytes calldata) internal returns (address, ECDSA.RecoverError, bytes32) => NONDET;
    function ECDSA.recover(bytes32, bytes memory) internal returns (address) => NONDET;
    function ECDSA.recoverCalldata(bytes32, bytes calldata) internal returns (address) => NONDET;
    function ECDSA.tryRecover(bytes32, bytes32, bytes32) internal returns (address, ECDSA.RecoverError, bytes32) => NONDET;
    function ECDSA.recover(bytes32, bytes32, bytes32) internal returns (address) => NONDET;
    function ECDSA.tryRecover(bytes32, uint8, bytes32, bytes32) internal returns (address, ECDSA.RecoverError, bytes32) => NONDET;
    function ECDSA.recover(bytes32, uint8, bytes32, bytes32) internal returns (address) => NONDET;
    function ECDSA.parse(bytes memory) internal returns (uint8, bytes32, bytes32) => NONDET;
    function ECDSA.parseCalldata(bytes calldata) internal returns (uint8, bytes32, bytes32) => NONDET;

    // SignatureChecker internal functions => NONDET
    function SignatureChecker.isValidSignatureNow(address, bytes32, bytes memory) internal returns (bool) => NONDET;
    function SignatureChecker.isValidSignatureNowCalldata(address, bytes32, bytes calldata) internal returns (bool) => NONDET;
    function SignatureChecker.isValidERC1271SignatureNow(address, bytes32, bytes memory) internal returns (bool) => NONDET;
    function SignatureChecker.isValidSignatureNow(bytes memory, bytes32, bytes memory) internal returns (bool) => NONDET;
    function SignatureChecker.areValidSignaturesNow(bytes32, bytes[] memory, bytes[] memory) internal returns (bool) => NONDET;
    function IntentConsumer._verifyAndConsumeIntent(address signer, bytes32 intentHash, uint256 nonce, uint256 deadline, bytes calldata signature) internal => NONDET;

    // ERC20Upgradeable internal functions (ghost + ERC20s_CVL)
    function TokenizationSpokeInstance.totalSupply() internal returns (uint256) => totalSupplyGhost;

    function TokenizationSpokeInstance.balanceOf(address account) internal returns (uint256) =>
        tokenBalanceOf(currentContract, account);

    function TokenizationSpokeInstance.transfer(address to, uint256 amount) internal returns (bool) with (env e) =>
        transferCVL(currentContract, e.msg.sender, to, amount);

    function TokenizationSpokeInstance.transferFrom(address from, address to, uint256 amount) internal returns (bool) with (env e) =>
        transferFromCVL(currentContract, e.msg.sender, from, to, amount);

    function ERC20Upgradeable._mint(address account, uint256 value) internal => mintCVL(account, value);

    function ERC20Upgradeable._burn(address account, uint256 value) internal => burnCVL(account, value);
}

////////////////////////////////////////////////////////////////////////////
//                              Functions                                 //
////////////////////////////////////////////////////////////////////////////

function mintCVL(address account, uint256 value) {
    totalSupplyGhost = require_uint256(totalSupplyGhost + value);
    balanceByToken[currentContract][account] = require_uint256(balanceByToken[currentContract][account] + value);
}

function burnCVL(address account, uint256 value) {
    totalSupplyGhost = require_uint256(totalSupplyGhost - value);
    balanceByToken[currentContract][account] = require_uint256(balanceByToken[currentContract][account] - value);
}

////////////////////////////////////////////////////////////////////////////
//                              GHOSTS                                    //
////////////////////////////////////////////////////////////////////////////

ghost uint256 totalSupplyGhost {
    init_state axiom totalSupplyGhost == 0;
}

////////////////////////////////////////////////////////////////////////////
//                              DEFINITIONS                               //
////////////////////////////////////////////////////////////////////////////

// Helper to check if a method is out of scope
definition outOfScopeFunctions(method f) returns bool =
    f.selector == sig:TokenizationSpokeInstance.initialize(string,string).selector ||
    f.selector == sig:TokenizationSpokeInstance.permit(address,address,uint256,uint256,uint8,bytes32,bytes32).selector ||
    f.selector == sig:TokenizationSpokeInstance.depositWithPermit(uint256,address,uint256,uint8,bytes32,bytes32).selector ||
    f.selector == sig:TokenizationSpokeInstance.usePermitNonce().selector ||
    f.selector == sig:TokenizationSpokeInstance.renounceAllowance(address).selector;

////////////////////////////////////////////////////////////////////////////
//                                 RULES                                  //
////////////////////////////////////////////////////////////////////////////

/**
 * @title Total supply equals sum of per-account share balances
 * @link_property TokenizationSpoke valid state
 */
invariant totalSupplySumOfBalances()
    totalSupply() == (usum address a. balanceByToken[currentContract][a])
{
    //safely assumed every address has a balance of 0 at construction
    preserved constructor() with (env e) {
        require (usum address a. balanceByToken[currentContract][a]) == 0;
    }
}