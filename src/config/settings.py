"""
VP Engine Configuration Settings
"""
from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    """Application settings"""
    
    # Database settings
    database_url: Optional[str] = None
    
    # PostgreSQL settings
    postgres_host: Optional[str] = "localhost"
    postgres_port: int = 5432
    postgres_db: Optional[str] = "vpengine"
    postgres_user: Optional[str] = "vpuser"
    postgres_password: Optional[str] = "vppass123"
    
    # MySQL settings
    mysql_host: Optional[str] = "localhost"
    mysql_port: int = 3306
    mysql_db: Optional[str] = "vpengine"
    mysql_user: Optional[str] = "vpuser"
    mysql_password: Optional[str] = "vppass123"
    
    # AWS settings
    aws_access_key_id: Optional[str] = None
    aws_secret_access_key: Optional[str] = None
    aws_region: str = "us-east-1"
    aws_s3_bucket: Optional[str] = None  # Add this field to fix the validation error
    
    # Application settings
    log_level: str = "INFO"
    output_format: str = "table"  # table, json, csv
    
    # Add these properties for compatibility
    @property
    def POSTGRES_HOST(self):
        return self.postgres_host
    
    @property
    def POSTGRES_PORT(self):
        return self.postgres_port
    
    @property
    def POSTGRES_DB(self):
        return self.postgres_db
    
    @property
    def POSTGRES_USER(self):
        return self.postgres_user
    
    @property
    def POSTGRES_PASSWORD(self):
        return self.postgres_password
    
    @property
    def MYSQL_HOST(self):
        return self.mysql_host
    
    @property
    def MYSQL_PORT(self):
        return self.mysql_port
    
    @property
    def MYSQL_DB(self):
        return self.mysql_db
    
    @property
    def MYSQL_USER(self):
        return self.mysql_user
    
    @property
    def MYSQL_PASSWORD(self):
        return self.mysql_password
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"  # Allow extra fields to be ignored

# Global settings instance
settings = Settings()