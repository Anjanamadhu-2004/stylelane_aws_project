# AWS Credentials Setup Guide

## Where to Paste AWS Credentials

When you receive AWS credentials from your mentor, you need to configure them. Here are the exact places:

### Option 1: AWS CLI Configuration (Recommended)

**Location:** `~/.aws/credentials` (Windows: `C:\Users\YourName\.aws\credentials`)

**Steps:**
1. Open terminal/command prompt
2. Run: `aws configure`
3. Enter when prompted:
   ```
   AWS Access Key ID: [paste from mentor]
   AWS Secret Access Key: [paste from mentor]
   Default region name: us-east-1
   Default output format: json
   ```

This creates the credentials file automatically.

### Option 2: Environment Variables (Temporary)

**Windows PowerShell:**
```powershell
$env:AWS_ACCESS_KEY_ID='your-access-key-id-here'
$env:AWS_SECRET_ACCESS_KEY='your-secret-access-key-here'
$env:AWS_DEFAULT_REGION='us-east-1'
```

**Windows CMD:**
```cmd
set AWS_ACCESS_KEY_ID=your-access-key-id-here
set AWS_SECRET_ACCESS_KEY=your-secret-access-key-here
set AWS_DEFAULT_REGION=us-east-1
```

**Linux/Mac:**
```bash
export AWS_ACCESS_KEY_ID='your-access-key-id-here'
export AWS_SECRET_ACCESS_KEY='your-secret-access-key-here'
export AWS_DEFAULT_REGION='us-east-1'
```

### Option 3: .env File (For Development)

**Location:** Create `.env` file in your project root

**Content:**
```env
AWS_ACCESS_KEY_ID=your-access-key-id-here
AWS_SECRET_ACCESS_KEY=your-secret-access-key-here
AWS_DEFAULT_REGION=us-east-1
```

Then in your Python code, load it:
```python
from dotenv import load_dotenv
load_dotenv()
```

## Where to Paste SNS Topic ARN

After running `aws_setup.py` successfully, you'll get an SNS Topic ARN like:
```
arn:aws:sns:us-east-1:123456789012:stylelane-notifications
```

**Paste it in these places:**

### 1. Environment Variable
```bash
export SNS_TOPIC_ARN='arn:aws:sns:us-east-1:123456789012:stylelane-notifications'
```

### 2. .env File
```env
SNS_TOPIC_ARN=arn:aws:sns:us-east-1:123456789012:stylelane-notifications
```

### 3. EC2 Instance (When Deploying)
When deploying to EC2, set it as an environment variable in your systemd service file or shell.

## Step-by-Step: First Time Setup

1. **Get credentials from mentor:**
   - AWS Access Key ID
   - AWS Secret Access Key

2. **Configure credentials:**
   ```bash
   aws configure
   ```

3. **Run setup script:**
   ```bash
   python aws_setup.py
   ```

4. **Copy SNS Topic ARN** from the output

5. **Set SNS Topic ARN:**
   ```bash
   export SNS_TOPIC_ARN='arn:aws:sns:us-east-1:YOUR_ACCOUNT:stylelane-notifications'
   ```

6. **Run the application:**
   ```bash
   python app_aws.py
   ```

## Verification

Test if credentials work:
```bash
aws sts get-caller-identity
```

This should return your AWS account ID if credentials are correct.

## Security Notes

- **Never commit credentials to Git!**
- Add `.env` to `.gitignore`
- Use IAM roles on EC2 instead of access keys when possible
- Rotate credentials regularly
