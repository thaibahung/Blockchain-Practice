// SPDX-License-Identifier: UNLICENSED
pragma solidity >=0.7.0;

import "https://raw.githubusercontent.com/Uniswap/v3-core/v1.0.0/contracts/interfaces/IUniswapV3Pool.sol";
import "https://raw.githubusercontent.com/Uniswap/v3-core/v1.0.0/contracts/libraries/SwapMath.sol";
import "https://raw.githubusercontent.com/Uniswap/v3-core/v1.0.0/contracts/libraries/TickMath.sol";
import "https://raw.githubusercontent.com/Uniswap/v3-core/v1.0.0/contracts/libraries/LowGasSafeMath.sol";

library V3Core {
    using LowGasSafeMath for uint256;

    function getAmountsOut(uint256 amountIn, bool zeroForOne, address poolAddress, uint24 fee)
        internal view returns (uint256 amountOut) {
            
            IUniswapV3Pool pool = IUniswapV3Pool(poolAddress);

            // Load slot0 state
            (uint160 sqrtPriceX96, int24 tick,,,,,) = pool.slot0();
            uint128 liquidity = pool.liquidity();

            uint256 remainingIn = amountIn;

            while (remainingIn > 0) {

                int24 tickSpacing = pool.tickSpacing();

                // Find next initialized tick
                (int24 nextTick, bool initialized) = _nextInitializedTickWithinOneWord(pool, tick, tickSpacing, zeroForOne);

                uint160 sqrtPriceNextX96 = TickMath.getSqrtRatioAtTick(nextTick);

                (
                    uint160 sqrtPriceAfterX96,
                    uint256 usedAmount,
                    uint256 receivedOut,
                    uint256 feeAmount
                ) = SwapMath.computeSwapStep(
                    sqrtPriceX96,
                    sqrtPriceNextX96,
                    liquidity,
                    int256(remainingIn),
                    fee
                );

                remainingIn = remainingIn.sub(usedAmount.add(feeAmount));
                amountOut = amountOut.add(receivedOut);
                sqrtPriceX96 = sqrtPriceAfterX96;

                // If swap reaches next tick price → cross the tick
                if (sqrtPriceAfterX96 == sqrtPriceNextX96) {

                    (, int128 liquidityNet, , , , , , ) = pool.ticks(nextTick);

                    if (zeroForOne) {
                        if (liquidityNet < 0) {
                            liquidity -= uint128(-liquidityNet);
                        } else {
                            liquidity += uint128(liquidityNet);
                        }
                    } else {
                        if (liquidityNet > 0) {
                            liquidity += uint128(liquidityNet);
                        } else {
                            liquidity -= uint128(-liquidityNet);
                        }
                    }

                    tick = zeroForOne ? nextTick - 1 : nextTick;

                } else {
                    // Swap completed before reaching next tick → exit loop
                    break;
                }
        }

        return amountOut;
    }

    /* ───────────────────────────────────────────────────────────────
          REAL TICKBITMAP IMPLEMENTATION (STANDALONE & CORRECT)
       ─────────────────────────────────────────────────────────────── */

    function _nextInitializedTickWithinOneWord(
        IUniswapV3Pool pool,
        int24 tick,
        int24 tickSpacing,
        bool lte
    )
        internal
        view
        returns (int24 next, bool initialized)
    {
        int24 compressed = tick / tickSpacing;
        if (tick < 0 && tick % tickSpacing != 0) compressed--;

        int16 wordPos = int16(compressed >> 8);
        uint8 bitPos = uint8(uint256(int256(compressed & 0xFF)));

        uint256 word = pool.tickBitmap(wordPos);

        if (lte) {
            uint256 mask = (uint256(1) << bitPos) - 1 | (uint256(1) << bitPos);
            uint256 masked = word & mask;

            if (masked != 0) {
                uint8 msb = _mostSignificantBit(masked);
                int24 nextCompressed = int24(msb) + int24(wordPos) * 256;
                next = nextCompressed * tickSpacing;
                initialized = true;
            } else {
                next = (int24(wordPos) * 256 - 1) * tickSpacing;
                initialized = false;
            }
        } else {
            uint256 mask = ~((uint256(1) << bitPos) - 1);
            uint256 masked = word & mask;

            if (masked != 0) {
                uint8 lsb = _leastSignificantBit(masked);
                int24 nextCompressed = int24(lsb) + int24(wordPos) * 256;
                next = nextCompressed * tickSpacing;
                initialized = true;
            } else {
                next = (int24(wordPos + 1) * 256) * tickSpacing;
                initialized = false;
            }
        }
    }

    /* ───────────────────────────────────────────────────────────────
                         BIT OPERATIONS (LSB/MSB)
       ─────────────────────────────────────────────────────────────── */

    function _leastSignificantBit(uint256 x) internal pure returns (uint8 r) {
        require(x > 0, "lsb-zero");
        r = 0;
        while ((x & 1) == 0) {
            x >>= 1;
            r++;
        }
    }

    function _mostSignificantBit(uint256 x) internal pure returns (uint8 r) {
        require(x > 0, "msb-zero");
        uint8 msb = 0;
        while (x > 1) {
            x >>= 1;
            msb++;
        }
        return msb;
    }
}
