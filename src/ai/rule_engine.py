import openai
import json
from typing import List, Dict, Any, Optional
import structlog
import pandas as pd
from datetime import datetime

from ..config.settings import settings
from ..models.validation import ValidationRule, RuleType, ColumnInfo, AIRuleSuggestion

logger = structlog.get_logger()

class AIRuleEngine:
    """AI-powered rule suggestion engine using OpenAI"""
    
    def __init__(self):
        if not settings.OPENAI_API_KEY:
            logger.warning("OpenAI API key not configured. AI features will be disabled.")
            self.enabled = False
        else:
            openai.api_key = settings.OPENAI_API_KEY
            self.enabled = True
    
    def analyze_column_and_suggest_rules(self, column_info: ColumnInfo, 
                                       sample_data: List[Any]) -> AIRuleSuggestion:
        """Analyze column data and suggest validation rules using AI"""
        
        if not self.enabled:
            return self._fallback_rule_suggestion(column_info)
        
        try:
            # Prepare data analysis prompt
            prompt = self._create_analysis_prompt(column_info, sample_data)
            
            # Call OpenAI API
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {
                        "role": "system",
                        "content": """You are a data quality expert. Analyze the provided column data and suggest appropriate validation rules. 
                        Return your response as JSON with this structure:
                        {
                            "suggested_rules": [
                                {
                                    "name": "rule name",
                                    "rule_type": "null_check|range_check|regex_check|duplicate_check|data_type_check",
                                    "parameters": {},
                                    "reasoning": "why this rule is suggested",
                                    "confidence": 0.9
                                }
                            ],
                            "overall_confidence": 0.85,
                            "analysis_summary": "brief analysis of the column"
                        }"""
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.3,
                max_tokens=1000
            )
            
            # Parse AI response
            ai_response = json.loads(response.choices[0].message.content)
            
            # Convert AI suggestions to ValidationRule objects
            suggested_rules = []
            for rule_suggestion in ai_response.get("suggested_rules", []):
                rule = ValidationRule(
                    name=rule_suggestion["name"],
                    description=rule_suggestion.get("reasoning", ""),
                    rule_type=RuleType(rule_suggestion["rule_type"]),
                    target_column=column_info.name,
                    parameters=rule_suggestion.get("parameters", {}),
                    severity="error" if rule_suggestion.get("confidence", 0) > 0.8 else "warning",
                    created_by="ai_engine"
                )
                suggested_rules.append(rule)
            
            return AIRuleSuggestion(
                column_name=column_info.name,
                suggested_rules=suggested_rules,
                confidence_score=ai_response.get("overall_confidence", 0.7),
                reasoning=ai_response.get("analysis_summary", "AI analysis completed")
            )
            
        except Exception as e:
            logger.error(f"AI rule suggestion failed for column {column_info.name}: {str(e)}")
            return self._fallback_rule_suggestion(column_info)
    
    def _create_analysis_prompt(self, column_info: ColumnInfo, sample_data: List[Any]) -> str:
        """Create analysis prompt for AI"""
        
        prompt = f"""
        Analyze this database column and suggest validation rules:
        
        Column Information:
        - Name: {column_info.name}
        - Data Type: {column_info.data_type}
        - Nullable: {column_info.nullable}
        - Unique Count: {column_info.unique_count}
        - Null Count: {column_info.null_count}
        - Min Value: {column_info.min_value}
        - Max Value: {column_info.max_value}
        
        Sample Data (first 10 values):
        {sample_data[:10]}
        
        Based on this information, suggest appropriate validation rules to ensure data quality.
        Consider:
        1. Null value checks if the column should not be null
        2. Range checks for numeric data
        3. Format checks for strings (email, phone, etc.)
        4. Uniqueness checks if applicable
        5. Data type consistency checks
        
        Provide specific parameters for each rule (e.g., min/max values, regex patterns).
        """
        
        return prompt
    
    def _fallback_rule_suggestion(self, column_info: ColumnInfo) -> AIRuleSuggestion:
        """Fallback rule suggestion when AI is not available"""
        
        suggested_rules = []
        
        # Basic null check if column appears to be non-nullable
        if column_info.null_count == 0 and not column_info.nullable:
            suggested_rules.append(ValidationRule(
                name=f"Non-null check for {column_info.name}",
                description="Ensure column has no null values",
                rule_type=RuleType.NULL_CHECK,
                target_column=column_info.name,
                parameters={},
                created_by="fallback_engine"
            ))
        
        # Range check for numeric columns
        if column_info.data_type.lower() in ['int', 'integer', 'float', 'decimal', 'numeric']:
            if column_info.min_value is not None and column_info.max_value is not None:
                suggested_rules.append(ValidationRule(
                    name=f"Range check for {column_info.name}",
                    description=f"Values should be between {column_info.min_value} and {column_info.max_value}",
                    rule_type=RuleType.RANGE_CHECK,
                    target_column=column_info.name,
                    parameters={
                        "min_value": column_info.min_value,
                        "max_value": column_info.max_value
                    },
                    created_by="fallback_engine"
                ))
        
        # Email format check for email-like column names
        if 'email' in column_info.name.lower():
            suggested_rules.append(ValidationRule(
                name=f"Email format check for {column_info.name}",
                description="Validate email format",
                rule_type=RuleType.REGEX_CHECK,
                target_column=column_info.name,
                parameters={
                    "pattern": r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
                },
                created_by="fallback_engine"
            ))
        
        # Uniqueness check for ID-like columns
        if any(keyword in column_info.name.lower() for keyword in ['id', 'key', 'identifier']):
            suggested_rules.append(ValidationRule(
                name=f"Uniqueness check for {column_info.name}",
                description="Ensure all values are unique",
                rule_type=RuleType.DUPLICATE_CHECK,
                target_column=column_info.name,
                parameters={},
                created_by="fallback_engine"
            ))
        
        return AIRuleSuggestion(
            column_name=column_info.name,
            suggested_rules=suggested_rules,
            confidence_score=0.6,
            reasoning="Basic rule suggestions based on column characteristics"
        )
    
    def suggest_rules_for_dataset(self, columns: List[ColumnInfo], 
                                sample_data: Dict[str, List[Any]]) -> List[AIRuleSuggestion]:
        """Suggest rules for entire dataset"""
        
        suggestions = []
        for column in columns:
            column_sample = sample_data.get(column.name, [])
            suggestion = self.analyze_column_and_suggest_rules(column, column_sample)
            suggestions.append(suggestion)
        
        return suggestions
    
    def generate_rule_explanation(self, rule: ValidationRule) -> str:
        """Generate human-readable explanation for a rule"""
        
        explanations = {
            RuleType.NULL_CHECK: f"This rule ensures that the '{rule.target_column}' column contains no null/empty values.",
            RuleType.RANGE_CHECK: f"This rule validates that values in '{rule.target_column}' fall within the specified range.",
            RuleType.REGEX_CHECK: f"This rule validates that values in '{rule.target_column}' match the specified format pattern.",
            RuleType.DUPLICATE_CHECK: f"This rule ensures that all values in '{rule.target_column}' are unique.",
            RuleType.DATA_TYPE_CHECK: f"This rule validates that all values in '{rule.target_column}' are of the correct data type.",
            RuleType.UNIQUENESS_CHECK: f"This rule ensures that '{rule.target_column}' contains only unique values."
        }
        
        base_explanation = explanations.get(rule.rule_type, f"This rule validates '{rule.target_column}' column.")
        
        # Add parameter details
        if rule.parameters:
            if rule.rule_type == RuleType.RANGE_CHECK:
                min_val = rule.parameters.get('min_value')
                max_val = rule.parameters.get('max_value')
                if min_val is not None and max_val is not None:
                    base_explanation += f" Values must be between {min_val} and {max_val}."
            elif rule.rule_type == RuleType.REGEX_CHECK:
                pattern = rule.parameters.get('pattern')
                if pattern:
                    base_explanation += f" Pattern: {pattern}"
        
        return base_explanation