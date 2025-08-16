"""Smart contract ABIs and related functionality."""

import json
from typing import Dict, Any, Optional, Tuple
from web3 import Web3
from web3.contract import Contract
from logger import logger

from config import (
    ERC20_ABI,
)

class ContractManager:
    """Manages contract instances and interactions."""
    
    def __init__(self, web3: Web3):
        self.web3 = web3
        self._token_contracts: Dict[str, Contract] = {}
        self._pair_contracts: Dict[str, Contract] = {}
        self._router_contracts: Dict[str, Contract] = {}
        self._factory_contracts: Dict[str, Contract] = {}
        self._quoter_contracts: Dict[str, Contract] = {}
        self._vault_contracts: Dict[str, Contract] = {}

    def get_token_contract(self, token_address: str) -> Contract:
        """Get or create ERC20 token contract instance."""
        if token_address not in self._token_contracts:
            checksum_address = self.web3.to_checksum_address(token_address)
            self._token_contracts[token_address] = self.web3.eth.contract(
                address=checksum_address,
                abi=json.loads(ERC20_ABI)
            )
        return self._token_contracts[token_address]

    def get_router_contract(self, router_address: str, ABI: str) -> Contract:
        if not hasattr(self, '_router_contracts'):
            self._router_contracts = {}
        
        checksum_address = self.web3.to_checksum_address(router_address)
        if checksum_address not in self._router_contracts:
            self._router_contracts[checksum_address] = self.web3.eth.contract(
                address=checksum_address,
                abi=json.loads(ABI)
            )
        return self._router_contracts[checksum_address]

    def get_factory_contract(self, factory_address: str, ABI: str) -> Contract:
        """Get or create factory contract instance."""
        if not hasattr(self, '_factory_contracts'):
            self._factory_contracts = {}
        
        checksum_address = self.web3.to_checksum_address(factory_address)
        if checksum_address not in self._factory_contracts:
            self._factory_contracts[checksum_address] = self.web3.eth.contract(
                address=checksum_address,
                abi=json.loads(ABI)
            )
        return self._factory_contracts[checksum_address]

    def get_pair_contract(self, pair_address: str, ABI: str) -> Contract:
        """Get or create pair contract instance."""
        if pair_address not in self._pair_contracts:
            checksum_address = self.web3.to_checksum_address(pair_address)
            self._pair_contracts[pair_address] = self.web3.eth.contract(
                address=checksum_address,
                abi=json.loads(ABI)
            )
        return self._pair_contracts[pair_address]
    
    def get_quoter_contract(self, quoter_address: str, ABI: str) -> Contract:
        """Get or create quoter contract instance."""
        if not hasattr(self, '_quoter_contracts'):
            self._quoter_contracts = {}
        
        checksum_address = self.web3.to_checksum_address(quoter_address)
        if checksum_address not in self._quoter_contracts:
            self._quoter_contracts[checksum_address] = self.web3.eth.contract(
                address=checksum_address,
                abi=json.loads(ABI)
            )
        return self._quoter_contracts[checksum_address]
    
    def get_vault_contract(self, vault_address: str, ABI: str) -> Contract:
        """Get or create vault contract instance."""
        if not hasattr(self, '_vault_contracts'):
            self._vault_contracts = {}
        
        checksum_address = self.web3.to_checksum_address(vault_address)
        if checksum_address not in self._vault_contracts:
            self._vault_contracts[checksum_address] = self.web3.eth.contract(
                address=checksum_address,
                abi=json.loads(ABI)
            )
        return self._vault_contracts[checksum_address]

    def decode_tx_router(self, input_data: str, router_address: str, ABI: str) -> tuple[str, dict]:
        """Decode transaction input data for a given router."""
        try:
            contract = self.get_router_contract(router_address, ABI)
            func_obj, params = contract.decode_function_input(input_data)
            return func_obj.fn_name, params
        except Exception as e:
            logger.exception(f"Error decoding transaction for router {router_address}: {e}")
            return "", {}

    def decode_tx_vault(self, input_data: str, vault_address: str, ABI: str) -> tuple[str, dict]:
        """Decode transaction input data for a given vault."""
        try:
            contract = self.get_vault_contract(vault_address, ABI)
            func_obj, params = contract.decode_function_input(input_data)
            return func_obj.fn_name, params
        except Exception as e:
            logger.exception(f"Error decoding transaction for vault {vault_address}: {e}")
            return "", {}