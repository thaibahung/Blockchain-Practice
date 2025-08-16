from abc import ABC, abstractmethod
from decimal import Decimal
from typing import Any, Dict, List, Optional, Callable, TypeVar, Generic, Set, Tuple
from web3.contract.contract import Contract

from domain.entities.models import Transaction, PoolEvent

T = TypeVar('T')

class IBlockchainProvider(ABC):
    """Interface for blockchain providers."""
    
    @property
    @abstractmethod
    def blockchain(self) -> str:
        """Get the blockchain (e.g., 'ethereum', 'bsc')."""
        pass
    
    @abstractmethod
    async def call_contract_function(
        self, contract: Contract, 
        function_name: str, *args, **kwargs
    ) -> Any:
        """
        Call a contract function.
        
        Args:
            contract: The contract instance
            function_name: The function name
            *args: Function arguments
            **kwargs: Function keyword arguments
            
        Returns:
            The function result
        """
        pass
    
    @abstractmethod
    async def multicall(
        self, calls: List[Dict[str, Any]], block_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Execute multiple contract calls in a single transaction.
        
        Args:
            calls: List of call specifications
            
        Returns:
            Dictionary of results
        """
        pass
    
    @abstractmethod
    def to_checksum_address(self, address: str) -> str:
        """
        Convert an address to checksum format.
        
        Args:
            address: The address to convert
            
        Returns:
            The checksum address
        """
        pass

    '''
    @abstractmethod
    def get_latest_block_number(self) -> int:
        """
        Get the latest block number.
        
        Returns:
            Latest block number
        """
        pass
    
    
    @abstractmethod
    async def get_transaction(self, tx_hash: str) -> Optional[Transaction]:
        """
        Get transaction details by hash.
        
        Args:
            tx_hash: Transaction hash
            
        Returns:
            Transaction object if found, None otherwise
        """
        pass
    
        
    @abstractmethod
    async def estimate_gas_fee(self) -> Optional[Tuple[float, float, float]]:
        """
        Get current gas price estimates.
        
        Returns:
            Optional[Tuple[float, float, float]]: (base_fee_gwei, priority_fee_gwei, max_fee_gwei) or None if error
        """
        pass
    '''    
    