import pandas as pd
import numpy as np
from faker import Faker
from pathlib import Path
import random

fake = Faker()

def create_sample_csv():
    """Create a sample CSV file with intentional data quality issues for demo"""
    
    # Ensure data directory exists
    Path("data").mkdir(exist_ok=True)
    
    print("🔧 Creating sample CSV data with intentional quality issues...")
    
    # Generate sample data
    data = []
    for i in range(1000):
        # Introduce various data quality issues
        
        # 5% null names
        name = fake.name() if random.random() > 0.05 else None
        
        # 10% invalid email formats
        if random.random() > 0.1:
            email = fake.email()
        else:
            email = fake.first_name().lower() + "@invalid"  # Invalid email
        
        # 3% invalid ages (negative or too high)
        if random.random() > 0.03:
            age = fake.random_int(min=18, max=90)
        else:
            age = fake.random_int(min=-5, max=200)  # Invalid age
        
        # 8% invalid phone numbers
        if random.random() > 0.08:
            phone = fake.phone_number()
        else:
            phone = "123"  # Invalid phone
        
        # 2% null salaries
        salary = round(fake.random_int(min=30000, max=150000), -3) if random.random() > 0.02 else None
        
        # 5% invalid departments
        if random.random() > 0.05:
            department = random.choice(['Engineering', 'Marketing', 'Sales', 'HR', 'Finance'])
        else:
            department = "InvalidDept"
        
        # Registration date with some invalid dates
        if random.random() > 0.02:
            registration_date = fake.date_between(start_date='-2y', end_date='today')
        else:
            registration_date = "2025-13-35"  # Invalid date
        
        # 1% completely duplicate records
        if random.random() < 0.01 and i > 0:
            # Use previous record's email (duplicate)
            email = data[-1][1]
        
        data.append([
            i + 1,  # id
            email,
            name,
            age,
            phone,
            salary,
            department,
            registration_date
        ])
    
    # Create DataFrame
    df = pd.DataFrame(data, columns=[
        'employee_id', 'email', 'full_name', 'age', 'phone', 
        'salary', 'department', 'registration_date'
    ])
    
    # Save to CSV
    csv_file = "data/sample_employees.csv"
    df.to_csv(csv_file, index=False)
    
    print(f"✅ Sample CSV created: {csv_file}")
    print(f"📊 Generated {len(df)} employee records with intentional data quality issues")
    print("📋 Issues included:")
    print("   • Null values in names and salaries")
    print("   • Invalid email formats")
    print("   • Out-of-range ages")
    print("   • Invalid phone numbers")
    print("   • Duplicate email addresses")
    print("   • Invalid department names")
    print("   • Invalid date formats")
    
    return csv_file

if __name__ == "__main__":
    create_sample_csv()