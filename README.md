# 🚀 VP Data Accuracy Test Rule Engine

## 📋 Tổng quan

VP Data Accuracy Test Rule Engine là một hệ thống tương tác mạnh mẽ cho việc kiểm tra chất lượng dữ liệu với các tính năng:

- ✅ **Hỗ trợ đa nguồn dữ liệu**: PostgreSQL, MySQL, CSV
- 🤖 **Gợi ý quy tắc bằng AI**: Sử dụng OpenAI để phân tích và đề xuất rules
- 📚 **Quản lý templates**: Tạo và tái sử dụng rule templates
- ☁️ **Tích hợp AWS**: Lưu trữ rules trên S3, thực thi qua Lambda
- 📊 **Báo cáo chi tiết**: Kết quả validation với visualizations
- 🎯 **Giao diện thân thiện**: Interactive CLI với Rich UI

## 🏗️ Kiến trúc hệ thống

```
VP Engine
├── CLI Interface (Rich UI)
├── AI Rule Engine (OpenAI/Anthropic)
├── Database Connectors (PostgreSQL/MySQL/CSV)
├── Validation Engine (Generate parameterized SQL scripts)
├── AWS Services (S3/Lambda)
└── Rule Management System
```

## 🎯 Quy trình sử dụng

### 1. **Lựa chọn nguồn dữ liệu**
- PostgreSQL Database
- MySQL Database  
- CSV File

### 2. **Lựa chọn hành động**
- 🤖 **Gợi ý quy tắc bằng AI**: AI phân tích dữ liệu và đề xuất rules
- 📚 **Sử dụng quy tắc có sẵn**: Chọn từ templates đã tạo
- ✏️ **Tạo quy tắc mới**: Tự định nghĩa rules và lưu lên S3

### 3. **Thực thi và hiển thị kết quả**
- Chạy validation rules
- Hiển thị báo cáo chi tiết
- Xuất kết quả ra file

## 🚀 Cài đặt nhanh

### Tự động (Khuyến nghị)
```bash
git clone <repository>
cd vp-engine
chmod +x setup.sh
./setup.sh
```

### Thủ công
```bash
# Tạo virtual environment
python3 -m venv venv
source venv/bin/activate

# Cài đặt dependencies
pip install -r requirements.txt
pip install -e .

# Tạo directories
mkdir -p {data,outputs,templates,config}

# Copy environment config
cp .env.example .env

# Tạo demo data
python scripts/create_demo_data.py
```

## ⚙️ Cấu hình

### 1. Environment Variables (.env)
```bash
# AWS Configuration (Optional)
AWS_REGION=ap-southeast-1
AWS_ACCESS_KEY_ID=your_aws_access_key
AWS_SECRET_ACCESS_KEY=your_aws_secret_key
AWS_S3_BUCKET=vp-engine-rules-bucket

# Database Configuration
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_USER=your_username
POSTGRES_PASSWORD=your_password
POSTGRES_DB=your_database

MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_USER=your_username
MYSQL_PASSWORD=your_password
MYSQL_DB=your_database

# AI Configuration (Optional)
OPENAI_API_KEY=your_openai_api_key
ANTHROPIC_API_KEY=your_anthropic_api_key
```

## 🎪 Demo nhanh

```bash
# Bắt đầu workflow tương tác
vp-engine start

# Workflow demo:
# 1. Chọn "3. CSV File"
# 2. Nhập path: data/sample_employees.csv
# 3. Thử AI suggestions hoặc existing rules
# 4. Xem kết quả validation
```

## 📚 Các loại validation rules

### 1. **Null Check**
```json
{
  "rule_type": "null_check",
  "target_column": "email",
  "parameters": {}
}
```

### 2. **Range Check**
```json
{
  "rule_type": "range_check", 
  "target_column": "age",
  "parameters": {
    "min_value": 18,
    "max_value": 100
  }
}
```

### 3. **Regex Check**
```json
{
  "rule_type": "regex_check",
  "target_column": "email",
  "parameters": {
    "pattern": "^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}$"
  }
}
```

### 4. **Duplicate Check**
```json
{
  "rule_type": "duplicate_check",
  "target_column": "email",
  "parameters": {}
}
```

### 5. **Uniqueness Check**
```json
{
  "rule_type": "uniqueness_check",
  "target_column": "user_id", 
  "parameters": {}
}
```

## 🤖 AI Rule Suggestions

Hệ thống sử dụng OpenAI để:
- Phân tích cấu trúc dữ liệu
- Nhận diện patterns và anomalies
- Đề xuất validation rules phù hợp
- Cung cấp confidence scores

```python
# Ví dụ AI suggestion
{
  "column_name": "email",
  "suggested_rules": [
    {
      "name": "Email Format Validation",
      "rule_type": "regex_check",
      "confidence": 0.95,
      "reasoning": "Column contains email-like strings"
    }
  ]
}
```

## ☁️ AWS Integration

### S3 Rule Storage
- Tự động backup rules lên S3
- Versioning và metadata tracking
- Cross-team rule sharing

### Lambda Execution (Tương lai)
- Scalable validation execution
- Scheduled data quality checks
- Integration với data pipelines

## 📊 Output formats

### Console Display
- Rich tables với color coding
- Progress bars và spinners
- Interactive prompts

### JSON Reports
```json
{
  "summary": {
    "total_rules": 6,
    "passed_rules": 4,
    "failed_rules": 2,
    "success_rate": 66.7,
    "data_quality_score": 89.5
  },
  "detailed_results": [...]
}
```

## 🔧 Development

### Project Structure
```
src/
├── cli/main.py           # CLI interface
├── ai/rule_engine.py     # AI suggestions  
├── aws/services.py       # AWS integration
├── core/validation_engine.py  # Core engine
├── database/connectors.py     # DB connectors
└── models/validation.py       # Data models
```

### Testing
```bash
pytest tests/
```

### Adding New Rule Types
1. Extend `RuleType` enum in `models/validation.py`
2. Add SQL generation logic in `validation_engine.py`
3. Update CLI interface if needed

## 🎯 Use Cases

### 1. **Data Migration Validation**
- Validate data integrity sau khi migration
- So sánh source vs target data quality

### 2. **ETL Pipeline Quality Gates**
- Integration vào CI/CD pipelines
- Automated data quality checks

### 3. **Regulatory Compliance**
- GDPR data quality requirements
- Financial data accuracy standards

### 4. **Data Discovery**
- Profile unknown datasets
- Generate documentation tự động

## 🚨 Troubleshooting

### Database Connection Issues
```bash
# Test PostgreSQL connection
psql -h localhost -U username -d database

# Test MySQL connection  
mysql -h localhost -u username -p database
```

### AWS Configuration
```bash
# Test AWS credentials
aws sts get-caller-identity

# Check S3 bucket access
aws s3 ls s3://your-bucket-name
```

### AI API Issues
- Verify OpenAI API key
- Check API rate limits
- Fallback to rule-based suggestions

## 📈 Roadmap

- [ ] Web UI interface
- [ ] Real-time streaming validation
- [ ] Custom rule engine DSL
- [ ] ML-based anomaly detection
- [ ] Multi-language support
- [ ] Enterprise SSO integration

## 🤝 Contributing

1. Fork repository
2. Create feature branch
3. Add tests
4. Submit pull request

## 📜 License

MIT License - xem file LICENSE để biết chi tiết.

## 📞 Support

- 📧 Email: tech@vpbank.com.vn
- 📖 Documentation: [Wiki link]
- 🐛 Issues: [GitHub Issues]