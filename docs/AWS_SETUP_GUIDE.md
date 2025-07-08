# 🔧 AWS Configuration Guide

## Step 1: Tạo IAM User
1. Đăng nhập AWS Console: https://console.aws.amazon.com
2. Tìm kiếm "IAM" → Vào IAM Dashboard
3. Click "Users" → "Create user"
4. Nhập username: vp-engine-user
5. Check "Programmatic access"
6. Click "Next: Permissions"

## Step 2: Gán Permissions
1. Chọn "Attach existing policies directly"
2. Tìm và check các policies sau:
   - AmazonS3FullAccess
   - AWSLambdaFullAccess (optional)
   - IAMReadOnlyAccess (optional)
3. Click "Next" → "Create user"

## Step 3: Download Credentials
1. Tại màn hình success, click "Download .csv"
2. Lưu file này an toàn (chứa Access Key và Secret Key)
3. Copy thông tin vào .env file

## Step 4: Tạo S3 Bucket
1. Tìm kiếm "S3" trong AWS Console
2. Click "Create bucket"
3. Bucket name: vp-engine-rules-bucket-{random-string}
   Ví dụ: vp-engine-rules-bucket-2025
4. Region: ap-southeast-1 (Singapore)
5. Để default settings → Create bucket

## Step 5: Cập nhật .env file
```bash
# Copy thông tin từ CSV file và S3 bucket
AWS_REGION=ap-southeast-1
AWS_ACCESS_KEY_ID=AKIA...  # Từ CSV file
AWS_SECRET_ACCESS_KEY=xxx... # Từ CSV file  
AWS_S3_BUCKET=vp-engine-rules-bucket-2025 # Tên bucket vừa tạo
```

## Step 6: Test Connection
```bash
# Sau khi setup
source venv/bin/activate
python -c "
import boto3
from src.config.settings import settings
print('Testing AWS connection...')
s3 = boto3.client('s3', region_name=settings.AWS_REGION)
print('✅ AWS S3 connection successful!')
"
```

## ⚠️ Security Best Practices
- Không commit .env file vào git
- Sử dụng IAM roles trong production
- Rotate access keys định kỳ
- Chỉ gán minimum permissions cần thiết

## 💡 Alternative: Chạy mà không cần AWS
Nếu không muốn setup AWS ngay:
1. Comment out AWS-related code trong .env
2. Hệ thống vẫn hoạt động bình thường với local file storage
3. Chỉ mất tính năng backup rules lên S3