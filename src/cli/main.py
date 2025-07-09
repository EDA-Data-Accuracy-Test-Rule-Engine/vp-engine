import click
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.prompt import Prompt, Confirm
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.syntax import Syntax
from pathlib import Path
import json
import os
import subprocess
from typing import Dict, Any, List, Optional
from datetime import datetime

from ..config.settings import settings
from ..models.validation import (
    DataSourceType, DataSourceConfig, ValidationRule, RuleSet, 
    RuleType, ColumnInfo, ValidationResult
)
from ..database.connectors import DatabaseManager
from ..ai.rule_engine import AIRuleEngine
from ..aws.services import S3RuleManager
from ..core.validation_engine import ValidationEngine

console = Console()

@click.group()
@click.version_option(version="1.0.0")
def cli():
    """
    🚀 VP Data Accuracy Test Rule Engine
    
    Interactive CLI for data validation and quality testing with AI-powered rule suggestions.
    """
    console.print(Panel.fit(
        "[bold blue]VP Data Accuracy Test Rule Engine[/bold blue]\n"
        "Interactive Data Validation Platform",
        border_style="blue"
    ))

@cli.command()
def start():
    """Start the interactive data validation workflow"""
    
    console.print("\n🎯 [bold green]Welcome to VP Data Accuracy Engine![/bold green]")
    console.print("Let's start by connecting to your data source...\n")
    
    # Main workflow loop - allows restarting from Step 2
    while True:
        # Step 1: Data Source Selection
        data_source_config = select_data_source()
        if not data_source_config:
            console.print("❌ [red]No data source selected. Exiting...[/red]")
            return
        
        # Step 2: Connect and analyze data source
        connector = connect_to_data_source(data_source_config)
        if not connector:
            console.print("❌ [red]Failed to connect to data source. Exiting...[/red]")
            return
        
        # Inner loop for table selection and validation workflow
        while True:
            # Step 3: Show tables and columns
            table_result = select_table_and_show_columns(connector, data_source_config)
            if table_result == "back":
                break  # Go back to data source selection
            elif not table_result:
                console.print("❌ [red]No table selected. Exiting...[/red]")
                return
            
            table_name = table_result
            
            # Step 4: User action selection
            action = select_user_action()
            if action == "back":
                continue  # Go back to table selection
            
            # Step 5: Execute based on user choice
            rule_set = None
            if action == "1":  # AI suggestion
                rule_set = handle_ai_suggestion(connector, data_source_config, table_name)
            elif action == "2":  # Use existing rules
                rule_set = handle_existing_rules(data_source_config, table_name)
            elif action == "3":  # Create new rules
                rule_set = handle_create_new_rules(data_source_config, table_name)
            
            if not rule_set:
                console.print("❌ [red]No rules were created or selected.[/red]")
                if not Confirm.ask("Would you like to try again?"):
                    return
                continue  # Go back to action selection
            
            # Step 6: Execute validation
            execute_validation_workflow(connector, rule_set, table_name)
            
            # Step 7: Ask what to do next
            next_action = ask_next_action()
            if next_action == "restart":
                break  # Break inner loop to restart from Step 2 (table selection)
            elif next_action == "new_source":
                break  # Break inner loop to go back to data source selection
            elif next_action == "exit":
                console.print("\n👋 [bold blue]Thank you for using VP Data Accuracy Engine![/bold blue]")
                return
        
        # If we broke out of inner loop due to "new_source", continue outer loop
        # If we broke out due to "restart", continue inner loop (but outer loop will restart inner loop)
        if next_action == "new_source":
            continue
        elif next_action == "restart":
            continue

def ask_next_action() -> str:
    """Ask user what they want to do after completing validation"""
    
    console.print(f"\n🎯 [bold cyan]What would you like to do next?[/bold cyan]")
    console.print("  1. 🔄 Restart with different table (same database)")
    console.print("  2. 🔌 Connect to different data source")
    console.print("  3. 🚪 Exit application")
    
    choice = Prompt.ask("\nEnter your choice", choices=["1", "2", "3"])
    
    if choice == "1":
        return "restart"
    elif choice == "2":
        return "new_source"
    else:
        return "exit"

def select_data_source() -> Optional[DataSourceConfig]:
    """Step 1: Let user select data source type"""
    
    console.print("📊 [bold cyan]Step 1: Select Data Source[/bold cyan]")
    console.print("Choose your data source type:")
    console.print("  1. PostgreSQL Database")
    console.print("  2. MySQL Database") 
    console.print("  3. CSV File")
    console.print("  0. ⬅️  Exit")
    
    choice = Prompt.ask("\nEnter your choice", choices=["0", "1", "2", "3"])
    
    if choice == "0":
        return None
    elif choice == "1":
        return configure_postgresql()
    elif choice == "2":
        return configure_mysql()
    elif choice == "3":
        return configure_csv()
    
    return None

def configure_postgresql() -> DataSourceConfig:
    """Configure PostgreSQL connection"""
    
    console.print("\n🐘 [bold blue]PostgreSQL Configuration[/bold blue]")
    
    host = Prompt.ask("Host", default="localhost")
    port = Prompt.ask("Port", default="5432")
    database = Prompt.ask("Database name")
    username = Prompt.ask("Username")
    password = Prompt.ask("Password", password=True)
    
    return DataSourceConfig(
        type=DataSourceType.POSTGRESQL,
        name=f"postgresql_{database}",
        connection_params={
            "host": host,
            "port": int(port),
            "database": database,
            "username": username,
            "password": password
        }
    )

def configure_mysql() -> DataSourceConfig:
    """Configure MySQL connection"""
    
    console.print("\n🐬 [bold green]MySQL Configuration[/bold green]")
    
    host = Prompt.ask("Host", default="localhost")
    port = Prompt.ask("Port", default="3306")
    database = Prompt.ask("Database name")
    username = Prompt.ask("Username")
    password = Prompt.ask("Password", password=True)
    
    return DataSourceConfig(
        type=DataSourceType.MYSQL,
        name=f"mysql_{database}",
        connection_params={
            "host": host,
            "port": int(port),
            "database": database,
            "username": username,
            "password": password
        }
    )

def configure_csv() -> DataSourceConfig:
    """Configure CSV file"""
    
    console.print("\n📄 [bold yellow]CSV File Configuration[/bold yellow]")
    
    while True:
        file_path = Prompt.ask("Enter CSV file path")
        
        if Path(file_path).exists():
            return DataSourceConfig(
                type=DataSourceType.CSV,
                name=f"csv_{Path(file_path).stem}",
                file_path=file_path
            )
        else:
            console.print(f"❌ [red]File not found: {file_path}[/red]")
            if not Confirm.ask("Try again?"):
                return None

def connect_to_data_source(config: DataSourceConfig):
    """Step 2: Connect to data source and test connection"""
    
    console.print(f"\n🔌 [bold cyan]Step 2: Connecting to {config.name}[/bold cyan]")
    
    try:
        with console.status("Establishing connection..."):
            connector = DatabaseManager.create_connector(config)
            success = connector.connect()
        
        if success:
            console.print("✅ [green]Connection established successfully![/green]")
            return connector
        else:
            console.print("❌ [red]Connection failed![/red]")
            return None
            
    except Exception as e:
        console.print(f"❌ [red]Connection error: {str(e)}[/red]")
        return None

def select_table_and_show_columns(connector, config: DataSourceConfig):
    """Step 3: Show tables and let user select, then show columns"""
    
    console.print("\n📋 [bold cyan]Step 3: Database Schema Overview[/bold cyan]")
    
    try:
        tables = connector.get_tables()
        
        if not tables:
            console.print("❌ [red]No tables found in the data source[/red]")
            return None
        
        # Show all tables with their structure first
        console.print(f"📊 [bold green]Found {len(tables)} tables in database:[/bold green]")
        
        all_tables_info = {}
        for table in tables:
            try:
                columns = connector.get_columns(table)
                all_tables_info[table] = columns
                console.print(f"\n🗂️  [bold]{table}[/bold] ({len(columns)} columns)")
                column_names = [col.name for col in columns[:5]]  # Show first 5 columns
                if len(columns) > 5:
                    column_names.append("...")
                console.print(f"   Columns: {', '.join(column_names)}")
            except Exception:
                console.print(f"\n🗂️  [bold]{table}[/bold] (unable to read columns)")
        
        console.print(f"\n💡 [yellow]For cross-table comparison rules (type 4 & 5), you can select any primary table.[/yellow]")
        console.print(f"   [yellow]The system will automatically detect related tables during rule execution.[/yellow]")
        
        # Let user choose primary table for validation
        if len(tables) == 1:
            primary_table = tables[0]
            console.print(f"\n📊 Selected primary table: [bold]{primary_table}[/bold]")
        else:
            console.print(f"\n📋 [bold cyan]Select Primary Table for Validation:[/bold cyan]")
            for i, table in enumerate(tables, 1):
                console.print(f"  {i}. {table}")
            console.print(f"  0. ⬅️  Back to data source selection")
            
            while True:
                try:
                    choice = Prompt.ask(f"\nSelect primary table (0-{len(tables)})")
                    
                    if choice == "0":
                        return "back"
                    
                    choice_int = int(choice)
                    if 1 <= choice_int <= len(tables):
                        primary_table = tables[choice_int - 1]
                        break
                    else:
                        console.print(f"❌ [red]Please enter a number between 0 and {len(tables)}[/red]")
                except ValueError:
                    console.print("❌ [red]Please enter a valid number[/red]")
        
        # Display detailed info for selected table
        if primary_table in all_tables_info:
            console.print(f"\n📊 [bold cyan]Detailed Analysis for {primary_table}:[/bold cyan]")
            display_column_info(all_tables_info[primary_table])
        
        # Store table info for cross-table rules
        config.table_info = all_tables_info
        
        return primary_table
        
    except Exception as e:
        console.print(f"❌ [red]Error getting table information: {str(e)}[/red]")
        return None

def display_column_info(columns: List[ColumnInfo]):
    """Display column information in a nice table"""
    
    table = Table(title="📊 Column Analysis")
    table.add_column("Column", style="cyan")
    table.add_column("Type", style="magenta")
    table.add_column("Nullable", style="yellow")
    table.add_column("Unique Count", style="green", justify="right")
    table.add_column("Null Count", style="red", justify="right")
    table.add_column("Sample Values", style="dim", width=30)
    
    for col in columns:
        sample_str = ", ".join(str(v) for v in col.sample_values[:3])
        if len(col.sample_values) > 3:
            sample_str += "..."
        
        table.add_row(
            col.name,
            col.data_type,
            "Yes" if col.nullable else "No",
            str(col.unique_count) if col.unique_count is not None else "N/A",
            str(col.null_count) if col.null_count is not None else "N/A",
            sample_str[:30]
        )
    
    console.print(table)

def select_user_action() -> str:
    """Step 4: Let user choose what to do next"""
    
    console.print(f"\n🎯 [bold cyan]Step 4: Choose Your Action[/bold cyan]")
    console.print("What would you like to do?")
    console.print("  1. 🤖 Get AI-powered rule suggestions")
    console.print("  2. 📚 Use existing rule templates")
    console.print("  3. ✏️  Create new custom rules")
    console.print("  0. ⬅️  Back to table selection")
    
    choice = Prompt.ask("\nEnter your choice", choices=["0", "1", "2", "3"])
    
    if choice == "0":
        return "back"
    
    return choice

def handle_ai_suggestion(connector, config: DataSourceConfig, table_name: str) -> Optional[RuleSet]:
    """Handle AI rule suggestion workflow"""
    
    console.print(f"\n🤖 [bold magenta]AI Rule Suggestion[/bold magenta]")
    console.print("Analyzing your data to suggest validation rules...")
    
    try:
        # Get column information and sample data for primary table
        with console.status("Analyzing data patterns..."):
            columns = connector.get_columns(table_name)
            sample_df = connector.get_sample_data(table_name, limit=100)
        
        # Initialize AI engine
        ai_engine = AIRuleEngine()
        
        # Get sample data for each column
        sample_data = {}
        for col in columns:
            if col.name in sample_df.columns:
                sample_data[col.name] = sample_df[col.name].dropna().tolist()[:10]
        
        # Get AI suggestions for single-table rules
        with console.status("Getting AI recommendations..."):
            suggestions = ai_engine.suggest_rules_for_dataset(columns, sample_data)
        
        all_rules = []
        
        # Process single-table rule suggestions
        if suggestions:
            console.print(f"\n📋 [bold green]AI suggested {len(suggestions)} single-table validation rules:[/bold green]")
            
            for suggestion in suggestions:
                if suggestion.suggested_rules:
                    console.print(f"\n📊 [bold cyan]Column: {suggestion.column_name}[/bold cyan]")
                    console.print(f"💡 Analysis: {suggestion.reasoning}")
                    console.print(f"🎯 Confidence: {suggestion.confidence_score:.1%}")
                    
                    for rule in suggestion.suggested_rules:
                        console.print(f"  • {rule.name}")
                        console.print(f"    Type: {rule.rule_type.value}")
                        console.print(f"    Description: {rule.description}")
                        if rule.parameters:
                            console.print(f"    Parameters: {rule.parameters}")
                        all_rules.append(rule)
        
        # Auto-generate cross-table rules if multiple tables available
        if hasattr(config, 'table_info') and config.table_info and len(config.table_info) > 1:
            console.print(f"\n🔗 [bold yellow]Detecting Cross-Table Relationship Rules...[/bold yellow]")
            
            cross_table_rules = generate_cross_table_rules(config.table_info, table_name)
            if cross_table_rules:
                console.print(f"🎯 [bold green]Found {len(cross_table_rules)} potential cross-table rules:[/bold green]")
                for rule in cross_table_rules:
                    console.print(f"  • {rule.name} ({rule.rule_type.value})")
                    console.print(f"    {rule.description}")
                
                if Confirm.ask("Include cross-table rules in the suggestion?"):
                    all_rules.extend(cross_table_rules)
        
        if all_rules:
            # Save suggestions to JSON file
            suggested_file = f"templates/ai_suggestions_{table_name}.json"
            Path("templates").mkdir(exist_ok=True)
            
            rule_set = RuleSet(
                name=f"AI Suggested Rules for {table_name}",
                description="Rules generated by AI analysis including cross-table relationships",
                data_source=config,
                rules=all_rules
            )
            
            with open(suggested_file, 'w') as f:
                rule_data = rule_set.model_dump()
                # Convert datetime to string for JSON serialization
                rule_data['created_at'] = rule_data['created_at'].isoformat()
                for rule in rule_data['rules']:
                    rule['created_at'] = rule['created_at'].isoformat()
                json.dump(rule_data, f, indent=2)
            
            console.print(f"\n💾 [green]AI suggestions saved to: {suggested_file}[/green]")
            
            if Confirm.ask("Would you like to use these AI-suggested rules?"):
                return rule_set
            else:
                console.print("You can edit the file and use it later with option 2.")
                return None
        else:
            console.print("❌ [red]No AI suggestions could be generated[/red]")
            return None
            
    except Exception as e:
        console.print(f"❌ [red]AI suggestion failed: {str(e)}[/red]")
        return None

def generate_cross_table_rules(table_info: Dict[str, List[ColumnInfo]], primary_table: str) -> List[ValidationRule]:
    """Generate cross-table validation rules based on table relationships"""
    
    cross_table_rules = []
    
    # Get list of all tables
    tables = list(table_info.keys())
    
    for other_table in tables:
        if other_table == primary_table:
            continue
            
        primary_columns = {col.name: col for col in table_info[primary_table]}
        other_columns = {col.name: col for col in table_info[other_table]}
        
        # Find common columns for same statistical comparison
        common_columns = set(primary_columns.keys()) & set(other_columns.keys())
        
        for common_col in common_columns:
            if common_col in ['id', 'created_at', 'updated_at']:  # Skip system columns
                continue
                
            # Same statistical comparison rule
            rule = ValidationRule(
                name=f"{common_col.title()} Consistency Check",
                description=f"Compare distinct {common_col} values between {primary_table} and {other_table}",
                rule_type=RuleType.SAME_STATISTICAL_COMPARISON,
                target_column=common_col,
                parameters={
                    "function": "COUNT_DISTINCT",
                    "table1": {
                        "schema": "public",
                        "table": primary_table,
                        "column": common_col
                    },
                    "table2": {
                        "schema": "public", 
                        "table": other_table,
                        "column": common_col
                    },
                    "comparison_operator": "="
                },
                severity="error",
                enabled=True
            )
            cross_table_rules.append(rule)
        
        # Look for amount/value columns for different statistical comparison
        amount_patterns = ['amount', 'value', 'price', 'cost', 'total', 'sum']
        
        primary_amount_cols = [col for col in primary_columns.keys() 
                              if any(pattern in col.lower() for pattern in amount_patterns)]
        other_amount_cols = [col for col in other_columns.keys() 
                            if any(pattern in col.lower() for pattern in amount_patterns)]
        
        if primary_amount_cols and other_amount_cols:
            # Create different statistical comparison rule
            rule = ValidationRule(
                name=f"{primary_table.title()} vs {other_table.title()} Amount Validation",
                description=f"Compare total amounts between {primary_table} and {other_table}",
                rule_type=RuleType.DIFFERENT_STATISTICAL_COMPARISON,
                target_column=primary_amount_cols[0],
                parameters={
                    "table1": {
                        "schema": "public",
                        "table": primary_table,
                        "column": primary_amount_cols[0],
                        "function": "SUM",
                        "filter": f"{primary_amount_cols[0]} IS NOT NULL"
                    },
                    "table2": {
                        "schema": "public",
                        "table": other_table, 
                        "column": other_amount_cols[0],
                        "function": "SUM",
                        "filter": f"{other_amount_cols[0]} IS NOT NULL"
                    },
                    "comparison_operator": "="
                },
                severity="warning",
                enabled=True
            )
            cross_table_rules.append(rule)
    
    return cross_table_rules

def handle_existing_rules(config: DataSourceConfig, table_name: str) -> Optional[RuleSet]:
    """Handle existing rules selection workflow"""
    
    console.print(f"\n📚 [bold blue]Existing Rule Templates[/bold blue]")
    
    # Look for rule files in templates directory
    templates_dir = Path("templates")
    if not templates_dir.exists():
        templates_dir.mkdir()
    
    rule_files = list(templates_dir.glob("*.json"))
    
    if not rule_files:
        console.print("❌ [red]No existing rule files found in templates/ directory[/red]")
        console.print("💡 [yellow]Tip: Create rules first using option 3 or AI suggestions (option 1)[/yellow]")
        return None
    
    # Display available rule files
    console.print("Available rule files:")
    for i, file_path in enumerate(rule_files, 1):
        try:
            with open(file_path, 'r') as f:
                rule_data = json.load(f)
            
            name = rule_data.get('name', file_path.stem)
            rule_count = len(rule_data.get('rules', []))
            description = rule_data.get('description', 'No description')
            
            console.print(f"  {i}. {file_path.name} - {name} ({rule_count} rules)")
        except Exception:
            console.print(f"  {i}. {file_path.name} - [red](Invalid file)[/red]")
    
    console.print(f"  0. ⬅️  Back to action selection")
    
    # Let user select
    while True:
        try:
            choice = Prompt.ask(f"\nSelect rule file (0-{len(rule_files)})")
            
            if choice == "0":
                return None
            
            choice_int = int(choice)
            if 1 <= choice_int <= len(rule_files):
                selected_file = rule_files[choice_int - 1]
                break
            else:
                console.print(f"❌ [red]Please enter a number between 0 and {len(rule_files)}[/red]")
        except ValueError:
            console.print("❌ [red]Please enter a valid number[/red]")
    
    # Load selected rule file
    try:
        with open(selected_file, 'r') as f:
            rule_data = json.load(f)
        
        # Convert datetime strings back to datetime objects
        from datetime import datetime
        if 'created_at' in rule_data:
            rule_data['created_at'] = datetime.fromisoformat(rule_data['created_at'])
        
        for rule in rule_data.get('rules', []):
            if 'created_at' in rule:
                rule['created_at'] = datetime.fromisoformat(rule['created_at'])
        
        # Update data source config
        rule_data['data_source'] = config.dict()
        
        rule_set = RuleSet(**rule_data)
        
        console.print(f"✅ [green]Loaded {len(rule_set.rules)} rules from {selected_file.name}[/green]")
        return rule_set
        
    except Exception as e:
        console.print(f"❌ [red]Failed to load rule file: {str(e)}[/red]")
        return None

def handle_create_new_rules(config: DataSourceConfig, table_name: str) -> Optional[RuleSet]:
    """Handle new rule creation workflow"""
    
    console.print(f"\n✏️ [bold yellow]Create New Rules[/bold yellow]")
    
    rule_set_name = Prompt.ask("Enter a name for your rule set", default=f"Rules for {table_name}")
    
    import re
    safe_name = re.sub(r'[^a-zA-Z0-9_-]', '_', rule_set_name.lower())
    template_file = f"templates/{safe_name}.json"
    
    template_rule_set = RuleSet(
        name=rule_set_name,
        description=f"Custom validation rules for {table_name}",
        data_source=config,
        rules=[
            ValidationRule(
                name="Example Value Range Check",
                description="Example rule - replace with your own",
                rule_type=RuleType.VALUE_RANGE,
                target_column="your_column_name",
                parameters={"min_value": 0, "max_value": 100},
                enabled=False
            )
        ]
    )
    
    Path("templates").mkdir(exist_ok=True)
    
    with open(template_file, 'w') as f:
        rule_data = template_rule_set.dict()
        rule_data['created_at'] = rule_data['created_at'].isoformat()
        for rule in rule_data['rules']:
            rule['created_at'] = rule['created_at'].isoformat()
        json.dump(rule_data, f, indent=2)
    
    console.print(f"📁 [green]Created template file: {template_file}[/green]")
    console.print("\n📝 [yellow]Please edit this file to define your validation rules.[/yellow]")
    console.print("\n🔧 [cyan]Rule types available (Hackathon Challenge):[/cyan]")
    console.print("  • value_range - Validate data according to expected ranges")
    console.print("  • value_template - Validate regex templates") 
    console.print("  • data_continuity - Validate data continuity/integrity")
    console.print("  • same_statistical_comparison - Same statistical calculations comparison")
    console.print("  • different_statistical_comparison - Different statistical calculations comparison")
    
    console.print(f"\n📖 [blue]Example file path: {Path(template_file).absolute()}[/blue]")
    
    if Confirm.ask("Open the file in your default editor?"):
        try:
            if os.name == 'nt':
                os.startfile(template_file)
            elif os.name == 'posix':
                subprocess.call(['open', template_file])
        except Exception as e:
            console.print(f"❌ [red]Could not open file automatically: {str(e)}[/red]")
    
    input("\n⏸️  Press Enter when you have finished editing the file...")
    
    if Confirm.ask("Upload rules to AWS S3 for backup?"):
        try:
            s3_manager = S3RuleManager()
            
            with open(template_file, 'r') as f:
                rule_data = json.load(f)
            
            from datetime import datetime
            if 'created_at' in rule_data:
                rule_data['created_at'] = datetime.fromisoformat(rule_data['created_at'])
            
            for rule in rule_data.get('rules', []):
                if 'created_at' in rule:
                    rule['created_at'] = datetime.fromisoformat(rule['created_at'])
            
            rule_set = RuleSet(**rule_data)
            
            with console.status("Uploading to S3..."):
                s3_key = s3_manager.upload_rule_set(rule_set, f"rules/{safe_name}.json")
            
            console.print(f"☁️ [green]Rules uploaded to S3: {s3_key}[/green]")
            
        except Exception as e:
            console.print(f"❌ [red]S3 upload failed: {str(e)}[/red]")
    
    try:
        with open(template_file, 'r') as f:
            rule_data = json.load(f)
        
        from datetime import datetime
        if 'created_at' in rule_data:
            rule_data['created_at'] = datetime.fromisoformat(rule_data['created_at'])
        
        for rule in rule_data.get('rules', []):
            if 'created_at' in rule:
                rule['created_at'] = datetime.fromisoformat(rule['created_at'])
        
        rule_set = RuleSet(**rule_data)
        
        enabled_rules = [r for r in rule_set.rules if r.enabled]
        console.print(f"✅ [green]Loaded {len(enabled_rules)} enabled rules from your file[/green]")
        
        return rule_set
        
    except Exception as e:
        console.print(f"❌ [red]Failed to load edited rules: {str(e)}[/red]")
        return None

def execute_validation_workflow(connector, rule_set: RuleSet, table_name: str):
    """Step 6: Execute validation rules and show results"""
    
    console.print(f"\n🚀 [bold green]Step 5: Executing Validation[/bold green]")
    
    # Filter enabled rules
    enabled_rules = [rule for rule in rule_set.rules if rule.enabled]
    
    if not enabled_rules:
        console.print("❌ [red]No enabled rules found to execute[/red]")
        return
    
    console.print(f"📊 Executing {len(enabled_rules)} validation rules...")
    
    try:
        # Import the new SQL validation engine
        from src.core.validation_engine import SQLValidationEngine
        from src.models.validation import SQLGenerationContext
        
        # Create SQL generation context
        context = SQLGenerationContext(
            database_type=rule_set.data_source.type,
            schema_name=None,  # Can be extended to support schema
            table_name=table_name,
            connection_info=rule_set.data_source.connection_params
        )
        
        # Initialize SQL validation engine
        sql_engine = SQLValidationEngine(context)
        
        # Generate and execute SQL for each rule
        validation_results = []
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            task = progress.add_task("Generating and executing SQL validation scripts...", total=len(enabled_rules))
            
            for rule in enabled_rules:
                try:
                    # Convert rule to dict format
                    rule_dict = {
                        'name': rule.name,
                        'rule_type': rule.rule_type.value,
                        'target_column': rule.target_column,
                        'parameters': rule.parameters
                    }
                    
                    # Generate SQL script
                    sql_script = sql_engine.generate_validation_sql(rule_dict)
                    
                    # Execute SQL and get results
                    if hasattr(connector, 'execute_query'):
                        # For database connectors
                        result_df = connector.execute_query(sql_script)
                        if not result_df.empty:
                            result_row = result_df.iloc[0]
                            validation_result = ValidationResult(
                                rule_name=rule.name,
                                rule_id=rule.id,
                                status="PASS" if result_row.get('status') == 'PASS' else "FAIL",
                                total_rows=int(result_row.get('total_rows', 0)),
                                failed_rows=int(result_row.get('failed_rows', 0)),
                                passed_rows=int(result_row.get('passed_rows', 0)),
                                generated_sql=sql_script,
                                details={'sql_result': result_row.to_dict()}
                            )
                        else:
                            validation_result = ValidationResult(
                                rule_name=rule.name,
                                rule_id=rule.id,
                                status="ERROR",
                                error_message="No results returned from SQL execution",
                                generated_sql=sql_script
                            )
                    else:
                        # For CSV connectors - show generated SQL only
                        validation_result = ValidationResult(
                            rule_name=rule.name,
                            rule_id=rule.id,
                            status="INFO",
                            error_message="SQL generated but not executed (CSV data source)",
                            generated_sql=sql_script,
                            details={'note': 'Use database connector to execute SQL'}
                        )
                    
                    validation_results.append(validation_result)
                    
                except Exception as rule_error:
                    console.print(f"❌ [red]Error processing rule '{rule.name}': {str(rule_error)}[/red]")
                    validation_results.append(ValidationResult(
                        rule_name=rule.name,
                        rule_id=rule.id,
                        status="ERROR",
                        error_message=str(rule_error)
                    ))
                
                progress.advance(task)
        
        # Display results
        display_sql_validation_results(validation_results)
        
        # Ask to save SQL scripts
        if Confirm.ask("Save generated SQL scripts to file?"):
            save_sql_scripts(validation_results, table_name)
        
    except Exception as e:
        console.print(f"❌ [red]Validation execution failed: {str(e)}[/red]")
        import traceback
        console.print(f"[red]Details: {traceback.format_exc()}[/red]")

def display_sql_validation_results(results: List[ValidationResult]):
    """Display SQL validation results with generated scripts"""
    console.print("\n📋 [bold blue]Validation Results[/bold blue]")
    
    for result in results:
        status_color = "green" if result.status == "PASS" else "red" if result.status == "FAIL" else "yellow"
        status_icon = "✅" if result.status == "PASS" else "❌" if result.status == "FAIL" else "⚠️"
        
        console.print(f"\n{status_icon} [bold]{result.rule_name}[/bold]")
        console.print(f"   Status: [{status_color}]{result.status}[/{status_color}]")
        
        if result.total_rows > 0:
            console.print(f"   Total Rows: {result.total_rows}")
            console.print(f"   Failed Rows: {result.failed_rows}")
            console.print(f"   Passed Rows: {result.passed_rows}")
        
        if result.error_message:
            console.print(f"   Error: [red]{result.error_message}[/red]")
        
        # Show generated SQL
        if result.generated_sql:
            console.print("   [bold cyan]Generated SQL:[/bold cyan]")
            # Create a panel with the SQL code
            sql_panel = Panel(
                Syntax(result.generated_sql, "sql", theme="monokai", line_numbers=True),
                title="SQL Script",
                border_style="cyan"
            )
            console.print(sql_panel)

def save_sql_scripts(results: List[ValidationResult], table_name: str):
    """Save generated SQL scripts to files"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Create outputs directory if it doesn't exist
    outputs_dir = Path("outputs")
    outputs_dir.mkdir(exist_ok=True)
    
    # Save individual SQL files
    for i, result in enumerate(results):
        if result.generated_sql:
            sql_filename = f"validation_sql_{table_name}_{result.rule_name.replace(' ', '_')}_{timestamp}.sql"
            sql_path = outputs_dir / sql_filename
            
            with open(sql_path, 'w') as f:
                f.write(f"-- Validation Rule: {result.rule_name}\n")
                f.write(f"-- Generated on: {datetime.now().isoformat()}\n")
                f.write(f"-- Table: {table_name}\n")
                f.write(f"-- Status: {result.status}\n\n")
                f.write(result.generated_sql)
            
            console.print(f"💾 SQL script saved: {sql_path}")
    
    # Save combined results JSON
    results_data = {
        'table_name': table_name,
        'generation_timestamp': timestamp,
        'total_rules': len(results),
        'results': [
            {
                'rule_name': r.rule_name,
                'status': r.status,
                'total_rows': r.total_rows,
                'failed_rows': r.failed_rows,
                'passed_rows': r.passed_rows,
                'error_message': r.error_message,
                'generated_sql': r.generated_sql
            }
            for r in results
        ]
    }
    
    json_filename = f"sql_validation_results_{table_name}_{timestamp}.json"
    json_path = outputs_dir / json_filename
    
    with open(json_path, 'w') as f:
        json.dump(results_data, f, indent=2, default=str)
    
    console.print(f"💾 Results saved: {json_path}")

if __name__ == "__main__":
    cli()