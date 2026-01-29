# Manual AWS Setup Instructions

## Step 1: Create DynamoDB Tables Manually

Go to AWS Console → DynamoDB → Create Table

Create these 7 tables with the following settings:

### 1. stylelane-users
- **Table name:** `stylelane-users`
- **Partition key:** `id` (String)
- **Settings:** On-demand
- **Add Global Secondary Index:**
  - Index name: `username-index`
  - Partition key: `username` (String)
  - Projection: All attributes

### 2. stylelane-stores
- **Table name:** `stylelane-stores`
- **Partition key:** `id` (String)
- **Settings:** On-demand

### 3. stylelane-products
- **Table name:** `stylelane-products`
- **Partition key:** `id` (String)
- **Settings:** On-demand
- **Add Global Secondary Index:**
  - Index name: `sku-index`
  - Partition key: `sku` (String)
  - Projection: All attributes

### 4. stylelane-inventory
- **Table name:** `stylelane-inventory`
- **Partition key:** `id` (String)
- **Settings:** On-demand

### 5. stylelane-sales
- **Table name:** `stylelane-sales`
- **Partition key:** `id` (String)
- **Settings:** On-demand

### 6. stylelane-restock-requests
- **Table name:** `stylelane-restock-requests`
- **Partition key:** `id` (String)
- **Settings:** On-demand

### 7. stylelane-shipments
- **Table name:** `stylelane-shipments`
- **Partition key:** `id` (String)
- **Settings:** On-demand

**Important:** Make sure all tables are in region **us-east-1** (US East - N. Virginia)

## Step 2: Create SNS Topic

1. Go to AWS Console → SNS → Topics
2. Click "Create topic"
3. Choose "Standard" type
4. Topic name: `stylelane-notifications`
5. Click "Create topic"
6. **Copy the Topic ARN** (looks like: `arn:aws:sns:us-east-1:123456789012:stylelane-notifications`)

## Step 3: Paste SNS Topic ARN in Code

1. Open `app_aws.py`
2. Find this line (around line 25):
   ```python
   SNS_TOPIC_ARN = "PASTE_YOUR_SNS_TOPIC_ARN_HERE"
   ```
3. Replace `PASTE_YOUR_SNS_TOPIC_ARN_HERE` with your actual Topic ARN:
   ```python
   SNS_TOPIC_ARN = "arn:aws:sns:us-east-1:123456789012:stylelane-notifications"
   ```

## Step 4: Configure AWS Credentials

Run in terminal:
```bash
aws configure
```

Enter:
- AWS Access Key ID: [from your mentor]
- AWS Secret Access Key: [from your mentor]
- Default region: `us-east-1`
- Default output format: `json`

## Step 5: Run the Application

```bash
python app_aws.py
```

## Step 6: Initialize Database

Visit in browser:
```
http://localhost:5000/initdb
```

This will create demo data (admin/admin123, manager1/manager123, supplier1/supplier123)

## That's It!

You don't need `aws_setup.py` - everything is done manually as your mentor explained.
