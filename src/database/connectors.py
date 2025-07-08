import pandas as pd
import sqlalchemy
from sqlalchemy import create_engine, text, inspect
import pymysql
import psycopg2
from typing import Dict, Any, List, Optional, Union
from abc import ABC, abstractmethod
import structlog
from pathlib import Path

from ..models.validation import DataSourceConfig, DataSourceType, ColumnInfo
from ..config.settings import settings

logger = structlog.get_logger()

class DatabaseConnector(ABC):
    """Abstract base class for database connections"""
    
    @abstractmethod
    def connect(self) -> bool:
        """Establish connection to the database"""
        pass
    
    @abstractmethod
    def get_tables(self) -> List[str]:
        """Get list of available tables"""
        pass
    
    @abstractmethod
    def get_columns(self, table_name: str) -> List[ColumnInfo]:
        """Get column information for a table"""
        pass
    
    @abstractmethod
    def get_sample_data(self, table_name: str, limit: int = 100) -> pd.DataFrame:
        """Get sample data from table"""
        pass
    
    @abstractmethod
    def execute_query(self, query: str) -> pd.DataFrame:
        """Execute SQL query and return results"""
        pass
    
    @abstractmethod
    def get_data_profile(self, table_name: str, column_name: str) -> Dict[str, Any]:
        """Get data profile statistics for a column"""
        pass

class PostgreSQLConnector(DatabaseConnector):
    """PostgreSQL database connector"""
    
    def __init__(self, config: DataSourceConfig):
        self.config = config
        self.engine = None
        self.connection_string = self._build_connection_string()
    
    def _build_connection_string(self) -> str:
        """Build PostgreSQL connection string"""
        params = self.config.connection_params
        host = params.get('host', settings.POSTGRES_HOST)
        port = params.get('port', settings.POSTGRES_PORT)
        database = params.get('database', settings.POSTGRES_DB)
        username = params.get('username', settings.POSTGRES_USER)
        password = params.get('password', settings.POSTGRES_PASSWORD)
        
        return f"postgresql://{username}:{password}@{host}:{port}/{database}"
    
    def connect(self) -> bool:
        """Establish PostgreSQL connection"""
        try:
            self.engine = create_engine(self.connection_string)
            # Test connection
            with self.engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            logger.info("PostgreSQL connection established successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to PostgreSQL: {str(e)}")
            return False
    
    def get_tables(self) -> List[str]:
        """Get list of PostgreSQL tables"""
        try:
            inspector = inspect(self.engine)
            tables = inspector.get_table_names()
            return tables
        except Exception as e:
            logger.error(f"Failed to get tables: {str(e)}")
            return []
    
    def get_columns(self, table_name: str) -> List[ColumnInfo]:
        """Get PostgreSQL column information"""
        try:
            inspector = inspect(self.engine)
            columns = inspector.get_columns(table_name)
            
            column_infos = []
            for col in columns:
                # Get additional statistics
                stats = self.get_data_profile(table_name, col['name'])
                
                column_info = ColumnInfo(
                    name=col['name'],
                    data_type=str(col['type']),
                    nullable=col['nullable'],
                    unique_count=stats.get('unique_count'),
                    null_count=stats.get('null_count'),
                    min_value=stats.get('min_value'),
                    max_value=stats.get('max_value'),
                    sample_values=stats.get('sample_values', [])
                )
                column_infos.append(column_info)
            
            return column_infos
        except Exception as e:
            logger.error(f"Failed to get columns for table {table_name}: {str(e)}")
            return []
    
    def get_sample_data(self, table_name: str, limit: int = 100) -> pd.DataFrame:
        """Get sample data from PostgreSQL table"""
        try:
            query = f"SELECT * FROM {table_name} LIMIT {limit}"
            return pd.read_sql_query(query, self.engine)
        except Exception as e:
            logger.error(f"Failed to get sample data: {str(e)}")
            return pd.DataFrame()
    
    def execute_query(self, query: str) -> pd.DataFrame:
        """Execute PostgreSQL query"""
        try:
            return pd.read_sql_query(query, self.engine)
        except Exception as e:
            logger.error(f"Query execution failed: {str(e)}")
            raise
    
    def get_data_profile(self, table_name: str, column_name: str) -> Dict[str, Any]:
        """Get PostgreSQL column statistics"""
        try:
            # Get basic statistics
            stats_query = f"""
            SELECT 
                COUNT(*) as total_count,
                COUNT(DISTINCT {column_name}) as unique_count,
                COUNT(*) - COUNT({column_name}) as null_count,
                MIN({column_name}) as min_value,
                MAX({column_name}) as max_value
            FROM {table_name}
            """
            
            stats_df = pd.read_sql_query(stats_query, self.engine)
            stats = stats_df.iloc[0].to_dict()
            
            # Get sample values
            sample_query = f"""
            SELECT DISTINCT {column_name} 
            FROM {table_name} 
            WHERE {column_name} IS NOT NULL 
            LIMIT 10
            """
            sample_df = pd.read_sql_query(sample_query, self.engine)
            stats['sample_values'] = sample_df[column_name].tolist()
            
            return stats
        except Exception as e:
            logger.error(f"Failed to get data profile: {str(e)}")
            return {}

class MySQLConnector(DatabaseConnector):
    """MySQL database connector"""
    
    def __init__(self, config: DataSourceConfig):
        self.config = config
        self.engine = None
        self.connection_string = self._build_connection_string()
    
    def _build_connection_string(self) -> str:
        """Build MySQL connection string"""
        params = self.config.connection_params
        host = params.get('host', settings.MYSQL_HOST)
        port = params.get('port', settings.MYSQL_PORT)
        database = params.get('database', settings.MYSQL_DB)
        username = params.get('username', settings.MYSQL_USER)
        password = params.get('password', settings.MYSQL_PASSWORD)
        
        return f"mysql+pymysql://{username}:{password}@{host}:{port}/{database}"
    
    def connect(self) -> bool:
        """Establish MySQL connection"""
        try:
            self.engine = create_engine(self.connection_string)
            # Test connection
            with self.engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            logger.info("MySQL connection established successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to MySQL: {str(e)}")
            return False
    
    def get_tables(self) -> List[str]:
        """Get list of MySQL tables"""
        try:
            inspector = inspect(self.engine)
            tables = inspector.get_table_names()
            return tables
        except Exception as e:
            logger.error(f"Failed to get tables: {str(e)}")
            return []
    
    def get_columns(self, table_name: str) -> List[ColumnInfo]:
        """Get MySQL column information"""
        try:
            inspector = inspect(self.engine)
            columns = inspector.get_columns(table_name)
            
            column_infos = []
            for col in columns:
                # Get additional statistics
                stats = self.get_data_profile(table_name, col['name'])
                
                column_info = ColumnInfo(
                    name=col['name'],
                    data_type=str(col['type']),
                    nullable=col['nullable'],
                    unique_count=stats.get('unique_count'),
                    null_count=stats.get('null_count'),
                    min_value=stats.get('min_value'),
                    max_value=stats.get('max_value'),
                    sample_values=stats.get('sample_values', [])
                )
                column_infos.append(column_info)
            
            return column_infos
        except Exception as e:
            logger.error(f"Failed to get columns for table {table_name}: {str(e)}")
            return []
    
    def get_sample_data(self, table_name: str, limit: int = 100) -> pd.DataFrame:
        """Get sample data from MySQL table"""
        try:
            query = f"SELECT * FROM {table_name} LIMIT {limit}"
            return pd.read_sql_query(query, self.engine)
        except Exception as e:
            logger.error(f"Failed to get sample data: {str(e)}")
            return pd.DataFrame()
    
    def execute_query(self, query: str) -> pd.DataFrame:
        """Execute MySQL query"""
        try:
            return pd.read_sql_query(query, self.engine)
        except Exception as e:
            logger.error(f"Query execution failed: {str(e)}")
            raise
    
    def get_data_profile(self, table_name: str, column_name: str) -> Dict[str, Any]:
        """Get MySQL column statistics"""
        try:
            # Get basic statistics
            stats_query = f"""
            SELECT 
                COUNT(*) as total_count,
                COUNT(DISTINCT {column_name}) as unique_count,
                COUNT(*) - COUNT({column_name}) as null_count,
                MIN({column_name}) as min_value,
                MAX({column_name}) as max_value
            FROM {table_name}
            """
            
            stats_df = pd.read_sql_query(stats_query, self.engine)
            stats = stats_df.iloc[0].to_dict()
            
            # Get sample values
            sample_query = f"""
            SELECT DISTINCT {column_name} 
            FROM {table_name} 
            WHERE {column_name} IS NOT NULL 
            LIMIT 10
            """
            sample_df = pd.read_sql_query(sample_query, self.engine)
            stats['sample_values'] = sample_df[column_name].tolist()
            
            return stats
        except Exception as e:
            logger.error(f"Failed to get data profile: {str(e)}")
            return {}

class CSVConnector(DatabaseConnector):
    """CSV file connector"""
    
    def __init__(self, config: DataSourceConfig):
        self.config = config
        self.file_path = config.file_path
        self.df = None
    
    def connect(self) -> bool:
        """Load CSV file"""
        try:
            if not self.file_path or not Path(self.file_path).exists():
                logger.error(f"CSV file not found: {self.file_path}")
                return False
            
            self.df = pd.read_csv(self.file_path)
            logger.info(f"CSV file loaded successfully: {self.file_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to load CSV file: {str(e)}")
            return False
    
    def get_tables(self) -> List[str]:
        """For CSV, return the filename as table name"""
        if self.file_path:
            return [Path(self.file_path).stem]
        return []
    
    def get_columns(self, table_name: str = None) -> List[ColumnInfo]:
        """Get CSV column information"""
        if self.df is None:
            return []
        
        try:
            column_infos = []
            for col_name in self.df.columns:
                col_data = self.df[col_name]
                
                # Determine data type
                if pd.api.types.is_numeric_dtype(col_data):
                    data_type = "numeric"
                elif pd.api.types.is_datetime64_any_dtype(col_data):
                    data_type = "datetime"
                else:
                    data_type = "text"
                
                column_info = ColumnInfo(
                    name=col_name,
                    data_type=data_type,
                    nullable=col_data.isnull().any(),
                    unique_count=col_data.nunique(),
                    null_count=col_data.isnull().sum(),
                    min_value=col_data.min() if pd.api.types.is_numeric_dtype(col_data) else None,
                    max_value=col_data.max() if pd.api.types.is_numeric_dtype(col_data) else None,
                    sample_values=col_data.dropna().unique()[:10].tolist()
                )
                column_infos.append(column_info)
            
            return column_infos
        except Exception as e:
            logger.error(f"Failed to get CSV columns: {str(e)}")
            return []
    
    def get_sample_data(self, table_name: str = None, limit: int = 100) -> pd.DataFrame:
        """Get sample data from CSV"""
        if self.df is None:
            return pd.DataFrame()
        
        return self.df.head(limit)
    
    def execute_query(self, query: str) -> pd.DataFrame:
        """Execute query on CSV (limited SQL support via pandas)"""
        # For CSV, we'll implement basic filtering
        # This is a simplified implementation
        if self.df is None:
            return pd.DataFrame()
        
        # This would need more sophisticated query parsing
        # For now, return the entire dataframe
        return self.df
    
    def get_data_profile(self, table_name: str, column_name: str) -> Dict[str, Any]:
        """Get CSV column statistics"""
        if self.df is None or column_name not in self.df.columns:
            return {}
        
        try:
            col_data = self.df[column_name]
            
            stats = {
                'total_count': len(col_data),
                'unique_count': col_data.nunique(),
                'null_count': col_data.isnull().sum(),
                'sample_values': col_data.dropna().unique()[:10].tolist()
            }
            
            if pd.api.types.is_numeric_dtype(col_data):
                stats['min_value'] = col_data.min()
                stats['max_value'] = col_data.max()
            
            return stats
        except Exception as e:
            logger.error(f"Failed to get CSV data profile: {str(e)}")
            return {}

class DatabaseManager:
    """Factory class for managing database connections"""
    
    @staticmethod
    def create_connector(config: DataSourceConfig) -> DatabaseConnector:
        """Create appropriate database connector based on config"""
        
        if config.type == DataSourceType.POSTGRESQL:
            return PostgreSQLConnector(config)
        elif config.type == DataSourceType.MYSQL:
            return MySQLConnector(config)
        elif config.type == DataSourceType.CSV:
            return CSVConnector(config)
        else:
            raise ValueError(f"Unsupported data source type: {config.type}")
    
    @staticmethod
    def test_connection(config: DataSourceConfig) -> bool:
        """Test database connection"""
        try:
            connector = DatabaseManager.create_connector(config)
            return connector.connect()
        except Exception as e:
            logger.error(f"Connection test failed: {str(e)}")
            return False