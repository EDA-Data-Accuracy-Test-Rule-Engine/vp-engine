import click
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.prompt import Prompt, Confirm
from rich.progress import Progress, SpinnerColumn, TextColumn
from pathlib import Path
import json
import os
import subprocess
from typing import Dict, Any, List, Optional

from ..config.settings import settings
from ..models.validation import (
    DataSourceType, DataSourceConfig, ValidationRule, RuleSet, 
    RuleType, ColumnInfo
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
    
    # Step 3: Show tables and columns
    table_name = select_table_and_show_columns(connector, data_source_config)
    if not table_name:
        console.print("❌ [red]No table selected. Exiting...[/red]")
        return
    
    # Step 4: User action selection
    action = select_user_action()
    
    # Step 5: Execute based on user choice
    rule_set = None
    if action == "1":  # AI suggestion
        rule_set = handle_ai_suggestion(connector, data_source_config, table_name)
    elif action == "2":  # Use existing rules
        rule_set = handle_existing_rules(data_source_config, table_name)
    elif action == "3":  # Create new rules
        rule_set = handle_create_new_rules(data_source_config, table_name)
    
    if not rule_set:
        console.print("❌ [red]No rules were created or selected. Exiting...[/red]")
        return
    
    # Step 6: Execute validation
    execute_validation_workflow(connector, rule_set, table_name)

def select_data_source() -> Optional[DataSourceConfig]:
    """Step 1: Let user select data source type"""
    
    console.print("📊 [bold cyan]Step 1: Select Data Source[/bold cyan]")
    console.print("Choose your data source type:")
    console.print("  1. PostgreSQL Database")
    console.print("  2. MySQL Database") 
    console.print("  3. CSV File")
    
    choice = Prompt.ask("\nEnter your choice", choices=["1", "2", "3"])
    
    if choice == "1":
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

def select_table_and_show_columns(connector, config: DataSourceConfig) -> Optional[str]:
    """Step 3: Show tables and let user select, then show columns"""
    
    console.print(f"\n📋 [bold cyan]Step 3: Available Tables and Columns[/bold cyan]")
    
    try:
        # Get tables
        tables = connector.get_tables()
        
        if not tables:
            console.print("❌ [red]No tables found in the data source[/red]")
            return None
        
        if len(tables) == 1:
            table_name = tables[0]
            console.print(f"📊 Found table: [bold]{table_name}[/bold]")
        else:
            console.print("Available tables:")
            for i, table in enumerate(tables, 1):
                console.print(f"  {i}. {table}")
            
            while True:
                try:
                    choice = int(Prompt.ask(f"\nSelect table (1-{len(tables)})"))
                    if 1 <= choice <= len(tables):
                        table_name = tables[choice - 1]
                        break
                    else:
                        console.print(f"❌ [red]Please enter a number between 1 and {len(tables)}[/red]")
                except ValueError:
                    console.print("❌ [red]Please enter a valid number[/red]")
        
        # Show columns
        with console.status(f"Analyzing columns in {table_name}..."):
            columns = connector.get_columns(table_name)
        
        if columns:
            display_column_info(columns)
        else:
            console.print("❌ [red]Could not retrieve column information[/red]")
        
        return table_name
        
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
    
    return Prompt.ask("\nEnter your choice", choices=["1", "2", "3"])

def handle_ai_suggestion(connector, config: DataSourceConfig, table_name: str) -> Optional[RuleSet]:
    """Handle AI rule suggestion workflow"""
    
    console.print(f"\n🤖 [bold magenta]AI Rule Suggestion[/bold magenta]")
    console.print("Analyzing your data to suggest validation rules...")
    
    try:
        # Get column information and sample data
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
        
        # Get AI suggestions
        with console.status("Getting AI recommendations..."):
            suggestions = ai_engine.suggest_rules_for_dataset(columns, sample_data)
        
        # Display suggestions
        if suggestions:
            console.print(f"\n📋 [bold green]AI suggested {len(suggestions)} validation rules:[/bold green]")
            
            all_rules = []
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
            
            # Save suggestions to JSON file
            suggested_file = f"templates/ai_suggestions_{table_name}.json"
            Path("templates").mkdir(exist_ok=True)
            
            rule_set = RuleSet(
                name=f"AI Suggested Rules for {table_name}",
                description="Rules generated by AI analysis",
                data_source=config,
                rules=all_rules
            )
            
            with open(suggested_file, 'w') as f:
                rule_data = rule_set.dict()
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
            
            console.print(f"  {i}. {file_path.name} - {name} ({rule_count} rules)")
        except Exception:
            console.print(f"  {i}. {file_path.name} - [red](Invalid file)[/red]")
    
    # Let user select
    while True:
        try:
            choice = int(Prompt.ask(f"\nSelect rule file (1-{len(rule_files)})"))
            if 1 <= choice <= len(rule_files):
                selected_file = rule_files[choice - 1]
                break
            else:
                console.print(f"❌ [red]Please enter a number between 1 and {len(rule_files)}[/red]")
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
    
    # Get rule set name
    rule_set_name = Prompt.ask("Enter a name for your rule set", default=f"Rules for {table_name}")
    
    # Create safe filename
    import re
    safe_name = re.sub(r'[^a-zA-Z0-9_-]', '_', rule_set_name.lower())
    template_file = f"templates/{safe_name}.json"
    
    # Create template structure
    template_rule_set = RuleSet(
        name=rule_set_name,
        description=f"Custom validation rules for {table_name}",
        data_source=config,
        rules=[
            # Example rule
            ValidationRule(
                name="Example Null Check",
                description="Example rule - replace with your own",
                rule_type=RuleType.NULL_CHECK,
                target_column="your_column_name",
                parameters={},
                enabled=False  # Disabled by default
            )
        ]
    )
    
    # Save template file
    Path("templates").mkdir(exist_ok=True)
    
    with open(template_file, 'w') as f:
        rule_data = template_rule_set.dict()
        rule_data['created_at'] = rule_data['created_at'].isoformat()
        for rule in rule_data['rules']:
            rule['created_at'] = rule['created_at'].isoformat()
        json.dump(rule_data, f, indent=2)
    
    console.print(f"📁 [green]Created template file: {template_file}[/green]")
    console.print("\n📝 [yellow]Please edit this file to define your validation rules.[/yellow]")
    console.print("\n🔧 [cyan]Rule types available:[/cyan]")
    console.print("  • null_check - Check for null values")
    console.print("  • range_check - Check numeric ranges") 
    console.print("  • regex_check - Check string patterns")
    console.print("  • duplicate_check - Check for duplicates")
    console.print("  • uniqueness_check - Check uniqueness")
    
    console.print(f"\n📖 [blue]Example file path: {Path(template_file).absolute()}[/blue]")
    
    if Confirm.ask("Open the file in your default editor?"):
        try:
            if os.name == 'nt':  # Windows
                os.startfile(template_file)
            elif os.name == 'posix':  # macOS and Linux
                subprocess.call(['open', template_file])
        except Exception as e:
            console.print(f"❌ [red]Could not open file automatically: {str(e)}[/red]")
    
    input("\n⏸️  Press Enter when you have finished editing the file...")
    
    # Ask for S3 upload
    if Confirm.ask("Upload rules to AWS S3 for backup?"):
        try:
            s3_manager = S3RuleManager()
            
            # Reload the edited file
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
    
    # Load and return the edited rules
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
    
    # Execute validation using DataFrame approach
    try:
        # Get data as DataFrame
        with console.status("Loading data..."):
            df = connector.get_sample_data(table_name, limit=10000)  # Load more data for validation
        
        # Initialize validation engine
        validation_engine = ValidationEngine()
        
        # Convert rules to the format expected by ValidationEngine
        rules_dict = {
            "rules": {}
        }
        
        for rule in enabled_rules:
            rule_config = {
                "type": rule.rule_type.value.lower(),
                "column": rule.target_column,
                **rule.parameters
            }
            
            # Map our rule types to validation engine types
            if rule.rule_type == RuleType.NULL_CHECK:
                rule_config["type"] = "not_null"
            elif rule.rule_type == RuleType.RANGE_CHECK:
                rule_config["type"] = "range"
            elif rule.rule_type == RuleType.REGEX_CHECK:
                rule_config["type"] = "format"
                if "pattern" not in rule_config:
                    rule_config["pattern"] = rule.parameters.get("regex_pattern", ".*")
            elif rule.rule_type == RuleType.DUPLICATE_CHECK:
                rule_config["type"] = "unique"
            elif rule.rule_type == RuleType.ENUM_CHECK:
                rule_config["type"] = "enum"
            
            rules_dict["rules"][rule.name] = rule_config
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            task = progress.add_task("Validating data...", total=1)
            
            # Execute validation
            summary = validation_engine.validate_dataframe(df, rules_dict)
            progress.advance(task)
        
        # Display results
        display_validation_results_simple(summary.results)
        
        # Generate and display summary
        display_validation_summary_simple(summary)
        
        # Ask to save results
        if Confirm.ask("Save results to file?"):
            save_validation_results_simple(summary, table_name)
        
    except Exception as e:
        console.print(f"❌ [red]Validation execution failed: {str(e)}[/red]")
        import traceback
        console.print(f"[red]Details: {traceback.format_exc()}[/red]")

def display_validation_results_simple(results):
    """Display validation results in a nice table"""
    
    table = Table(title="🎯 Validation Results")
    table.add_column("Rule Name", style="cyan", width=25)
    table.add_column("Status", style="bold", width=8)
    table.add_column("Total Rows", style="magenta", justify="right")
    table.add_column("Failed", style="red", justify="right")
    table.add_column("Details", style="dim", width=30)
    
    for result in results:
        # Status with emoji
        if result.status.value == "passed":
            status = "✅ PASS"
        elif result.status.value == "failed":
            status = "❌ FAIL"
        else:
            status = "🚨 WARN"
        
        # Details
        details = result.message[:30] + "..." if len(result.message) > 30 else result.message
        
        table.add_row(
            result.rule_name,
            status,
            str(result.total_count),
            str(result.failed_count),
            details
        )
    
    console.print(table)

def display_validation_summary_simple(summary):
    """Display validation summary"""
    
    total_rules = summary.total_rules
    passed_rules = summary.passed_rules
    failed_rules = summary.failed_rules
    warning_rules = summary.warning_rules
    
    success_rate = (passed_rules / total_rules * 100) if total_rules > 0 else 0
    
    summary_panel = f"""
[bold]Validation Summary[/bold]
⏱️  Total rules executed: {total_rules}
✅ Passed: {passed_rules}
❌ Failed: {failed_rules}
⚠️  Warnings: {warning_rules}
📈 Success rate: {success_rate:.1f}%
    """
    
    console.print(Panel(summary_panel, title="🎯 Summary", border_style="green"))

def save_validation_results_simple(summary, table_name: str):
    """Save validation results to file"""
    
    from datetime import datetime
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = f"outputs/validation_results_{table_name}_{timestamp}.json"
    
    Path("outputs").mkdir(exist_ok=True)
    
    output_data = {
        "table_name": table_name,
        "execution_timestamp": datetime.now().isoformat(),
        "summary": {
            "total_rules": summary.total_rules,
            "passed_rules": summary.passed_rules,
            "failed_rules": summary.failed_rules,
            "warning_rules": summary.warning_rules
        },
        "detailed_results": [
            {
                "rule_name": r.rule_name,
                "status": r.status.value,
                "total_count": r.total_count,
                "failed_count": r.failed_count,
                "message": r.message,
                "details": r.details
            }
            for r in summary.results
        ]
    }
    
    with open(output_file, 'w') as f:
        json.dump(output_data, f, indent=2, default=str)
    
    console.print(f"💾 [green]Results saved to: {output_file}[/green]")

if __name__ == "__main__":
    cli()