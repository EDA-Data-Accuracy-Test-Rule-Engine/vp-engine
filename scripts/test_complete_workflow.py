#!/usr/bin/env python3
"""
Test script for VP Engine - Complete Workflow Test
Tests all 5 rule types with real PostgreSQL database
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.models.validation import (
    DataSourceConfig, DataSourceType, RuleSet, ValidationRule, RuleType,
    SQLGenerationContext
)
from src.database.connectors import DatabaseManager
from src.core.validation_engine import SQLValidationEngine
import json
from datetime import datetime

def test_complete_workflow():
    """Test complete VP Engine workflow with PostgreSQL database"""
    
    print("🚀 VP Engine Complete Workflow Test")
    print("=" * 60)
    
    # Step 1: Configure PostgreSQL connection
    print("\n📊 Step 1: Configuring PostgreSQL Connection")
    
    config = DataSourceConfig(
        type=DataSourceType.POSTGRESQL,
        name="hackathon_test_db",
        connection_params={
            "host": "localhost",
            "port": 5432,
            "database": "vpengine",
            "username": "vpuser",
            "password": "vppass123"
        }
    )
    
    # Step 2: Test database connection
    print("\n🔌 Step 2: Testing Database Connection")
    
    try:
        connector = DatabaseManager.create_connector(config)
        connection_success = connector.connect()
        
        if connection_success:
            print("✅ PostgreSQL connection established successfully!")
        else:
            print("❌ Failed to connect to PostgreSQL")
            return False
            
    except Exception as e:
        print(f"❌ Connection error: {str(e)}")
        return False
    
    # Step 3: Load test rules
    print("\n📋 Step 3: Loading Hackathon Challenge Rules")
    
    try:
        with open('templates/hackathon_test_rules.json', 'r') as f:
            rule_data = json.load(f)
        
        # Convert datetime strings back to datetime objects
        if 'created_at' in rule_data:
            rule_data['created_at'] = datetime.fromisoformat(rule_data['created_at'])
        
        for rule in rule_data.get('rules', []):
            if 'created_at' in rule:
                rule['created_at'] = datetime.fromisoformat(rule['created_at'])
        
        # Update data source config
        rule_data['data_source'] = config.dict()
        
        rule_set = RuleSet(**rule_data)
        print(f"✅ Loaded {len(rule_set.rules)} rules from template")
        
    except Exception as e:
        print(f"❌ Failed to load rules: {str(e)}")
        return False
    
    # Step 4: Execute validation with SQL generation
    print("\n🚀 Step 4: Executing Validation Rules")
    
    try:
        # Create SQL generation context
        context = SQLGenerationContext(
            database_type=DataSourceType.POSTGRESQL,
            schema_name="public",
            table_name="",  # Will be set per rule
            connection_info=config.connection_params
        )
        
        # Initialize SQL validation engine
        sql_engine = SQLValidationEngine(context)
        
        validation_results = []
        
        for i, rule in enumerate(rule_set.rules, 1):
            if not rule.enabled:
                continue
                
            print(f"\n📝 Rule {i}: {rule.name}")
            print(f"   Type: {rule.rule_type.value}")
            
            try:
                # Convert rule to dict format
                rule_dict = {
                    'name': rule.name,
                    'rule_type': rule.rule_type.value,
                    'target_column': rule.target_column,
                    'parameters': rule.parameters
                }
                
                # Set table name for context
                if rule.rule_type in [RuleType.SAME_STATISTICAL_COMPARISON, RuleType.DIFFERENT_STATISTICAL_COMPARISON]:
                    # For cross-table rules, use the first table as context
                    context.table_name = rule.parameters.get('table1', {}).get('table', 'transactions')
                else:
                    # Map rule types to correct tables based on target column
                    if rule.target_column in ['amount_usd']:
                        context.table_name = 'transactions'
                    elif rule.target_column in ['email', 'phone', 'age']:
                        context.table_name = 'customers'
                    elif rule.target_column in ['id', 'employee_code']:
                        context.table_name = 'employees'
                    else:
                        # Default fallback
                        table_mapping = {
                            RuleType.VALUE_RANGE: 'transactions',
                            RuleType.VALUE_TEMPLATE: 'customers', 
                            RuleType.DATA_CONTINUITY: 'employees'
                        }
                        context.table_name = table_mapping.get(rule.rule_type, 'transactions')
                
                # Generate SQL script
                sql_script = sql_engine.generate_validation_sql(rule_dict)
                print(f"   ✅ SQL Generated Successfully")
                
                # Execute SQL and get results
                result_df = connector.execute_query(sql_script)
                
                if not result_df.empty:
                    result_row = result_df.iloc[0]
                    
                    status = "PASS" if result_row.get('status') == 'PASS' else "FAIL"
                    total_rows = int(result_row.get('total_rows', 0))
                    failed_rows = int(result_row.get('failed_rows', 0))
                    passed_rows = int(result_row.get('passed_rows', 0))
                    
                    print(f"   📊 Status: {status}")
                    print(f"   📊 Total Rows: {total_rows}")
                    print(f"   📊 Failed Rows: {failed_rows}")
                    print(f"   📊 Passed Rows: {passed_rows}")
                    
                    validation_results.append({
                        'rule_name': rule.name,
                        'rule_type': rule.rule_type.value,
                        'status': status,
                        'total_rows': total_rows,
                        'failed_rows': failed_rows,
                        'passed_rows': passed_rows,
                        'sql_generated': True,
                        'sql_executed': True
                    })
                else:
                    print(f"   ❌ No results returned")
                    validation_results.append({
                        'rule_name': rule.name,
                        'rule_type': rule.rule_type.value,
                        'status': 'ERROR',
                        'error': 'No results returned',
                        'sql_generated': True,
                        'sql_executed': False
                    })
                    
            except Exception as rule_error:
                print(f"   ❌ Error: {str(rule_error)}")
                validation_results.append({
                    'rule_name': rule.name,
                    'rule_type': rule.rule_type.value,
                    'status': 'ERROR',
                    'error': str(rule_error),
                    'sql_generated': False,
                    'sql_executed': False
                })
        
        # Step 5: Generate test report
        print("\n📋 Step 5: Test Results Summary")
        print("=" * 60)
        
        total_rules = len(validation_results)
        successful_executions = len([r for r in validation_results if r.get('sql_executed')])
        passed_validations = len([r for r in validation_results if r.get('status') == 'PASS'])
        failed_validations = len([r for r in validation_results if r.get('status') == 'FAIL'])
        error_validations = len([r for r in validation_results if r.get('status') == 'ERROR'])
        
        print(f"📊 Total Rules Tested: {total_rules}")
        print(f"✅ Successfully Executed: {successful_executions}")
        print(f"🎯 Passed Validations: {passed_validations}")
        print(f"❌ Failed Validations: {failed_validations}")
        print(f"⚠️  Error Validations: {error_validations}")
        print(f"📈 Execution Success Rate: {(successful_executions/total_rules)*100:.1f}%")
        
        # Save detailed results
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        results_file = f"outputs/complete_workflow_test_{timestamp}.json"
        
        test_results = {
            'test_timestamp': timestamp,
            'database_type': 'PostgreSQL',
            'total_rules': total_rules,
            'successful_executions': successful_executions,
            'passed_validations': passed_validations,
            'failed_validations': failed_validations,
            'error_validations': error_validations,
            'execution_success_rate': f"{(successful_executions/total_rules)*100:.1f}%",
            'detailed_results': validation_results
        }
        
        with open(results_file, 'w') as f:
            json.dump(test_results, f, indent=2, default=str)
        
        print(f"\n💾 Detailed results saved to: {results_file}")
        
        # Final verdict
        if successful_executions == total_rules and error_validations == 0:
            print("\n🎉 TEST PASSED: All rules executed successfully!")
            return True
        else:
            print("\n⚠️  TEST COMPLETED WITH ISSUES: Some rules had errors")
            return False
            
    except Exception as e:
        print(f"\n❌ Test execution failed: {str(e)}")
        return False

if __name__ == "__main__":
    success = test_complete_workflow()
    sys.exit(0 if success else 1)