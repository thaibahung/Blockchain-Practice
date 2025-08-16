"""Arbitrum Blockchain Provider"""

from typing import Any, List, Dict, Optional
from web3 import Web3
from web3.contract import Contract
from contracts import ContractManager
from cachetools import TTLCache

from domain.interfaces.blockchain_provider import IBlockchainProvider


class ArbitrumBlockchainProvider(IBlockchainProvider):
    """Provides data and functionality specific to the Arbitrum blockchain."""

    def __init__(self, web3: Web3, contract_manager: ContractManager):
        self.web3 = web3
        self.contract_manager = contract_manager

        # Transaction cache with 5-minute TTL (300 seconds)
        self.tx_cache = TTLCache(maxsize=10000, ttl=300)
        
        # Locks for transaction requests to prevent concurrent requests for the same tx
        self.tx_locks = {}
        
        # Store for handled events to handle reorgs
        # Maps log event identifiers to event details
        self.handled_events = {}

    @property
    def blockchain(self) -> str:
        return "arbitrum"
    
    async def call_contract_function(
        self, contract: Contract, 
        function_name: str, *args, **kwargs
    ) -> Any:
        pass


    async def multicall(
        self, calls: List[Dict[str, Any]], block_id: Optional[int] = None
    ) -> Dict[str, Any]:
        pass


    def to_checksum_address(self, address: str) -> str:
        """
        Convert an address to checksum format.
        
        Args:
            address: The address to convert
            
        Returns:
            The checksum address
        """
        return Web3.to_checksum_address(address)
    