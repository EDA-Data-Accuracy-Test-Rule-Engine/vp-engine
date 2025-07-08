"""
VP Engine - Core Validation Engine
Simple rule-based data validation without Great Expectations
"""
import json
import pandas as pd
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from enum import Enum
import re
from datetime import datetime

class ValidationStatus(Enum):
    PASSED = "passed"
    FAILED = "failed"
    WARNING = "warning"

@dataclass
class ValidationResult:
    rule_name: str
    status: ValidationStatus
    message: str
    details: Dict[str, Any]
    failed_count: int = 0
    total_count: int = 0

@dataclass 
class RuleValidationSummary:
    total_rules: int
    passed_rules: int
    failed_rules: int
    warning_rules: int
    results: List[ValidationResult]

class ValidationEngine:
    """Simple validation engine for data quality checks"""
    
    def __init__(self):
        self.rules = {}
        
    def load_rules_from_file(self, file_path: str) -> Dict[str, Any]:
        """Load validation rules from JSON file"""
        with open(file_path, 'r') as f:
            self.rules = json.load(f)
        return self.rules
    
    def validate_dataframe(self, df: pd.DataFrame, rules: Optional[Dict] = None) -> RuleValidationSummary:
        """Validate dataframe against rules"""
        if rules is None:
            rules = self.rules
            
        results = []
        
        for rule_name, rule_config in rules.get('rules', {}).items():
            result = self._apply_rule(df, rule_name, rule_config)
            results.append(result)
        
        # Calculate summary
        passed = sum(1 for r in results if r.status == ValidationStatus.PASSED)
        failed = sum(1 for r in results if r.status == ValidationStatus.FAILED)
        warnings = sum(1 for r in results if r.status == ValidationStatus.WARNING)
        
        return RuleValidationSummary(
            total_rules=len(results),
            passed_rules=passed,
            failed_rules=failed,
            warning_rules=warnings,
            results=results
        )
    
    def _apply_rule(self, df: pd.DataFrame, rule_name: str, rule_config: Dict) -> ValidationResult:
        """Apply a single validation rule"""
        rule_type = rule_config.get('type')
        
        try:
            if rule_type == 'not_null':
                return self._validate_not_null(df, rule_name, rule_config)
            elif rule_type == 'unique':
                return self._validate_unique(df, rule_name, rule_config)
            elif rule_type == 'range':
                return self._validate_range(df, rule_name, rule_config)
            elif rule_type == 'format':
                return self._validate_format(df, rule_name, rule_config)
            elif rule_type == 'enum':
                return self._validate_enum(df, rule_name, rule_config)
            else:
                return ValidationResult(
                    rule_name=rule_name,
                    status=ValidationStatus.FAILED,
                    message=f"Unknown rule type: {rule_type}",
                    details={},
                    failed_count=1,
                    total_count=1
                )
        except Exception as e:
            return ValidationResult(
                rule_name=rule_name,
                status=ValidationStatus.FAILED,
                message=f"Rule execution failed: {str(e)}",
                details={},
                failed_count=1,
                total_count=1
            )
    
    def _validate_not_null(self, df: pd.DataFrame, rule_name: str, config: Dict) -> ValidationResult:
        """Validate that column has no null values"""
        column = config['column']
        if column not in df.columns:
            return ValidationResult(
                rule_name=rule_name,
                status=ValidationStatus.FAILED,
                message=f"Column '{column}' not found",
                details={},
                failed_count=1,
                total_count=1
            )
        
        null_count = df[column].isnull().sum()
        total_count = len(df)
        
        status = ValidationStatus.PASSED if null_count == 0 else ValidationStatus.FAILED
        
        return ValidationResult(
            rule_name=rule_name,
            status=status,
            message=f"Found {null_count} null values in column '{column}'",
            details={'null_count': int(null_count), 'column': column},
            failed_count=int(null_count),
            total_count=total_count
        )
    
    def _validate_unique(self, df: pd.DataFrame, rule_name: str, config: Dict) -> ValidationResult:
        """Validate that column values are unique"""
        column = config['column']
        if column not in df.columns:
            return ValidationResult(
                rule_name=rule_name,
                status=ValidationStatus.FAILED,
                message=f"Column '{column}' not found",
                details={},
                failed_count=1,
                total_count=1
            )
        
        total_count = len(df)
        unique_count = df[column].nunique()
        duplicate_count = total_count - unique_count
        
        status = ValidationStatus.PASSED if duplicate_count == 0 else ValidationStatus.FAILED
        
        return ValidationResult(
            rule_name=rule_name,
            status=status,
            message=f"Found {duplicate_count} duplicate values in column '{column}'",
            details={'duplicate_count': duplicate_count, 'column': column},
            failed_count=duplicate_count,
            total_count=total_count
        )
    
    def _validate_range(self, df: pd.DataFrame, rule_name: str, config: Dict) -> ValidationResult:
        """Validate that numeric values are within range"""
        column = config['column']
        min_val = config.get('min')
        max_val = config.get('max')
        
        if column not in df.columns:
            return ValidationResult(
                rule_name=rule_name,
                status=ValidationStatus.FAILED,
                message=f"Column '{column}' not found",
                details={},
                failed_count=1,
                total_count=1
            )
        
        # Convert to numeric, coercing errors to NaN
        numeric_col = pd.to_numeric(df[column], errors='coerce')
        
        mask = pd.Series([True] * len(df))
        if min_val is not None:
            mask = mask & (numeric_col >= min_val)
        if max_val is not None:
            mask = mask & (numeric_col <= max_val)
        
        # Also include non-null check
        mask = mask & numeric_col.notna()
        
        failed_count = (~mask).sum()
        total_count = len(df)
        
        status = ValidationStatus.PASSED if failed_count == 0 else ValidationStatus.FAILED
        
        return ValidationResult(
            rule_name=rule_name,
            status=status,
            message=f"Found {failed_count} values outside range [{min_val}, {max_val}] in column '{column}'",
            details={'failed_count': int(failed_count), 'column': column, 'min': min_val, 'max': max_val},
            failed_count=int(failed_count),
            total_count=total_count
        )
    
    def _validate_format(self, df: pd.DataFrame, rule_name: str, config: Dict) -> ValidationResult:
        """Validate that values match a regex pattern"""
        column = config['column']
        pattern = config['pattern']
        
        if column not in df.columns:
            return ValidationResult(
                rule_name=rule_name,
                status=ValidationStatus.FAILED,
                message=f"Column '{column}' not found",
                details={},
                failed_count=1,
                total_count=1
            )
        
        # Apply regex pattern to non-null values
        valid_mask = df[column].astype(str).str.match(pattern, na=False)
        null_mask = df[column].isnull()
        
        # Count only non-null values that don't match pattern
        failed_count = (~valid_mask & ~null_mask).sum()
        total_count = len(df)
        
        status = ValidationStatus.PASSED if failed_count == 0 else ValidationStatus.FAILED
        
        return ValidationResult(
            rule_name=rule_name,
            status=status,
            message=f"Found {failed_count} values not matching pattern '{pattern}' in column '{column}'",
            details={'failed_count': int(failed_count), 'column': column, 'pattern': pattern},
            failed_count=int(failed_count),
            total_count=total_count
        )
    
    def _validate_enum(self, df: pd.DataFrame, rule_name: str, config: Dict) -> ValidationResult:
        """Validate that values are in allowed list"""
        column = config['column']
        allowed_values = config['allowed_values']
        
        if column not in df.columns:
            return ValidationResult(
                rule_name=rule_name,
                status=ValidationStatus.FAILED,
                message=f"Column '{column}' not found",
                details={},
                failed_count=1,
                total_count=1
            )
        
        valid_mask = df[column].isin(allowed_values) | df[column].isnull()
        failed_count = (~valid_mask).sum()
        total_count = len(df)
        
        status = ValidationStatus.PASSED if failed_count == 0 else ValidationStatus.FAILED
        
        return ValidationResult(
            rule_name=rule_name,
            status=status,
            message=f"Found {failed_count} values not in allowed list in column '{column}'",
            details={'failed_count': int(failed_count), 'column': column, 'allowed_values': allowed_values},
            failed_count=int(failed_count),
            total_count=total_count
        )