// SPDX-License-Identifier: MIT
pragma solidity 0.8.28;

/// @notice The oracle of the BabylonLiquidationSplitting.spec scene: one stored price per reserve.
/// @dev Stands in for AaveOracle and its price feeds. Like AaveOracle, it reverts on a zero price.
/// @dev Nothing writes the prices, so every read of a reserve's price during a rule returns the same value.
contract LiquidationSplittingOracle {
  mapping(uint256 reserveId => uint256) internal _prices;

  function getReservePrice(uint256 reserveId) external view returns (uint256) {
    uint256 price = _prices[reserveId];
    require(price > 0);
    return price;
  }
}
