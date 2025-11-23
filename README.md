# 🚨 AWS SageMaker Cost Scanner & Cleanup Tool

A comprehensive CLI tool to scan for all chargeable SageMaker resources and provide cleanup options to stop AWS charges.

## 🎯 Features

- **🔍 Complete Resource Scanning**
  - SageMaker Endpoints (biggest cost driver ~$1-4/hour)
  - Training Jobs (active jobs ~$1-4/hour)
  - Notebook Instances (~$0.05-1/hour)
  - S3 Storage (model artifacts ~$0.01-1/day)

- **💰 Cost Analysis**
  - Real-time hourly/daily/monthly cost estimates
  - Instance-specific pricing
  - Total cost summaries

- **🧹 Automated Cleanup**
  - Safe resource deletion with confirmation
  - Batch cleanup operations
  - Immediate cost savings calculation

## 🚀 Quick Start

### 1. Setup AWS Credentials

Choose one method:

**Option A: AWS CLI (Recommended)**
```bash
aws configure
# Enter your AWS Access Key ID, Secret Key, and region
```

**Option B: Environment Variables**
```bash
export AWS_ACCESS_KEY_ID="your-access-key"
export AWS_SECRET_ACCESS_KEY="your-secret-key"
export AWS_DEFAULT_REGION="us-east-1"
```

**Option C: IAM Role (if running on EC2)**
- Attach IAM role with SageMaker permissions to your EC2 instance

### 2. Install Dependencies

```bash
# If using virtual environment (recommended)
python3 -m venv .venv
source .venv/bin/activate
pip install boto3

# Or install globally
pip install boto3
```

### 3. Run the Scanner

**Quick scan:**
```bash
./scan_sagemaker_costs.sh scan
```

**Scan and cleanup:**
```bash
./scan_sagemaker_costs.sh cleanup
```

**Python script directly:**
```bash
python3 cost_estimator_remove_resource.py --scan
python3 cost_estimator_remove_resource.py --cleanup
python3 cost_estimator_remove_resource.py --region us-west-2
```

## 📋 Command Reference

### Shell Wrapper (Easy)
```bash
./scan_sagemaker_costs.sh [scan|cleanup] [region]

# Examples:
./scan_sagemaker_costs.sh scan           # Scan only
./scan_sagemaker_costs.sh cleanup        # Scan and cleanup with confirmation
./scan_sagemaker_costs.sh scan us-west-2 # Scan specific region
```

### Python Script (Full Options)
```bash
python3 cost_estimator_remove_resource.py [OPTIONS]

Options:
  --scan          Scan for chargeable resources (default)
  --cleanup       Scan and offer to cleanup resources  
  --region REGION Specify AWS region (auto-detected if not provided)
  --json          Output results in JSON format
  --help          Show help message

Examples:
  python3 cost_estimator_remove_resource.py --scan
  python3 cost_estimator_remove_resource.py --cleanup
  python3 cost_estimator_remove_resource.py --region eu-west-1
  python3 cost_estimator_remove_resource.py --cleanup --json
```

## 📊 Sample Output

```
🌍 Scanning AWS Region: us-east-1
🕐 Scan Time: 2025-11-19 15:30:00

================================================================================
🔍 SAGEMAKER COST SCAN RESULTS  
================================================================================

🚀 ENDPOINTS (2 found)
--------------------------------------------------
🟢 huggingface-pytorch-inference-2024-11-19-14-30-00-123
   Status: InService
   💰 Cost: $1.41/hour | $33.84/day | $1015.20/month
   📦 ml.g5.xlarge x1 = $1.41/hour

🔴 my-model-endpoint-v2
   Status: Failed
   💰 Cost: $0.00/hour | $0.00/day | $0.00/month

🏋️  TRAINING JOBS (1 active)
--------------------------------------------------
🔄 my-training-job-2024-11-19
   Status: InProgress
   💰 Cost: $2.03/hour
   ⏱️  Running for: 2.5 hours
   💸 Cost so far: $5.08
   📦 ml.g5.2xlarge x1

📓 NOTEBOOK INSTANCES (0 active)
--------------------------------------------------
✅ No active notebook instances found

💾 S3 STORAGE (3 SageMaker buckets)
--------------------------------------------------
🪣 llm-model-artifacts-sunny
   📊 Size: 15.2 GB
   💰 Monthly cost: $0.35
   📁 Objects: 1,234

================================================================================
💰 COST SUMMARY
================================================================================
🔥 ACTIVE COMPUTE CHARGES: $3.44/hour
📅 Daily compute cost: $82.56
📊 Monthly compute cost: $2476.80
💾 Monthly storage cost: $0.89
🎯 TOTAL MONTHLY ESTIMATE: $2477.69

⚠️  WARNING: You have $3.44/hour in active charges!
💸 This equals ~$2477/month if left running!
```

## ⚠️  Emergency Cleanup

If you see high charges and need immediate cleanup:

```bash
# EMERGENCY: Stop all charges now
./scan_sagemaker_costs.sh cleanup

# Or run Python directly
python3 cost_estimator_remove_resource.py --cleanup
```

This will:
1. ✅ Delete all InService endpoints  
2. ⏹️  Stop all running training jobs
3. 🛑 Stop all notebook instances
4. 💰 Calculate your savings

## 🔒 Required AWS Permissions

Your AWS credentials need these permissions:

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "sagemaker:ListEndpoints",
                "sagemaker:DescribeEndpoint",
                "sagemaker:DescribeEndpointConfig",
                "sagemaker:DeleteEndpoint",
                "sagemaker:DeleteEndpointConfig",
                "sagemaker:ListTrainingJobs",
                "sagemaker:DescribeTrainingJob",
                "sagemaker:StopTrainingJob",
                "sagemaker:ListNotebookInstances",
                "sagemaker:DescribeNotebookInstance",
                "sagemaker:StopNotebookInstance",
                "s3:ListAllMyBuckets",
                "s3:ListBucket",
                "s3:GetBucketLocation"
            ],
            "Resource": "*"
        }
    ]
}
```

## 🐛 Troubleshooting

### "Unable to locate credentials"
```bash
# Check AWS CLI configuration
aws configure list

# Or set environment variables
export AWS_ACCESS_KEY_ID="your-key"
export AWS_SECRET_ACCESS_KEY="your-secret"
export AWS_DEFAULT_REGION="us-east-1"
```

### "You must specify a region"
```bash
# Run with explicit region
python3 cost_estimator_remove_resource.py --region us-east-1

# Or set default region
aws configure set region us-east-1
```

### "ModuleNotFoundError: No module named 'boto3'"
```bash
# Install boto3
pip install boto3

# Or if using virtual environment
source .venv/bin/activate
pip install boto3
```

## 💡 Tips

1. **Set up billing alerts** in AWS Console to prevent surprises
2. **Run regular scans** to catch accidental resource creation
3. **Always verify** before cleanup - deleted endpoints need to be recreated
4. **Use specific regions** if you have resources in multiple regions
5. **Check multiple regions** if you're unsure where resources are deployed

## 🔗 Related Files

- `cost_estimator_remove_resource.py` - Main Python scanner script
- `scan_sagemaker_costs.sh` - Shell wrapper for easier execution
- `estimator_launcher.ipynb` - Jupyter notebook with emergency cleanup cells
- `README.md` - This file

## 🆘 Emergency Contacts

If you're seeing unexpected AWS charges:

1. **Immediate**: Run this cleanup tool
2. **AWS Support**: Open a billing support case
3. **AWS Console**: Manually delete resources in SageMaker console
4. **Billing Alerts**: Set up budget alerts for future prevention

---

**⚠️  Remember: This tool can delete resources that may be expensive to recreate. Always verify what you're deleting!**
