import pytest
import sys
from pathlib import Path

# Add src to path for testing
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from src.models.validation import (
    DataSourceType, DataSourceConfig, ValidationRule, 
    RuleType, RuleSet, ColumnInfo
)
from src.database.connectors import DatabaseManager, CSVConnector
from src.core.validation_engine import ValidationEngine, RuleValidationSummary

class TestValidationModels:
    """Test data validation models"""
    
    def test_data_source_config_creation(self):
        """Test DataSourceConfig creation"""
        config = DataSourceConfig(
            type=DataSourceType.CSV,
            name="test_csv",
            file_path="/path/to/test.csv"
        )
        
        assert config.type == DataSourceType.CSV
        assert config.name == "test_csv"
        assert config.file_path == "/path/to/test.csv"
    
    def test_validation_rule_creation(self):
        """Test ValidationRule creation"""
        rule = ValidationRule(
            name="Test Null Check",
            rule_type=RuleType.NULL_CHECK,
            target_column="email",
            description="Test null validation"
        )
        
        assert rule.name == "Test Null Check"
        assert rule.rule_type == RuleType.NULL_CHECK
        assert rule.target_column == "email"
        assert rule.enabled == True
    
    def test_rule_set_creation(self):
        """Test RuleSet creation with multiple rules"""
        config = DataSourceConfig(
            type=DataSourceType.CSV,
            name="test_csv",
            file_path="/test.csv"
        )
        
        rules = [
            ValidationRule(
                name="Null Check",
                rule_type=RuleType.NULL_CHECK,
                target_column="email"
            ),
            ValidationRule(
                name="Range Check",
                rule_type=RuleType.RANGE_CHECK,
                target_column="age",
                parameters={"min_value": 18, "max_value": 100}
            )
        ]
        
        rule_set = RuleSet(
            name="Test Rules",
            data_source=config,
            rules=rules
        )
        
        assert rule_set.name == "Test Rules"
        assert len(rule_set.rules) == 2
        assert len(rule_set.get_enabled_rules()) == 2

class TestDatabaseConnectors:
    """Test database connection functionality"""
    
    @pytest.fixture
    def sample_csv_path(self, tmp_path):
        """Create a temporary CSV file for testing"""
        csv_content = """id,name,email,age
1,John Doe,john@example.com,30
2,Jane Smith,jane@example.com,25
3,Bob Wilson,,35
4,Alice Brown,alice@invalid,22"""
        
        csv_file = tmp_path / "test_data.csv"
        csv_file.write_text(csv_content)
        return str(csv_file)
    
    def test_csv_connector_creation(self, sample_csv_path):
        """Test CSV connector initialization"""
        config = DataSourceConfig(
            type=DataSourceType.CSV,
            name="test_csv",
            file_path=sample_csv_path
        )
        
        connector = DatabaseManager.create_connector(config)
        assert isinstance(connector, CSVConnector)
        assert connector.file_path == sample_csv_path
    
    def test_csv_connector_connection(self, sample_csv_path):
        """Test CSV connector can load data"""
        config = DataSourceConfig(
            type=DataSourceType.CSV,
            name="test_csv",
            file_path=sample_csv_path
        )
        
        connector = DatabaseManager.create_connector(config)
        success = connector.connect()
        assert success == True
        assert connector.df is not None
        assert len(connector.df) == 4
    
    def test_csv_get_columns(self, sample_csv_path):
        """Test CSV column analysis"""
        config = DataSourceConfig(
            type=DataSourceType.CSV,
            name="test_csv",
            file_path=sample_csv_path
        )
        
        connector = DatabaseManager.create_connector(config)
        connector.connect()
        
        columns = connector.get_columns()
        assert len(columns) == 4
        
        # Check column names
        column_names = [col.name for col in columns]
        assert "id" in column_names
        assert "name" in column_names
        assert "email" in column_names
        assert "age" in column_names
        
        # Check for null detection
        email_col = next(col for col in columns if col.name == "email")
        assert email_col.null_count == 1  # Bob Wilson has null email

class TestValidationEngine:
    """Test validation engine functionality"""
    
    @pytest.fixture
    def sample_csv_path(self, tmp_path):
        """Create a temporary CSV file for testing"""
        csv_content = """id,name,email,age,salary
1,John Doe,john@example.com,30,50000
2,Jane Smith,jane@example.com,25,45000
3,Bob Wilson,,35,60000
4,Alice Brown,alice@invalid,150,40000
5,Charlie Davis,charlie@example.com,20,"""
        
        csv_file = tmp_path / "test_data.csv"
        csv_file.write_text(csv_content)
        return str(csv_file)
    
    @pytest.fixture
    def csv_connector(self, sample_csv_path):
        """Create and connect CSV connector"""
        config = DataSourceConfig(
            type=DataSourceType.CSV,
            name="test_csv",
            file_path=sample_csv_path
        )
        
        connector = DatabaseManager.create_connector(config)
        connector.connect()
        return connector
    
    def test_null_check_validation(self, csv_connector):
        """Test null check validation rule"""
        engine = ValidationEngine(csv_connector)
        
        rule = ValidationRule(
            name="Email Null Check",
            rule_type=RuleType.NULL_CHECK,
            target_column="email"
        )
        
        # Note: CSV connector doesn't support SQL queries like database connectors
        # This test validates the rule structure and engine initialization
        assert engine.connector == csv_connector
        assert rule.rule_type == RuleType.NULL_CHECK
    
    def test_validation_summary_generation(self):
        """Test validation result summary generation"""
        from src.models.validation import ValidationResult
        
        results = [
            ValidationResult(
                rule_name="Test Rule 1",
                status="PASS",
                total_rows=100,
                failed_rows=0,
                passed_rows=100,
                execution_time_ms=50
            ),
            ValidationResult(
                rule_name="Test Rule 2", 
                status="FAIL",
                total_rows=100,
                failed_rows=10,
                passed_rows=90,
                execution_time_ms=75
            )
        ]
        
        summary = RuleValidationSummary.generate_summary(results)
        
        assert summary['summary']['total_rules'] == 2
        assert summary['summary']['passed_rules'] == 1
        assert summary['summary']['failed_rules'] == 1
        assert summary['summary']['success_rate'] == 50.0
        assert summary['summary']['total_rows_checked'] == 200
        assert summary['summary']['total_failed_rows'] == 10

class TestIntegration:
    """Integration tests for end-to-end functionality"""
    
    def test_import_all_modules(self):
        """Test that all main modules can be imported without errors"""
        try:
            from src.models.validation import DataSourceType, ValidationRule
            from src.database.connectors import DatabaseManager
            from src.core.validation_engine import ValidationEngine
            from src.ai.rule_engine import AIRuleEngine
            from src.config.settings import settings
            
            # If we get here, all imports succeeded
            assert True
        except ImportError as e:
            pytest.fail(f"Failed to import modules: {e}")
    
    def test_json_serialization(self):
        """Test that models can be serialized to JSON"""
        import json
        
        rule = ValidationRule(
            name="Test Rule",
            rule_type=RuleType.NULL_CHECK,
            target_column="email",
            parameters={"test": "value"}
        )
        
        # Convert to dict (simulating JSON serialization)
        rule_dict = rule.dict()
        
        # Convert datetime to string for JSON compatibility
        rule_dict['created_at'] = rule_dict['created_at'].isoformat()
        
        # Should be able to serialize to JSON
        json_str = json.dumps(rule_dict)
        assert json_str is not None
        assert "Test Rule" in json_str

if __name__ == "__main__":
    pytest.main([__file__, "-v"])