import boto3
import json
import uuid
from typing import Dict, Any, Optional, List
from botocore.exceptions import ClientError, NoCredentialsError
import structlog
from pathlib import Path

from ..config.settings import settings
from ..models.validation import RuleSet

logger = structlog.get_logger()

class S3RuleManager:
    """Manage rule storage and retrieval from AWS S3"""
    
    def __init__(self):
        try:
            self.s3_client = boto3.client(
                's3',
                region_name=settings.AWS_REGION,
                aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY
            )
            self.bucket_name = settings.AWS_S3_BUCKET
            self._ensure_bucket_exists()
        except NoCredentialsError:
            logger.error("AWS credentials not found. Please configure AWS credentials.")
            raise
        except Exception as e:
            logger.error(f"Failed to initialize S3 client: {str(e)}")
            raise
    
    def _ensure_bucket_exists(self):
        """Create S3 bucket if it doesn't exist"""
        try:
            self.s3_client.head_bucket(Bucket=self.bucket_name)
            logger.info(f"S3 bucket {self.bucket_name} exists")
        except ClientError as e:
            error_code = int(e.response['Error']['Code'])
            if error_code == 404:
                # Bucket doesn't exist, create it
                try:
                    if settings.AWS_REGION == 'us-east-1':
                        self.s3_client.create_bucket(Bucket=self.bucket_name)
                    else:
                        self.s3_client.create_bucket(
                            Bucket=self.bucket_name,
                            CreateBucketConfiguration={'LocationConstraint': settings.AWS_REGION}
                        )
                    logger.info(f"Created S3 bucket: {self.bucket_name}")
                except ClientError as create_error:
                    logger.error(f"Failed to create bucket: {str(create_error)}")
                    raise
            else:
                logger.error(f"Error accessing bucket: {str(e)}")
                raise
    
    def upload_rule_set(self, rule_set: RuleSet, file_name: Optional[str] = None) -> str:
        """Upload rule set to S3 and return the S3 key"""
        try:
            if not file_name:
                file_name = f"rules/{uuid.uuid4()}.json"
            
            # Convert rule set to JSON
            rule_data = rule_set.dict()
            rule_data['created_at'] = rule_data['created_at'].isoformat()
            for rule in rule_data['rules']:
                rule['created_at'] = rule['created_at'].isoformat()
            
            # Upload to S3
            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=file_name,
                Body=json.dumps(rule_data, indent=2),
                ContentType='application/json',
                Metadata={
                    'rule-set-name': rule_set.name,
                    'data-source-type': rule_set.data_source.type.value,
                    'rule-count': str(len(rule_set.rules))
                }
            )
            
            logger.info(f"Uploaded rule set to S3: {file_name}")
            return file_name
            
        except Exception as e:
            logger.error(f"Failed to upload rule set to S3: {str(e)}")
            raise
    
    def download_rule_set(self, s3_key: str) -> RuleSet:
        """Download rule set from S3"""
        try:
            response = self.s3_client.get_object(Bucket=self.bucket_name, Key=s3_key)
            rule_data = json.loads(response['Body'].read().decode('utf-8'))
            
            # Convert datetime strings back to datetime objects
            from datetime import datetime
            rule_data['created_at'] = datetime.fromisoformat(rule_data['created_at'])
            for rule in rule_data['rules']:
                rule['created_at'] = datetime.fromisoformat(rule['created_at'])
            
            return RuleSet(**rule_data)
            
        except Exception as e:
            logger.error(f"Failed to download rule set from S3: {str(e)}")
            raise
    
    def list_rule_sets(self) -> List[Dict[str, Any]]:
        """List all rule sets stored in S3"""
        try:
            response = self.s3_client.list_objects_v2(
                Bucket=self.bucket_name,
                Prefix='rules/'
            )
            
            rule_sets = []
            if 'Contents' in response:
                for obj in response['Contents']:
                    # Get object metadata
                    head_response = self.s3_client.head_object(
                        Bucket=self.bucket_name,
                        Key=obj['Key']
                    )
                    
                    metadata = head_response.get('Metadata', {})
                    rule_sets.append({
                        's3_key': obj['Key'],
                        'name': metadata.get('rule-set-name', 'Unknown'),
                        'data_source_type': metadata.get('data-source-type', 'Unknown'),
                        'rule_count': metadata.get('rule-count', '0'),
                        'last_modified': obj['LastModified'],
                        'size': obj['Size']
                    })
            
            return rule_sets
            
        except Exception as e:
            logger.error(f"Failed to list rule sets from S3: {str(e)}")
            raise
    
    def delete_rule_set(self, s3_key: str) -> bool:
        """Delete rule set from S3"""
        try:
            self.s3_client.delete_object(Bucket=self.bucket_name, Key=s3_key)
            logger.info(f"Deleted rule set from S3: {s3_key}")
            return True
        except Exception as e:
            logger.error(f"Failed to delete rule set from S3: {str(e)}")
            return False

class LambdaExecutor:
    """Execute validation rules using AWS Lambda for scalability"""
    
    def __init__(self):
        self.lambda_client = boto3.client(
            'lambda',
            region_name=settings.AWS_REGION,
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY
        )
        self.function_name = 'vp-engine-validator'
    
    def invoke_validation(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Invoke Lambda function for validation execution"""
        try:
            response = self.lambda_client.invoke(
                FunctionName=self.function_name,
                InvocationType='RequestResponse',
                Payload=json.dumps(payload)
            )
            
            result = json.loads(response['Payload'].read())
            return result
            
        except Exception as e:
            logger.error(f"Failed to invoke Lambda function: {str(e)}")
            raise
    
    def deploy_validation_function(self, zip_file_path: str) -> bool:
        """Deploy validation function to Lambda (for setup)"""
        try:
            with open(zip_file_path, 'rb') as zip_file:
                response = self.lambda_client.create_function(
                    FunctionName=self.function_name,
                    Runtime='python3.9',
                    Role='arn:aws:iam::your-account:role/lambda-execution-role',
                    Handler='lambda_function.lambda_handler',
                    Code={'ZipFile': zip_file.read()},
                    Description='VP Engine Data Validation Function',
                    Timeout=300,
                    MemorySize=512
                )
            
            logger.info(f"Deployed Lambda function: {self.function_name}")
            return True
            
        except ClientError as e:
            if e.response['Error']['Code'] == 'ResourceConflictException':
                # Function already exists, update it
                with open(zip_file_path, 'rb') as zip_file:
                    self.lambda_client.update_function_code(
                        FunctionName=self.function_name,
                        ZipFile=zip_file.read()
                    )
                logger.info(f"Updated Lambda function: {self.function_name}")
                return True
            else:
                logger.error(f"Failed to deploy Lambda function: {str(e)}")
                return False