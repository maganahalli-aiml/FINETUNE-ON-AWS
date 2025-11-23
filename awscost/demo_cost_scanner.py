#!/usr/bin/env python3
"""
🎭 AWS SageMaker Cost Scanner - Demo Mode
Shows sample output with mock data for demonstration purposes.
"""

from datetime import datetime

def print_demo_scan():
    """Print a demo scan with sample data to show what the output looks like."""
    
    print("🚨 AWS SageMaker Cost Scanner - DEMO MODE")
    print("🌍 Scanning AWS Region: us-east-1")
    print(f"🕐 Scan Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("📋 NOTE: This is sample data for demonstration")
    
    print("\n" + "="*80)
    print("🔍 SAGEMAKER COST SCAN RESULTS")
    print("="*80)
    
    # Sample Endpoints
    print(f"\n🚀 ENDPOINTS (2 found)")
    print("-" * 50)
    
    print("🟢 huggingface-pytorch-inference-2024-11-19-14-30-00-123")
    print("   Status: InService")
    print("   💰 Cost: $1.41/hour | $33.84/day | $1015.20/month")
    print("   📦 ml.g5.xlarge x1 = $1.41/hour")
    print()
    
    print("🟢 my-llm-endpoint-prod")
    print("   Status: InService")
    print("   💰 Cost: $2.03/hour | $48.72/day | $1461.60/month")
    print("   📦 ml.g5.2xlarge x1 = $2.03/hour")
    print()
    
    # Sample Training Jobs
    print(f"\n🏋️  TRAINING JOBS (1 active)")
    print("-" * 50)
    
    print("🔄 llm-finetuning-job-2024-11-19")
    print("   Status: InProgress")
    print("   💰 Cost: $3.83/hour")
    print("   ⏱️  Running for: 2.5 hours")
    print("   💸 Cost so far: $9.58")
    print("   📦 ml.p3.2xlarge x1")
    print()
    
    # Sample Notebook Instances  
    print(f"\n📓 NOTEBOOK INSTANCES (1 active)")
    print("-" * 50)
    
    print("📝 my-sagemaker-notebook")
    print("   Status: InService")
    print("   💰 Cost: $0.23/hour | $5.52/day")
    print("   📦 ml.m5.xlarge")
    print()
    
    # Sample S3 Storage
    print(f"\n💾 S3 STORAGE (3 SageMaker buckets)")
    print("-" * 50)
    
    print("🪣 llm-model-artifacts-sunny")
    print("   📊 Size: 15.2 GB")
    print("   💰 Monthly cost: $0.35")
    print("   📁 Objects: 1,234")
    print()
    
    print("🪣 llm-finetune-dataset-sunny")
    print("   📊 Size: 8.7 GB")
    print("   💰 Monthly cost: $0.20")
    print("   📁 Objects: 567")
    print()
    
    print("🪣 sagemaker-us-east-1-123456789")
    print("   📊 Size: 25.1 GB")
    print("   💰 Monthly cost: $0.58")
    print("   📁 Objects: 2,891")
    print()
    
    # Summary
    total_hourly = 1.41 + 2.03 + 3.83 + 0.23  # $7.50
    total_daily = total_hourly * 24  # $180.00
    total_monthly = total_daily * 30  # $5,400
    storage_monthly = 0.35 + 0.20 + 0.58  # $1.13
    
    print("\n" + "="*80)
    print("💰 COST SUMMARY")
    print("="*80)
    print(f"🔥 ACTIVE COMPUTE CHARGES: ${total_hourly:.2f}/hour")
    print(f"📅 Daily compute cost: ${total_daily:.2f}")
    print(f"📊 Monthly compute cost: ${total_monthly:.2f}")
    print(f"💾 Monthly storage cost: ${storage_monthly:.2f}")
    print(f"🎯 TOTAL MONTHLY ESTIMATE: ${total_monthly + storage_monthly:.2f}")
    
    print(f"\n⚠️  WARNING: You have ${total_hourly:.2f}/hour in active charges!")
    print(f"💸 This equals ~${int(total_monthly)}/month if left running!")
    
    print("\n" + "="*80)
    print("🧹 CLEANUP SIMULATION")
    print("="*80)
    print("If you ran --cleanup, this tool would:")
    print("✅ Delete 2 active endpoints (save $3.44/hour)")
    print("⏹️  Stop 1 training job (save $3.83/hour)")  
    print("🛑 Stop 1 notebook instance (save $0.23/hour)")
    print(f"💰 Total savings: ${total_hourly:.2f}/hour = ${int(total_monthly)}/month")
    
    print("\n💡 To run real scan:")
    print("1. Configure AWS credentials: aws configure")
    print("2. Run: ./scan_sagemaker_costs.sh scan")
    print("3. For cleanup: ./scan_sagemaker_costs.sh cleanup")

if __name__ == "__main__":
    print_demo_scan()