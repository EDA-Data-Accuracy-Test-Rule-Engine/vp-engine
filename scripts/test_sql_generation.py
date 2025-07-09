#!/usr/bin/env python3
"""
Test script for VP Engine with Hackathon Challenge database
This script demonstrates all 5 rule types working with the sample database
"""

import sys
import json
from pathlib import Path
from datetime import datetime

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from src.core.validation_engine import SQLValidationEngine
from src.models.validation import SQLGenerationContext, DataSourceType

def test_sql_generation():
    """Test SQL generation for all 5 rule types"""
    print("🚀 Testing VP Engine SQL Generation with Hackathon Challenge Rules")
    print("=" * 70)
    
    # Create SQL generation context
    context = SQLGenerationContext(
        database_type=DataSourceType.POSTGRESQL,
        schema_name="public",
        table_name="test_table",
        connection_info={}
    )
    
    # Initialize SQL validation engine
    engine = SQLValidationEngine(context)
    
    # Test rules for each type
    test_rules = [
        {
            "name": "Rule Type 1 - Value Range",
            "rule_type": "value_range",
            "target_column": "amount_usd",
            "parameters": {
                "min_value": 100,
                "max_value": 10000
            }
        },
        {
            "name": "Rule Type 2 - Email Template",
            "rule_type": "value_template", 
            "target_column": "email",
            "parameters": {
                "pattern": "^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}$"
            }
        },
        {
            "name": "Rule Type 3 - Data Continuity",
            "rule_type": "data_continuity",
            "target_column": "id",
            "parameters": {
                "sequence_type": "incremental"
            }
        },
        {
            "name": "Rule Type 4 - Same Statistical Comparison",
            "rule_type": "same_statistical_comparison",
            "target_column": "branch_code",
            "parameters": {
                "table1": {
                    "schema_name": "public",
                    "table": "table_a",
                    "columns": ["branch_code"],
                    "filter_condition": None
                },
                "table2": {
                    "schema_name": "public", 
                    "table": "table_b",
                    "columns": ["branch_code"],
                    "filter_condition": None
                },
                "statistical_function": "COUNT_DISTINCT",
                "comparison_operator": "="
            }
        },
        {
            "name": "Rule Type 5 - Different Statistical Comparison",
            "rule_type": "different_statistical_comparison",
            "target_column": "repayment_amount",
            "parameters": {
                "table1": {
                    "schema_name": "public",
                    "table": "overdue_loan_payments",
                    "columns": ["overdue_principal_payment", "overdue_principal_penalty", "overdue_interest_payment", "overdue_interest_penalty"],
                    "filter_condition": "contract_nbr IS NOT NULL"
                },
                "table2": {
                    "schema_name": "public",
                    "table": "transaction_summary", 
                    "columns": ["repayment_amount"],
                    "filter_condition": "contract_nbr IS NOT NULL"
                },
                "statistical_function1": "SUM",
                "statistical_function2": "SUM",
                "comparison_operator": "="
            }
        }
    ]
    
    # Generate and display SQL for each rule
    results = []
    for i, rule in enumerate(test_rules, 1):
        print(f"\n📋 {i}. {rule['name']}")
        print("-" * 50)
        
        try:
            # Update context for appropriate table
            if rule['rule_type'] == 'value_range':
                engine.context.table_name = "transactions"
            elif rule['rule_type'] == 'value_template':
                engine.context.table_name = "customers"
            elif rule['rule_type'] == 'data_continuity':
                engine.context.table_name = "employees"
            else:
                engine.context.table_name = "test_table"
            
            sql = engine.generate_validation_sql(rule)
            print("✅ SQL Generated Successfully")
            print(f"📝 SQL Script:")
            print(sql)
            
            results.append({
                "rule_name": rule['name'],
                "rule_type": rule['rule_type'],
                "status": "SUCCESS",
                "sql": sql
            })
            
        except Exception as e:
            print(f"❌ Error: {str(e)}")
            results.append({
                "rule_name": rule['name'],
                "rule_type": rule['rule_type'], 
                "status": "ERROR",
                "error": str(e)
            })
    
    # Save results
    output_dir = Path("outputs")
    output_dir.mkdir(exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    results_file = output_dir / f"sql_generation_test_{timestamp}.json"
    
    with open(results_file, 'w') as f:
        json.dump({
            "test_timestamp": timestamp,
            "total_rules": len(test_rules),
            "successful_generations": len([r for r in results if r['status'] == 'SUCCESS']),
            "results": results
        }, f, indent=2)
    
    print(f"\n💾 Test results saved to: {results_file}")
    
    # Summary
    success_count = len([r for r in results if r['status'] == 'SUCCESS'])
    print(f"\n📊 Test Summary:")
    print(f"   Total Rules Tested: {len(test_rules)}")
    print(f"   Successful Generations: {success_count}")
    print(f"   Success Rate: {success_count/len(test_rules)*100:.1f}%")
    
    return success_count == len(test_rules)

if __name__ == "__main__":
    test_sql_generation()