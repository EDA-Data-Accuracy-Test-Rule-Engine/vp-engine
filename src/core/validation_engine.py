"""
VP Engine - Core Validation Engine
SQL-based data validation engine that generates parameterized SQL scripts
"""
import json
import pandas as pd
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import re
from datetime import datetime
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))
from models.validation import (
    DataSourceType, RuleType, ValidationResult, StatisticalFunction,
    ComparisonOperator, TableReference, BooleanOperator, ComplexRule,
    SQLGenerationContext
)

class ValidationStatus(Enum):
    PASSED = "passed"
    FAILED = "failed"
    WARNING = "warning"
    ERROR = "error"

@dataclass 
class RuleValidationSummary:
    total_rules: int
    passed_rules: int
    failed_rules: int
    warning_rules: int
    error_rules: int
    results: List[ValidationResult]
    execution_time_ms: int = 0

class SQLValidationEngine:
    """SQL-based validation engine that generates parameterized SQL scripts"""
    
    def __init__(self, context: SQLGenerationContext):
        self.context = context
        self.database_type = context.database_type
        
    def generate_validation_sql(self, rule: Dict[str, Any]) -> str:
        """Generate SQL script for a validation rule"""
        rule_type = rule.get('rule_type') or rule.get('type')
        
        if rule_type == RuleType.VALUE_RANGE or rule_type == 'value_range':
            return self._generate_value_range_sql(rule)
        elif rule_type == RuleType.VALUE_TEMPLATE or rule_type == 'value_template':
            return self._generate_value_template_sql(rule)
        elif rule_type == RuleType.DATA_CONTINUITY or rule_type == 'data_continuity':
            return self._generate_data_continuity_sql(rule)
        elif rule_type == RuleType.SAME_STATISTICAL_COMPARISON or rule_type == 'same_statistical_comparison':
            return self._generate_same_statistical_comparison_sql(rule)
        elif rule_type == RuleType.DIFFERENT_STATISTICAL_COMPARISON or rule_type == 'different_statistical_comparison':
            return self._generate_different_statistical_comparison_sql(rule)
        else:
            raise ValueError(f"Unsupported rule type: {rule_type}")
    
    def _get_table_reference(self, table_name: str = None, schema: str = None) -> str:
        """Generate properly formatted table reference"""
        schema = schema or self.context.schema_name
        table = table_name or self.context.table_name
        
        if schema:
            return f"{schema}.{table}"
        return table
    
    def _generate_value_range_sql(self, rule: Dict[str, Any]) -> str:
        """Generate SQL for value range validation (Rule Type 1)"""
        column = rule['target_column']
        params = rule.get('parameters', {})
        min_val = params.get('min_value')
        max_val = params.get('max_value')
        
        table_ref = self._get_table_reference()
        
        conditions = []
        if min_val is not None:
            conditions.append(f"{column} < {min_val}")
        if max_val is not None:
            conditions.append(f"{column} > {max_val}")
        
        where_clause = " OR ".join(conditions) if conditions else "1=0"
        
        sql = f"""
SELECT 
    '{rule.get('name', 'Value Range Check')}' as rule_name,
    COUNT(*) as total_rows,
    SUM(CASE WHEN ({where_clause}) THEN 1 ELSE 0 END) as failed_rows,
    COUNT(*) - SUM(CASE WHEN ({where_clause}) THEN 1 ELSE 0 END) as passed_rows,
    CASE 
        WHEN SUM(CASE WHEN ({where_clause}) THEN 1 ELSE 0 END) = 0 THEN 'PASS'
        ELSE 'FAIL'
    END as status
FROM {table_ref}
WHERE {column} IS NOT NULL;
"""
        return sql.strip()
    
    def _generate_value_template_sql(self, rule: Dict[str, Any]) -> str:
        """Generate SQL for regex template validation (Rule Type 2)"""
        column = rule['target_column']
        params = rule.get('parameters', {})
        pattern = params.get('pattern') or params.get('regex_pattern', '.*')
        
        table_ref = self._get_table_reference()
        
        if self.database_type == DataSourceType.POSTGRESQL:
            regex_condition = f"{column} !~ '{pattern}'"
        elif self.database_type == DataSourceType.MYSQL:
            regex_condition = f"{column} NOT REGEXP '{pattern}'"
        else:
            regex_condition = f"NOT REGEXP_LIKE({column}, '{pattern}')"
        
        sql = f"""
SELECT 
    '{rule.get('name', 'Value Template Check')}' as rule_name,
    COUNT(*) as total_rows,
    SUM(CASE WHEN ({regex_condition}) THEN 1 ELSE 0 END) as failed_rows,
    COUNT(*) - SUM(CASE WHEN ({regex_condition}) THEN 1 ELSE 0 END) as passed_rows,
    CASE 
        WHEN SUM(CASE WHEN ({regex_condition}) THEN 1 ELSE 0 END) = 0 THEN 'PASS'
        ELSE 'FAIL'
    END as status
FROM {table_ref}
WHERE {column} IS NOT NULL;
"""
        return sql.strip()
    
    def _generate_data_continuity_sql(self, rule: Dict[str, Any]) -> str:
        """Generate SQL for data continuity validation (Rule Type 3)"""
        column = rule['target_column']
        params = rule.get('parameters', {})
        sequence_type = params.get('sequence_type', 'incremental')
        
        table_ref = self._get_table_reference()
        
        if sequence_type == 'incremental':
            sql = f"""
WITH sequence_check AS (
    SELECT 
        {column},
        LAG({column}) OVER (ORDER BY {column}) as prev_value,
        ROW_NUMBER() OVER (ORDER BY {column}) as expected_sequence
    FROM {table_ref}
    WHERE {column} IS NOT NULL
),
gaps AS (
    SELECT COUNT(*) as gap_count
    FROM sequence_check
    WHERE {column} != prev_value + 1 AND prev_value IS NOT NULL
)
SELECT 
    '{rule.get('name', 'Data Continuity Check')}' as rule_name,
    (SELECT COUNT(*) FROM {table_ref}) as total_rows,
    (SELECT gap_count FROM gaps) as failed_rows,
    (SELECT COUNT(*) FROM {table_ref}) - (SELECT gap_count FROM gaps) as passed_rows,
    CASE 
        WHEN (SELECT gap_count FROM gaps) = 0 THEN 'PASS'
        ELSE 'FAIL'
    END as status;
"""
        else:
            sql = f"""
WITH timestamp_gaps AS (
    SELECT 
        COUNT(*) as gap_count
    FROM (
        SELECT 
            {column},
            LAG({column}) OVER (ORDER BY {column}) as prev_timestamp,
            EXTRACT(EPOCH FROM ({column} - LAG({column}) OVER (ORDER BY {column}))) as time_diff
        FROM {table_ref}
        WHERE {column} IS NOT NULL
    ) t
    WHERE time_diff > {params.get('max_gap_seconds', 3600)}
)
SELECT 
    '{rule.get('name', 'Data Continuity Check')}' as rule_name,
    (SELECT COUNT(*) FROM {table_ref}) as total_rows,
    (SELECT gap_count FROM timestamp_gaps) as failed_rows,
    (SELECT COUNT(*) FROM {table_ref}) - (SELECT gap_count FROM timestamp_gaps) as passed_rows,
    CASE 
        WHEN (SELECT gap_count FROM timestamp_gaps) = 0 THEN 'PASS'
        ELSE 'FAIL'
    END as status;
"""
        
        return sql.strip()
    
    def _generate_same_statistical_comparison_sql(self, rule: Dict[str, Any]) -> str:
        """Generate SQL for same statistical comparison (Rule Type 4)"""
        params = rule.get('parameters', {})
        table1 = params.get('table1')
        table2 = params.get('table2')
        function = params.get('statistical_function', StatisticalFunction.AVG)
        operator = params.get('comparison_operator', ComparisonOperator.EQUAL)
        
        table1_ref = f"{table1.get('schema_name', '')}.{table1['table']}" if table1.get('schema_name') else table1['table']
        table2_ref = f"{table2.get('schema_name', '')}.{table2['table']}" if table2.get('schema_name') else table2['table']
        
        column1 = table1['columns'][0]
        column2 = table2['columns'][0]
        
        # Fix PostgreSQL function name
        if function == StatisticalFunction.COUNT_DISTINCT:
            function_sql1 = f"COUNT(DISTINCT {column1})"
            function_sql2 = f"COUNT(DISTINCT {column2})"
        else:
            function_sql1 = f"{function}({column1})"
            function_sql2 = f"{function}({column2})"
        
        sql = f"""
WITH stats1 AS (
    SELECT {function_sql1} as stat_value
    FROM {table1_ref}
    {f"WHERE {table1.get('filter_condition')}" if table1.get('filter_condition') else ""}
),
stats2 AS (
    SELECT {function_sql2} as stat_value
    FROM {table2_ref}
    {f"WHERE {table2.get('filter_condition')}" if table2.get('filter_condition') else ""}
),
comparison AS (
    SELECT 
        s1.stat_value as table1_stat,
        s2.stat_value as table2_stat,
        CASE 
            WHEN s1.stat_value {operator} s2.stat_value THEN 'PASS'
            ELSE 'FAIL'
        END as status
    FROM stats1 s1, stats2 s2
)
SELECT 
    '{rule.get('name', 'Same Statistical Comparison')}' as rule_name,
    1 as total_rows,
    CASE WHEN status = 'FAIL' THEN 1 ELSE 0 END as failed_rows,
    CASE WHEN status = 'PASS' THEN 1 ELSE 0 END as passed_rows,
    status,
    table1_stat,
    table2_stat
FROM comparison;
"""
        return sql.strip()
    
    def _generate_different_statistical_comparison_sql(self, rule: Dict[str, Any]) -> str:
        """Generate SQL for different statistical comparison (Rule Type 5)"""
        params = rule.get('parameters', {})
        table1 = params.get('table1')
        table2 = params.get('table2')
        function1 = params.get('statistical_function1', StatisticalFunction.SUM)
        function2 = params.get('statistical_function2', StatisticalFunction.AVG)
        operator = params.get('comparison_operator', ComparisonOperator.EQUAL)
        
        table1_ref = f"{table1.get('schema_name', '')}.{table1['table']}" if table1.get('schema_name') else table1['table']
        table2_ref = f"{table2.get('schema_name', '')}.{table2['table']}" if table2.get('schema_name') else table2['table']
        
        columns1 = table1['columns']
        columns2 = table2['columns']
        
        if len(columns1) > 1:
            columns1_expr = " + ".join([f"{function1}({col})" for col in columns1])
        else:
            columns1_expr = f"{function1}({columns1[0]})"
            
        columns2_expr = f"{function2}({columns2[0]})"
        
        sql = f"""
WITH stats1 AS (
    SELECT ({columns1_expr}) as stat_value
    FROM {table1_ref}
    {f"WHERE {table1.get('filter_condition')}" if table1.get('filter_condition') else ""}
),
stats2 AS (
    SELECT {columns2_expr} as stat_value
    FROM {table2_ref}
    {f"WHERE {table2.get('filter_condition')}" if table2.get('filter_condition') else ""}
),
comparison AS (
    SELECT 
        s1.stat_value as table1_stat,
        s2.stat_value as table2_stat,
        CASE 
            WHEN s1.stat_value {operator} s2.stat_value THEN 'PASS'
            ELSE 'FAIL'
        END as status
    FROM stats1 s1, stats2 s2
)
SELECT 
    '{rule.get('name', 'Different Statistical Comparison')}' as rule_name,
    1 as total_rows,
    CASE WHEN status = 'FAIL' THEN 1 ELSE 0 END as failed_rows,
    CASE WHEN status = 'PASS' THEN 1 ELSE 0 END as passed_rows,
    status,
    table1_stat,
    table2_stat
FROM comparison;
"""
        return sql.strip()
    
    def generate_complex_rule_sql(self, complex_rule: ComplexRule) -> str:
        """Generate SQL for complex boolean rule combinations"""
        rule_sqls = {}
        for rule_id, rule in complex_rule.rules.items():
            rule_dict = rule.dict() if hasattr(rule, 'dict') else rule
            rule_sqls[rule_id] = self.generate_validation_sql(rule_dict)
        
        expression = complex_rule.expression
        
        combined_sql = f"""
-- Complex Rule: {complex_rule.name}
-- Boolean Expression: {expression}

"""
        for rule_id, sql in rule_sqls.items():
            combined_sql += f"-- Rule ID: {rule_id}\n{sql}\n\nUNION ALL\n\n"
        
        combined_sql = combined_sql.rstrip("\n\nUNION ALL\n\n")
        
        return combined_sql

ValidationEngine = SQLValidationEngine