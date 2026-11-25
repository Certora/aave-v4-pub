// SPDX-License-Identifier: MIT
pragma solidity 0.8.28;

import {ERC20} from 'src/dependencies/openzeppelin/ERC20.sol';

/// @notice The two ERC20 tokens of the BabylonLiquidationSplitting.spec scene: the unmodified OpenZeppelin ERC20.
/// @dev Two contracts, so that the debt underlying and the collateral underlying can be different tokens.
contract LiquidationSplittingTokenA is ERC20 {
  constructor() ERC20('Token A', 'A') {}
}

contract LiquidationSplittingTokenB is ERC20 {
  constructor() ERC20('Token B', 'B') {}
}
