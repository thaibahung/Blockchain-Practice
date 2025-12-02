// SPDX-License-Identifier: UNLICENSED
pragma solidity >=0.7.0;

import "./V2_core.sol";
import "./V3_core.sol";
import "@openzeppelin/contracts/security/ReentrancyGuard.sol";

interface IV2PairLike {
    function token0() external view returns (address);
    function token1() external view returns (address);
}

// Pool version enumeration 
enum PoolVersion { 
    UniswapV2, 
    UniswapV3, 
    SushiSwapV2, 
    PancakeSwapV2, 
    SushiSwapV3, 
    PancakeSwapV3 
}

struct Edge { 
    address pool; 
    uint256 fee; 
    PoolVersion version; 
} 

struct Cycle_3 { 
    address token1; 
    address token2; 
    address token3; 
    Edge edge1; 
    Edge edge2; 
    Edge edge3; 
} 

struct Cycle_2 { 
    address token1; 
    address token2; 
    address edge1; 
    address edge2; 
}

contract OptiArb is ReentrancyGuard {
    function _zeroForOne(address pool, address tokenIn) internal view returns (bool) {
        return tokenIn == IV2PairLike(pool).token0();
    }

    function _getAmountOutByVersion(uint256 amountIn, bool z, Edge calldata e) 
        internal view returns (uint256) {

        // ---- V2 Versions ----
        if (
            e.version == PoolVersion.UniswapV2 ||
            e.version == PoolVersion.SushiSwapV2 ||
            e.version == PoolVersion.PancakeSwapV2
        ) {
            return V2_core.getAmountsOut(amountIn, z, e.pool, e.fee);
        }

        // ---- V3 Versions ----
        if (
            e.version == PoolVersion.UniswapV3 ||
            e.version == PoolVersion.SushiSwapV3 ||
            e.version == PoolVersion.PancakeSwapV3
        ) {
            return V3_core.getAmountsOut(amountIn, z, e.pool, e.fee);
        }

        // Should never happen
        revert("Unsupported pool version");
    }

    function checkProfit(uint256 amountIn, Cycle_3 calldata c)
        external
        view
        returns (uint256 profit)
    {
        uint256 cur = amountIn;

        // Step 1
        cur = _getAmountOutByVersion(
            cur,
            _zeroForOne(c.edge1.pool, c.token1),
            c.edge1
        );

        // Step 2
        cur = _getAmountOutByVersion(
            cur,
            _zeroForOne(c.edge2.pool, c.token2),
            c.edge2
        );

        // Step 3
        cur = _getAmountOutByVersion(
            cur,
            _zeroForOne(c.edge3.pool, c.token3),
            c.edge3
        );

        // Profit
        profit = cur > amountIn ? cur - amountIn : 0;
    }

    // Batch variant
    function checkProfits(uint256 amountIn, Cycle_3[] calldata cycles)
        external view
        returns (uint256[] memory profits)
    {
        profits = new uint256[](cycles.length);
        for (uint i=0;i<cycles.length;i++) {
            profits[i] = this.checkProfit(amountIn, cycles[i]);
        }
    }
}