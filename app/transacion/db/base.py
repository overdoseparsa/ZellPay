from abc import ABC , abstractmethod
from typing import (
    Dict,
    Any,
    Optional,
    Tuple
)
from uuid import UUID , uuid4
from logging import getLogger

from psycopg import IsolationLevel 
from psycopg.errors import IntegrityError
from psycopg.connection import  Connection

from uuid import UUID
import json

# from app.models.interface import RedisManager , PostgresDatabaseManager
from test11 import *


from abc import ABC, abstractmethod
from logging import getLogger
import psycopg
from psycopg.rows import dict_row , tuple_row

import redis
from contextlib import contextmanager
from psycopg_pool import ConnectionPool 

logger = getLogger(__name__)


class BaseConfig(ABC):
    """Base Config configuration management"""
    
    def __init__(self, host: str = '0.0.0.0', port: int = 6379, dbname: int | str = 0):
        self.host = host
        self.port = port
        self.dbname = dbname
class RedisConfig(BaseConfig):...

class DatabaseConfig(BaseConfig):
    """Database configuration management"""
    
    def __init__(self, 
                 dbname: str = 'zelpaymant', #  TODO  get  from  env 
                 user: str = 'ZELLIT', 
                 password: str = 'mohamadkhaki83@',
                 host: str = '0.0.0.0',
                 port: int = 5432,
                 min_connections: int = 1,
                 max_connections: int = 10):

        super().__init__(
            host,
            port,
            dbname
            ) 

        self.user = user
        self.password = password
        self.min_connections = min_connections
        self.max_connections = max_connections

class AbstractDatabaseManager(ABC):
    """ AbstractDatabaseManager for connections and operations """

    def __init__(self , config:DatabaseConfig):
        self.config = config 
        self._connection_pool = None
        assert hasattr(self,'_initialize_pool') , 'Must be implement _initialize_pool'
        self._initialize_pool()

    @abstractmethod
    def _initialize_pool(self):
        """
            Why did I do this? Because our logic and business logic may be different from code,
            so if I want to add another layer, we won't have an issue.
            We have respected dependency inversion.

            >>> self._connection_pool = ...      
        """
        raise NotImplementedError


class PostgresDatabaseManager(AbstractDatabaseManager):
    rows_factory = {
        'dict':dict_row , 
        'tuple':tuple_row
        
    }
    row_factory = ...
    isolation_level = ... 
    """Manages database connections and operations"""
    def __init__(self, config: DatabaseConfig):
        self.config = config
        self._initialize_pool()
    def _initialize_pool(self): # CRITICAL must be overload 
        """Initialize connection pool from postgres3

            Why use `wait()`?  
            If the configuration is incorrect or invalid, the pool will attempt to create connections.  
            Since the configuration is wrong, it will fail and eventually raise a timeout error.  
            Clients requesting a connection will also timeout while waiting for a valid connection. 
        """
        try:
            print("connection to the database with connection pool")
            conninfo = (
                f"dbname={self.config.dbname} "
                f"user={self.config.user} "
                f"password={self.config.password} "
                f"host={self.config.host} "
                f"port={self.config.port}"
            )
            self._connection_pool = ConnectionPool( 
                conninfo,
                min_size = self.config.min_connections,
                max_size = self.config.max_connections,
            )
            self._connection_pool.wait()
        
            logger.info("Database connection pool initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize database pool: {e}")
            raise
    @property
    def pool(self):
        return self._connection_pool
    
    def close(self)->None:
        self._connection_pool.close(
            timeout=3
        )
        
    @contextmanager
    def Connection(self ,
            isolation_level=psycopg.IsolationLevel.READ_COMMITTED,
            row_factory=None
            ):
        
        with self.pool.connection() as connection:

            if row_factory:
                assert row_factory in self.rows_factory, f"Invalid row factory: {row_factory}"
                connection.row_factory = self.rows_factory[row_factory]
                
            connection.set_isolation_level(isolation_level)
            
            try : 
                yield connection

            except Exception as e:

                logger.critical('Can Not Connect to the Database')
                connection.rollback()
                raise

            finally : 
                if connection:
                    connection.commit()



logger = getLogger(__name__)

class RedisManager:
    """Manages Redis connections and operations"""
    
    def __init__(self, config: RedisConfig): # TODO remove redis config 
        self.config = config
        self._redis_client = None
        self._initialize_client()
    
    def _initialize_client(self):
        """Initialize Redis client"""
        try:
            self._redis_client = redis.Redis( #TODO converrt to the async
                host=self.config.host,
                port=self.config.port,
                decode_responses=True
            )
            # Test connection
            self._redis_client.ping()
            logger.info("Redis client initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Redis client: {e}")
            raise
    
    @contextmanager
    def get_client(self): 
        """Get Redis client"""
        try:
            yield self._redis_client
        except Exception as e:
            logger.error(f"Redis operation failed: {e}")
            raise
        finally :
            if self._redis_client :
                self.close_client

    
    def close_client(self):
        """Close Redis client"""
        if self._redis_client:
            self._redis_client.close()
            logger.info("Redis client closed")

