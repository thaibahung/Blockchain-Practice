"""Redis logger for pool events and states."""

import json
import time
from typing import Any, Dict, Optional, List, Union
import redis
from decimal import Decimal

from config import REDIS_HOST, REDIS_LOGGING_ENABLED, REDIS_PASSWORD, REDIS_POOL_LOGS_PREFIX, REDIS_PORT
from domain.entities.models import PoolEvent
from domain.entities.pool_models import IPool
from infrastructure.data_providers.pools.v2_pool import V2Pool

from logger import logger

# Custom JSON encoder to handle Decimal and other custom types
class CustomJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Decimal):
            return str(obj)
        return super().default(obj)
    

class RedisPoolLogger:
    """Redis logger for pool events and states."""
    
    def __init__(self):
        """
        Initialize the Redis logger.
        Uses REDIS_LOGGING_ENABLED config to determine if logging is enabled.
        """
        self.enabled = REDIS_LOGGING_ENABLED
        if not self.enabled:
            logger.info("Redis logging is disabled")
            self.redis = None
            return
            
        try:
            self.redis = redis.Redis(
                host=REDIS_HOST,
                port=REDIS_PORT,
                password=REDIS_PASSWORD,
                decode_responses=True
            )
            # Test connection
            self.redis.ping()
            logger.info(f"Connected to Redis at {REDIS_HOST}:{REDIS_PORT}")
        except redis.ConnectionError as e:
            logger.error(f"Failed to connect to Redis: {e}")
            self.redis = None
    
    def _get_pool_key(self, pool_address: str) -> str:
        """
        Get the Redis key for a pool.
        
        Args:
            pool_address: Pool address
            
        Returns:
            Redis key for the pool
        """
        return f"{REDIS_POOL_LOGS_PREFIX}{pool_address.lower()}"

    def _serialize_event(self, event: PoolEvent) -> Dict[str, Any]:
        """
        Serialize a pool event.
        
        Args:
            event: Pool event
            
        Returns:
            Serialized event data
        """
        # Convert event to dict
        event_dict = {k: v for k, v in event.__dict__.items()}
        
        # Add event type info
        event_dict['pool_type'] = getattr(event, 'pool_type', None)
        
        return event_dict
    
    
    def _serialize_pool_state(self, pool: IPool) -> Dict[str, Any]:
        """
        Serialize the state of a pool.
        
        Args:
            pool: Pool instance
            
        Returns:
            Serialized pool state
        """
        # Common pool properties
        pool_state = {
            'address': pool.address,
            'token0': pool.token0,
            'token1': pool.token1,
            'fee': pool.fee,
            'price': str(pool.get_price()),
        }
        
        # V2Pool specific properties
        if isinstance(pool, V2Pool):
            pool_state.update({
                'pool_type': 'v2',
                'reserve0': str(pool.reserve0),
                'reserve1': str(pool.reserve1),
                'price0': str(pool.price0),
                'price1': str(pool.price1),
                'decimals0': pool._decimals0,
                'decimals1': pool._decimals1,
            })

        return pool_state
    
    
    def log_pool_creation(self, pool: IPool, block_number: int) -> bool:
        """
        Log pool creation to Redis.
        
        Args:
            pool: Pool instance
            block_number: Block number at which the pool was created
            
        Returns:
            True if logging was successful, False otherwise
        """
        if not self.enabled:
            return True
            
        if not self.redis:
            logger.warning("Redis connection not available for pool creation logging")
            return False
        
        try:
            pool_address = pool.address
            pool_key = self._get_pool_key(pool_address)
            timestamp = time.time()
            
            # Create log data
            log_data = {
                'event_type': 'pool_creation',
                'block_number': block_number,
                'timestamp': timestamp,
                'pool_state': self._serialize_pool_state(pool)
            }
            
            # Serialize to JSON
            log_json = json.dumps(log_data, cls=CustomJSONEncoder)
            
            # Add to sorted set with timestamp as score
            self.redis.zadd(pool_key, {log_json: timestamp})
            logger.debug(f"Logged pool creation for {pool_address}")
            return True
            
        except Exception as e:
            logger.error(f"Error logging pool creation: {e}")
            return False
        
        
    def log_pool_update(self, pool: IPool, event: PoolEvent) -> bool:
        """
        Log pool update to Redis.
        
        Args:
            pool: Pool instance after update
            event: Pool event that triggered the update
            
        Returns:
            True if logging was successful, False otherwise
        """
        if not self.enabled:
            return True
            
        if not self.redis:
            logger.warning("Redis connection not available for pool update logging")
            return False
        
        try:
            pool_address = pool.address
            pool_key = self._get_pool_key(pool_address)
            timestamp = time.time()
            
            # Create log data
            log_data = {
                'event_type': 'pool_update',
                'block_number': event.block_number,
                'timestamp': timestamp,
                'transaction_hash': event.transaction_hash,
                'log_index': event.log_index,
                'event': self._serialize_event(event),
                'is_reorg': event.is_reorg,
                'pool_state': self._serialize_pool_state(pool)
            }
            
            # Serialize to JSON
            log_json = json.dumps(log_data, cls=CustomJSONEncoder)
            
            # Add to sorted set with timestamp as score
            self.redis.zadd(pool_key, {log_json: timestamp})
            logger.debug(f"Logged pool update for {pool_address}")
            return True
            
        except Exception as e:
            logger.error(f"Error logging pool update: {e}")
            return False
    
    def get_pool_logs(self, pool_address: str, count: int = 10) -> List[Dict[str, Any]]:
        """
        Get the most recent logs for a pool.
        
        Args:
            pool_address: Pool address
            count: Number of logs to retrieve
            
        Returns:
            List of pool logs
        """
        if not self.enabled or not self.redis:
            logger.warning("Redis logging is disabled or connection not available for retrieving pool logs")
            return []
        
        try:
            pool_key = self._get_pool_key(pool_address)
            
            # Get logs from sorted set (newest first)
            logs_json = self.redis.zrevrange(pool_key, 0, count - 1)
            
            # Parse JSON
            logs = [json.loads(log_json) for log_json in logs_json]
            return logs
            
        except Exception as e:
            logger.error(f"Error retrieving pool logs: {e}")
            return []
    
    def get_pool_logs_by_time_range(self, pool_address: str, start_time: float, end_time: float) -> List[Dict[str, Any]]:
        """
        Get logs for a pool within a specific time range.
        
        Args:
            pool_address: Pool address
            start_time: Start time (unix timestamp)
            end_time: End time (unix timestamp)
            
        Returns:
            List of pool logs within the time range
        """
        if not self.enabled or not self.redis:
            logger.warning("Redis logging is disabled or connection not available for retrieving pool logs")
            return []
        
        try:
            pool_key = self._get_pool_key(pool_address)
            
            # Get logs from sorted set within the time range
            logs_json = self.redis.zrangebyscore(pool_key, start_time, end_time)
            
            # Parse JSON
            logs = [json.loads(log_json) for log_json in logs_json]
            return logs
            
        except Exception as e:
            logger.error(f"Error retrieving pool logs by time range: {e}")
            return []

    def is_enabled(self) -> bool:
        """
        Check if Redis logging is enabled and connected.
        
        Returns:
            True if Redis logging is enabled and connected, False otherwise
        """
        return self.enabled and self.redis is not None
    
    def set_enabled(self, enabled: bool) -> None:
        """
        Enable or disable Redis logging.
        
        Args:
            enabled: Whether to enable Redis logging
        """
        # If enabling and was previously disabled, try to connect
        if enabled and not self.enabled:
            self.enabled = True
            self.__init__()
        else:
            self.enabled = enabled
            if not enabled:
                logger.info("Redis logging has been disabled")

# Singleton instance
# Uses the config setting for whether Redis logging is enabled
redis_pool_logger = RedisPoolLogger()