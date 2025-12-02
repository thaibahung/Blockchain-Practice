// SPDX-License-Identifier: UNLICENSED
pragma solidity >=0.7.0; 

interface IUniswapV2Pair {
    function token0() external view returns (address); 
    function token1() external view returns (address); 
    function getReserves() external view returns (uint112 reserve0, uint112 reserve1, uint32 blockTimestampLast); 
    function swap(uint amount0Out, uint amount1Out, address to, bytes calldata data) external; 
}

library V2_core { 
    function getPairReserves(address pair) 
        internal view returns ( uint112 reserve0, uint112 reserve1, uint32 blockTimestampLast ) { 
            (reserve0, reserve1, blockTimestampLast) = IUniswapV2Pair(pair).getReserves(); 
        }
    
    function getAmountsOut(uint256 amountIn, bool zeroforone, address pair, uint256 fee) 
        internal view returns (uint256 amountOut) { 
            uint256 res0; 
            uint256 res1; 
            uint256 time; 
            (res0, res1, time) = getPairReserves(pair); 
            
            if (zeroforone == false) { 
                uint256 cur = res0; 
                res0 = res1; 
                res1 = cur; 
            } 
            
            require(amountIn > 0, "INSUFFICIENT_INPUT_AMOUNT"); 
            require(res0 > 0 && res1 > 0, "INSUFFICIENT_LIQUIDITY"); 
            
            uint amountInWithFee = amountIn * (10000 - fee); 
            uint numerator = amountInWithFee * res1; 
            uint denominator = res0 * 10000 + amountInWithFee; 
            
            amountOut = numerator / denominator; 
        }
    }