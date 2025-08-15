from typing import Dict, Optional, Any, Tuple
from decimal import Decimal
import math
from logger import logger

from infrastructure.data_providers.pools.v2_pool import V2Pool
from domain.entities.pool_models import IPool



class PoolSimulatorManager:
    def __init__(self):
        self.pool_simulators: dict[str, IPool] = {}
        self.v2_pool_address_cache: dict[str, str] = {}
    
    def clear(self) -> None:
        self.pool_simulators.clear()
        self.v2_pool_address_cache.clear()
    
    def _create_pool_by_tokens_cache_key(self, token0: str, token1: str, fee: int, provider: str) -> str:
        """
        Sort token addresses to ensure consistent ordering.
        
        Args:
            token0: First token address
            token1: Second token address
            
        Returns:
            Tuple of sorted token addresses (lowercase)
        """
        tokens = [token0.lower(), token1.lower()]
        tokens.sort()
        return f'{tokens[0]}_{tokens[1]}_{fee}_{provider}'
    

    def get_v2_pool_address(self, token0: str, token1: str, provider: str) -> Optional[str]:
        """
        Get V2 pool address from cache or compute it.
        
        Args:
            token0: First token address
            token1: Second token address
            
        Returns:
            Pool address if found, None otherwise
        """
        # Create cache key for V2 pools
        cache_key = self._create_pool_by_tokens_cache_key(token0, token1, 0, provider)
        
        # Check cache first
        if cache_key in self.v2_pool_address_cache:
            return self.v2_pool_address_cache[cache_key]
            
        # Not in cache - we'll return None
        # Repository calls are handled in the transaction handlers
        return None
    
    def get_simulator(self, pool_address: str) -> Optional[IPool]:
        """
        Get a pool simulator by address.
        
        Args:
            pool_address: Pool address
            
        Returns:
            Pool simulator if found, None otherwise
        """
        return self.pool_simulators.get(pool_address)


    async def create_and_store_v2_pool_simulator(
        self, pool_address: str, token0: str, token1: str, 
        decimals0: int, decimals1: int, reserve0: Decimal, reserve1: Decimal, fee_tier: int, block_number: int, provider_name: str = 'uniswap_v2'
    ) -> None:
        """
        Create and store a pool simulator for a V2 pool.
        
        Args:
            pool_address: Pool address
            token0: Token0 address
            token1: Token1 address
            decimals0: Token0 decimals
            decimals1: Token1 decimals
            reserve0: Reserve of token0
            reserve1: Reserve of token1
        """
        try:
            # Create V2Pool - convert Decimal reserves to int (wei units)
            pool_simulator = V2Pool(
                address=pool_address,
                token0=token0,
                token1=token1,
                reserve0=int(reserve0 * (10 ** decimals0)),  # Convert to wei
                reserve1=int(reserve1 * (10 ** decimals1)),  # Convert to wei
                fee=fee_tier/1000000.0,  #Convert fee tier from basis points to decimal
                decimals0=decimals0,
                decimals1=decimals1,
                protocol=provider_name  # Adding protocol identifier
            )
            
            # Store pool simulator
            self.pool_simulators[pool_address] = pool_simulator
            address_cache_key = self._create_pool_by_tokens_cache_key(token0, token1, 0, provider_name)
            self.v2_pool_address_cache[address_cache_key] = pool_address
            
            # Log pool creation to Redis
            redis_pool_logger.log_pool_creation(pool_simulator, block_number)
            
            logger.debug(f"Created V2 pool simulator for {pool_address}")
        except Exception as e:
            logger.exception(f"Error creating V2 pool simulator for {pool_address}")