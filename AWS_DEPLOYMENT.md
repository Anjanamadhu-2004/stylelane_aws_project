# StyleLane AWS Deployment Guide

This guide explains how to deploy StyleLane to AWS using EC2, DynamoDB, SNS, and IAM.

## Prerequisites

1. AWS Account with appropriate permissions
2. AWS CLI installed and configured (`aws configure`)
3. Python 3.8+ installed
4. EC2 instance (Ubuntu/Amazon Linux recommended)

## Architecture

- **EC2**: Hosts the Flask application
- **DynamoDB**: NoSQL database (replaces SQLite)
- **SNS**: Notifications for low stock alerts and restock requests
- **IAM**: Manages AWS resource access permissions
- **Region**: US East (N. Virginia) - us-east-1

## Step 1: Set Up AWS Resources

### Option A: Automated Setup (Recommended)

Run the setup script to create all resources:

```bash
python aws_setup.py
```

This will:
- Create 7 DynamoDB tables
- Create SNS topic for notifications
- Generate IAM policy document

### Option B: Manual Setup

#### 1. Create DynamoDB Tables

Use AWS Console or CLI to create these tables with `PAY_PER_REQUEST` billing:

- `stylelane-users` (with GSI: username-index)
- `stylelane-stores`
- `stylelane-products` (with GSI: sku-index)
- `stylelane-inventory`
- `stylelane-sales`
- `stylelane-restock-requests`
- `stylelane-shipments`

#### 2. Create SNS Topic

```bash
aws sns create-topic --name stylelane-notifications --region us-east-1
```

Note the Topic ARN for later use.

#### 3. Create IAM Policy

Create an IAM policy with permissions for:
- DynamoDB: PutItem, GetItem, UpdateItem, DeleteItem, Query, Scan
- SNS: Publish

Attach this policy to your EC2 instance role or IAM user.

## Step 2: Configure EC2 Instance

### 1. Launch EC2 Instance

- Choose Ubuntu 22.04 LTS or Amazon Linux 2023
- Instance type: t2.micro (free tier) or t3.small
- Security Group: Allow inbound HTTP (port 80) and custom TCP (port 5000)
- Attach IAM role with DynamoDB and SNS permissions

### 2. Connect to EC2 Instance

```bash
ssh -i your-key.pem ubuntu@your-ec2-ip
```

### 3. Install Dependencies

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Python and pip
sudo apt install python3 python3-pip -y

# Install Git (if needed)
sudo apt install git -y
```

### 4. Clone/Upload Project

```bash
# Option 1: Clone from Git
git clone your-repo-url
cd stylelane-project

# Option 2: Upload files via SCP
# scp -r . ubuntu@your-ec2-ip:/home/ubuntu/stylelane
```

### 5. Install Python Dependencies

```bash
pip3 install -r requirements.txt
```

## Step 3: Configure Environment Variables

Create a `.env` file or set environment variables:

```bash
export AWS_REGION="us-east-1"
export SNS_TOPIC_ARN="arn:aws:sns:us-east-1:YOUR_ACCOUNT:stylelane-notifications"
export SECRET_KEY="your-secret-key-change-this"
```

Or create a `.env` file:

```bash
cat > .env << EOF
AWS_REGION=us-east-1
SNS_TOPIC_ARN=arn:aws:sns:us-east-1:YOUR_ACCOUNT:stylelane-notifications
SECRET_KEY=your-secret-key-change-this
EOF
```

## Step 4: Configure AWS Credentials

### Option A: IAM Role (Recommended for EC2)

Attach an IAM role to your EC2 instance with DynamoDB and SNS permissions. The application will automatically use the instance role.

### Option B: AWS Credentials File

```bash
aws configure
# Enter your Access Key ID
# Enter your Secret Access Key
# Default region: us-east-1
# Default output format: json
```

## Step 5: Run the Application

### Development Mode

```bash
python3 app_aws.py
```

### Production Mode with Gunicorn

```bash
pip3 install gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 app_aws:app
```

### As a Service (systemd)

Create `/etc/systemd/system/stylelane.service`:

```ini
[Unit]
Description=StyleLane Flask Application
After=network.target

[Service]
User=ubuntu
WorkingDirectory=/home/ubuntu/stylelane
Environment="PATH=/usr/bin"
Environment="AWS_REGION=us-east-1"
Environment="SNS_TOPIC_ARN=arn:aws:sns:us-east-1:YOUR_ACCOUNT:stylelane-notifications"
Environment="SECRET_KEY=your-secret-key"
ExecStart=/usr/bin/gunicorn -w 4 -b 0.0.0.0:5000 app_aws:app

[Install]
WantedBy=multi-user.target
```

Enable and start:

```bash
sudo systemctl enable stylelane
sudo systemctl start stylelane
sudo systemctl status stylelane
```

## Step 6: Initialize Database

Visit in your browser:

```
http://your-ec2-ip:5000/initdb
```

This will create demo data (admin/admin123, manager1/manager123, supplier1/supplier123).

## Step 7: Set Up Nginx (Optional, for Production)

```bash
sudo apt install nginx -y

# Create nginx config
sudo nano /etc/nginx/sites-available/stylelane
```

Add:

```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

Enable:

```bash
sudo ln -s /etc/nginx/sites-available/stylelane /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

## Step 8: Configure SNS Notifications (Optional)

To receive email notifications:

1. Go to AWS SNS Console
2. Select your topic: `stylelane-notifications`
3. Click "Create subscription"
4. Choose "Email" protocol
5. Enter your email address
6. Confirm subscription via email

## Troubleshooting

### DynamoDB Connection Issues

- Verify IAM permissions
- Check AWS region (must be us-east-1)
- Ensure tables exist: `aws dynamodb list-tables --region us-east-1`

### SNS Notifications Not Working

- Verify SNS_TOPIC_ARN environment variable
- Check IAM permissions for SNS:Publish
- Verify topic exists: `aws sns list-topics --region us-east-1`

### Application Errors

- Check logs: `journalctl -u stylelane -f` (if using systemd)
- Verify environment variables are set
- Check EC2 security group allows inbound traffic on port 5000

## Cost Estimation

- **EC2 t2.micro**: Free tier eligible (750 hours/month)
- **DynamoDB**: Pay-per-request pricing (~$1.25 per million requests)
- **SNS**: First 1M requests/month free
- **Data Transfer**: First 1GB/month free

Estimated monthly cost for small usage: **$0-5**

## Security Best Practices

1. **Change default passwords** after initialization
2. **Use HTTPS** in production (Let's Encrypt + Certbot)
3. **Rotate AWS credentials** regularly
4. **Restrict security group** to specific IPs if possible
5. **Use IAM roles** instead of access keys when possible
6. **Enable CloudWatch** logging for monitoring

## Monitoring

Set up CloudWatch alarms for:
- DynamoDB read/write capacity
- EC2 CPU utilization
- Application errors (via CloudWatch Logs)

## Support

For issues, check:
- AWS CloudWatch Logs
- Application logs: `tail -f /var/log/stylelane.log`
- EC2 instance status in AWS Console
