"""
AWS Setup Script for StyleLane
This script helps set up AWS resources (DynamoDB tables, SNS topic, IAM policies)
Run this before deploying app_aws.py

IMPORTANT: You need AWS credentials to run this script.
If you don't have credentials yet, this script will show you what needs to be configured.
"""
import boto3
import json
import os
from botocore.exceptions import ClientError, NoCredentialsError

AWS_REGION = "us-east-1"

# DynamoDB table names
TABLES = {
    "users": "stylelane-users",
    "stores": "stylelane-stores",
    "products": "stylelane-products",
    "inventory": "stylelane-inventory",
    "sales": "stylelane-sales",
    "restock_requests": "stylelane-restock-requests",
    "shipments": "stylelane-shipments",
}

SNS_TOPIC_NAME = "stylelane-notifications"


def check_aws_credentials():
    """Check if AWS credentials are configured"""
    try:
        # Try to get AWS account ID (requires valid credentials)
        sts_client = boto3.client("sts", region_name=AWS_REGION)
        identity = sts_client.get_caller_identity()
        account_id = identity.get("Account")
        print(f"✓ AWS credentials found")
        print(f"  Account ID: {account_id}")
        print(f"  Region: {AWS_REGION}")
        return True, account_id
    except NoCredentialsError:
        print("✗ AWS credentials not found!")
        print("\nTo configure AWS credentials:")
        print("  1. Get credentials from your mentor:")
        print("     - AWS Access Key ID")
        print("     - AWS Secret Access Key")
        print("  2. Run: aws configure")
        print("     Or set environment variables:")
        print("     export AWS_ACCESS_KEY_ID='your-key'")
        print("     export AWS_SECRET_ACCESS_KEY='your-secret'")
        print("     export AWS_DEFAULT_REGION='us-east-1'")
        print("\n  3. Or create a .env file with:")
        print("     AWS_ACCESS_KEY_ID=your-key")
        print("     AWS_SECRET_ACCESS_KEY=your-secret")
        print("     AWS_REGION=us-east-1")
        return False, None
    except ClientError as e:
        print(f"✗ Error with AWS credentials: {e}")
        print("  Please check your credentials and permissions.")
        return False, None


def create_dynamodb_tables():
    """Create all DynamoDB tables"""
    dynamodb = boto3.resource("dynamodb", region_name=AWS_REGION)
    dynamodb_client = boto3.client("dynamodb", region_name=AWS_REGION)
    
    print("\nCreating DynamoDB tables...")
    
    # Users table with GSI for username lookup
    try:
        table = dynamodb.create_table(
            TableName=TABLES["users"],
            KeySchema=[{"AttributeName": "id", "KeyType": "HASH"}],
            AttributeDefinitions=[
                {"AttributeName": "id", "AttributeType": "S"},
                {"AttributeName": "username", "AttributeType": "S"},
            ],
            GlobalSecondaryIndexes=[{
                "IndexName": "username-index",
                "KeySchema": [{"AttributeName": "username", "KeyType": "HASH"}],
                "Projection": {"ProjectionType": "ALL"},
            }],
            BillingMode="PAY_PER_REQUEST",
        )
        table.wait_until_exists()
        print(f"✓ Created table: {TABLES['users']}")
    except ClientError as e:
        if e.response["Error"]["Code"] == "ResourceInUseException":
            print(f"  Table {TABLES['users']} already exists")
        else:
            print(f"  Error creating {TABLES['users']}: {e}")
    
    # Stores table
    try:
        table = dynamodb.create_table(
            TableName=TABLES["stores"],
            KeySchema=[{"AttributeName": "id", "KeyType": "HASH"}],
            AttributeDefinitions=[{"AttributeName": "id", "AttributeType": "S"}],
            BillingMode="PAY_PER_REQUEST",
        )
        table.wait_until_exists()
        print(f"✓ Created table: {TABLES['stores']}")
    except ClientError as e:
        if e.response["Error"]["Code"] == "ResourceInUseException":
            print(f"  Table {TABLES['stores']} already exists")
        else:
            print(f"  Error creating {TABLES['stores']}: {e}")
    
    # Products table with GSI for SKU lookup
    try:
        table = dynamodb.create_table(
            TableName=TABLES["products"],
            KeySchema=[{"AttributeName": "id", "KeyType": "HASH"}],
            AttributeDefinitions=[
                {"AttributeName": "id", "AttributeType": "S"},
                {"AttributeName": "sku", "AttributeType": "S"},
            ],
            GlobalSecondaryIndexes=[{
                "IndexName": "sku-index",
                "KeySchema": [{"AttributeName": "sku", "KeyType": "HASH"}],
                "Projection": {"ProjectionType": "ALL"},
            }],
            BillingMode="PAY_PER_REQUEST",
        )
        table.wait_until_exists()
        print(f"✓ Created table: {TABLES['products']}")
    except ClientError as e:
        if e.response["Error"]["Code"] == "ResourceInUseException":
            print(f"  Table {TABLES['products']} already exists")
        else:
            print(f"  Error creating {TABLES['products']}: {e}")
    
    # Inventory table
    try:
        table = dynamodb.create_table(
            TableName=TABLES["inventory"],
            KeySchema=[{"AttributeName": "id", "KeyType": "HASH"}],
            AttributeDefinitions=[{"AttributeName": "id", "AttributeType": "S"}],
            BillingMode="PAY_PER_REQUEST",
        )
        table.wait_until_exists()
        print(f"✓ Created table: {TABLES['inventory']}")
    except ClientError as e:
        if e.response["Error"]["Code"] == "ResourceInUseException":
            print(f"  Table {TABLES['inventory']} already exists")
        else:
            print(f"  Error creating {TABLES['inventory']}: {e}")
    
    # Sales table
    try:
        table = dynamodb.create_table(
            TableName=TABLES["sales"],
            KeySchema=[{"AttributeName": "id", "KeyType": "HASH"}],
            AttributeDefinitions=[{"AttributeName": "id", "AttributeType": "S"}],
            BillingMode="PAY_PER_REQUEST",
        )
        table.wait_until_exists()
        print(f"✓ Created table: {TABLES['sales']}")
    except ClientError as e:
        if e.response["Error"]["Code"] == "ResourceInUseException":
            print(f"  Table {TABLES['sales']} already exists")
        else:
            print(f"  Error creating {TABLES['sales']}: {e}")
    
    # Restock Requests table
    try:
        table = dynamodb.create_table(
            TableName=TABLES["restock_requests"],
            KeySchema=[{"AttributeName": "id", "KeyType": "HASH"}],
            AttributeDefinitions=[{"AttributeName": "id", "AttributeType": "S"}],
            BillingMode="PAY_PER_REQUEST",
        )
        table.wait_until_exists()
        print(f"✓ Created table: {TABLES['restock_requests']}")
    except ClientError as e:
        if e.response["Error"]["Code"] == "ResourceInUseException":
            print(f"  Table {TABLES['restock_requests']} already exists")
        else:
            print(f"  Error creating {TABLES['restock_requests']}: {e}")
    
    # Shipments table
    try:
        table = dynamodb.create_table(
            TableName=TABLES["shipments"],
            KeySchema=[{"AttributeName": "id", "KeyType": "HASH"}],
            AttributeDefinitions=[{"AttributeName": "id", "AttributeType": "S"}],
            BillingMode="PAY_PER_REQUEST",
        )
        table.wait_until_exists()
        print(f"✓ Created table: {TABLES['shipments']}")
    except ClientError as e:
        if e.response["Error"]["Code"] == "ResourceInUseException":
            print(f"  Table {TABLES['shipments']} already exists")
        else:
            print(f"  Error creating {TABLES['shipments']}: {e}")


def create_sns_topic():
    """Create SNS topic for notifications"""
    sns_client = boto3.client("sns", region_name=AWS_REGION)
    
    print("\nCreating SNS topic...")
    try:
        response = sns_client.create_topic(Name=SNS_TOPIC_NAME)
        topic_arn = response["TopicArn"]
        print(f"✓ Created SNS topic: {topic_arn}")
        print(f"\n⚠️  IMPORTANT: Copy this SNS Topic ARN and paste it in:")
        print(f"   1. .env file: SNS_TOPIC_ARN='{topic_arn}'")
        print(f"   2. app_aws.py environment variable")
        print(f"   3. EC2 instance environment variables when deploying")
        return topic_arn
    except ClientError as e:
        if e.response["Error"]["Code"] == "InvalidParameter":
            # Topic might already exist, try to get it
            try:
                response = sns_client.list_topics()
                for topic in response.get("Topics", []):
                    if SNS_TOPIC_NAME in topic["TopicArn"]:
                        print(f"✓ SNS topic already exists: {topic['TopicArn']}")
                        print(f"\n⚠️  Use this SNS Topic ARN:")
                        print(f"   SNS_TOPIC_ARN='{topic['TopicArn']}'")
                        return topic["TopicArn"]
            except:
                pass
        print(f"  Error creating SNS topic: {e}")
        return None


def create_iam_policy():
    """Create IAM policy document for the application"""
    policy_document = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Action": [
                    "dynamodb:PutItem",
                    "dynamodb:GetItem",
                    "dynamodb:UpdateItem",
                    "dynamodb:DeleteItem",
                    "dynamodb:Query",
                    "dynamodb:Scan",
                ],
                "Resource": [
                    f"arn:aws:dynamodb:{AWS_REGION}:*:table/stylelane-*",
                    f"arn:aws:dynamodb:{AWS_REGION}:*:table/stylelane-*/index/*",
                ],
            },
            {
                "Effect": "Allow",
                "Action": [
                    "sns:Publish",
                ],
                "Resource": f"arn:aws:sns:{AWS_REGION}:*:stylelane-*",
            },
        ],
    }
    
    policy_file = "stylelane-iam-policy.json"
    with open(policy_file, "w") as f:
        json.dump(policy_document, f, indent=2)
    
    print(f"\n✓ Created IAM policy document: {policy_file}")
    print(f"\n⚠️  Next steps:")
    print(f"   1. Go to AWS IAM Console")
    print(f"   2. Create a new IAM role or user")
    print(f"   3. Attach this policy file: {policy_file}")
    print(f"   4. Attach this role to your EC2 instance")


def show_configuration_instructions():
    """Show instructions for configuring AWS credentials"""
    print("\n" + "=" * 60)
    print("AWS CREDENTIALS CONFIGURATION INSTRUCTIONS")
    print("=" * 60)
    print("\nWhen you receive credentials from your mentor, configure them using ONE of these methods:")
    print("\nMETHOD 1: Using AWS CLI (Recommended)")
    print("  Run: aws configure")
    print("  Enter:")
    print("    AWS Access Key ID: [paste from mentor]")
    print("    AWS Secret Access Key: [paste from mentor]")
    print("    Default region: us-east-1")
    print("    Default output format: json")
    print("\nMETHOD 2: Environment Variables")
    print("  Windows PowerShell:")
    print("    $env:AWS_ACCESS_KEY_ID='your-key-here'")
    print("    $env:AWS_SECRET_ACCESS_KEY='your-secret-here'")
    print("    $env:AWS_DEFAULT_REGION='us-east-1'")
    print("\n  Windows CMD:")
    print("    set AWS_ACCESS_KEY_ID=your-key-here")
    print("    set AWS_SECRET_ACCESS_KEY=your-secret-here")
    print("    set AWS_DEFAULT_REGION=us-east-1")
    print("\n  Linux/Mac:")
    print("    export AWS_ACCESS_KEY_ID='your-key-here'")
    print("    export AWS_SECRET_ACCESS_KEY='your-secret-here'")
    print("    export AWS_DEFAULT_REGION='us-east-1'")
    print("\nMETHOD 3: Create .env file")
    print("  1. Copy aws_config_template.env to .env")
    print("  2. Edit .env and paste your credentials:")
    print("     AWS_ACCESS_KEY_ID=your-key-here")
    print("     AWS_SECRET_ACCESS_KEY=your-secret-here")
    print("  3. Load in Python: from dotenv import load_dotenv; load_dotenv()")
    print("\n" + "=" * 60)


def main():
    """Main setup function"""
    print("=" * 60)
    print("StyleLane AWS Setup")
    print("=" * 60)
    print(f"\nRegion: {AWS_REGION}")
    print("\nThis script will create:")
    print("  - DynamoDB tables (7 tables)")
    print("  - SNS topic for notifications")
    print("  - IAM policy document")
    
    # Check credentials first
    has_credentials, account_id = check_aws_credentials()
    
    if not has_credentials:
        show_configuration_instructions()
        print("\n" + "=" * 60)
        print("SETUP CANNOT CONTINUE WITHOUT AWS CREDENTIALS")
        print("=" * 60)
        print("\nPlease:")
        print("  1. Get AWS credentials from your mentor")
        print("  2. Configure them using one of the methods above")
        print("  3. Run this script again: python aws_setup.py")
        print("\nThe code is ready - you just need credentials to create AWS resources.")
        return
    
    print("\nMake sure you have:")
    print("  - Appropriate permissions (DynamoDB, SNS, IAM)")
    
    input("\nPress Enter to continue...")
    
    try:
        create_dynamodb_tables()
        topic_arn = create_sns_topic()
        create_iam_policy()
        
        print("\n" + "=" * 60)
        print("Setup Complete!")
        print("=" * 60)
        print("\nNext steps:")
        print("1. Save the SNS Topic ARN (shown above)")
        print("2. Configure environment variables:")
        if topic_arn:
            print(f"   export SNS_TOPIC_ARN='{topic_arn}'")
        print("   export AWS_REGION='us-east-1'")
        print("   export SECRET_KEY='your-secret-key-here'")
        print("\n3. Run the application:")
        print("   python app_aws.py")
        print("\n4. Initialize database:")
        print("   Visit: http://localhost:5000/initdb")
    except Exception as e:
        print(f"\n✗ Error during setup: {e}")
        print("\nPlease check:")
        print("  - AWS credentials are correct")
        print("  - You have permissions for DynamoDB, SNS, and IAM")
        print("  - Region is set to us-east-1")


if __name__ == "__main__":
    main()
