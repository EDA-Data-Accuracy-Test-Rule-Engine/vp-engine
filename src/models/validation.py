from pydantic import BaseModel, Field
from typing import Dict, Any, List, Optional, Union
from enum import Enum
from datetime import datetime

class DataSourceType(str, Enum):
    POSTGRESQL = "postgresql"
    MYSQL = "mysql"
    CSV = "csv"

class RuleType(str, Enum):
    VALUE_RANGE = "value_range"
    VALUE_TEMPLATE = "value_template"
    DATA_CONTINUITY = "data_continuity"
    SAME_STATISTICAL_COMPARISON = "same_statistical_comparison"
    DIFFERENT_STATISTICAL_COMPARISON = "different_statistical_comparison"

class ColumnInfo(BaseModel):
    name: str
    data_type: str
    nullable: bool
    sample_values: List[Any] = []
    unique_count: Optional[int] = None
    null_count: Optional[int] = None
    min_value: Optional[Union[int, float, str]] = None
    max_value: Optional[Union[int, float, str]] = None

class DataSourceConfig(BaseModel):
    type: DataSourceType
    name: str
    connection_params: Dict[str, Any] = {}
    file_path: Optional[str] = None
    table_name: Optional[str] = None

class ValidationRule(BaseModel):
    id: Optional[str] = None
    name: str
    description: Optional[str] = None
    rule_type: RuleType
    target_column: str
    parameters: Dict[str, Any] = {}
    severity: str = "error"
    enabled: bool = True
    created_by: str = "system"
    created_at: datetime = Field(default_factory=datetime.now)

class RuleSet(BaseModel):
    name: str
    description: Optional[str] = None
    data_source: DataSourceConfig
    rules: List[ValidationRule]
    created_at: datetime = Field(default_factory=datetime.now)
    s3_key: Optional[str] = None

class ValidationResult(BaseModel):
    rule_name: str
    rule_id: Optional[str] = None
    status: str
    total_rows: int = 0
    failed_rows: int = 0
    passed_rows: int = 0
    error_message: Optional[str] = None
    execution_time_ms: int = 0
    details: Dict[str, Any] = {}
    generated_sql: Optional[str] = None

class StatisticalFunction(str, Enum):
    SUM = "SUM"
    AVG = "AVG"
    MIN = "MIN"
    MAX = "MAX"
    COUNT = "COUNT"
    COUNT_DISTINCT = "COUNT_DISTINCT"
    STDDEV = "STDDEV"
    VARIANCE = "VARIANCE"

class ComparisonOperator(str, Enum):
    EQUAL = "="
    NOT_EQUAL = "!="
    GREATER_THAN = ">"
    LESS_THAN = "<"
    GREATER_EQUAL = ">="
    LESS_EQUAL = "<="

class TableReference(BaseModel):
    schema_name: Optional[str] = None
    table: str
    columns: List[str]
    filter_condition: Optional[str] = None

class BooleanOperator(str, Enum):
    AND = "AND"
    OR = "OR"
    NOT = "NOT"

class ComplexRule(BaseModel):
    name: str
    description: Optional[str] = None
    expression: str
    rules: Dict[str, ValidationRule]
    enabled: bool = True

class SQLGenerationContext(BaseModel):
    database_type: DataSourceType
    schema_name: Optional[str] = None
    table_name: str
    connection_info: Dict[str, Any] = {}