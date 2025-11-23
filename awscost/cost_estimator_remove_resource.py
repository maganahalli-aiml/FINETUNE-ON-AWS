#!/usr/bin/env python3
"""
🚨 AWS SageMaker Cost Scanner & Resource Cleanup Tool
Scans for all chargeable SageMaker resources and provides cleanup options.

Usage:
    python cost_estimator_remove_resource.py --scan          # Scan only
    python cost_estimator_remove_resource.py --cleanup       # Scan and cleanup
    python cost_estimator_remove_resource.py --region us-east-1  # Specific region
    python cost_estimator_remove_resource.py --help          # Show help
"""

import boto3
import argparse
import sys
import json
from datetime import datetime, timezone
from typing import Dict, List, Any
import time

class SageMakerCostScanner:
    def __init__(self, region_name: str = None):
        """Initialize the scanner with AWS clients."""
        self.region_name = region_name or self._detect_region()
        
        # Check AWS credentials before creating clients
        self._check_aws_credentials()
        
        self.sagemaker_client = boto3.client('sagemaker', region_name=self.region_name)
        self.s3_client = boto3.client('s3', region_name=self.region_name)
        self.ec2_client = boto3.client('ec2', region_name=self.region_name)
        self.apigateway_client = boto3.client('apigateway', region_name=self.region_name)
        self.apigatewayv2_client = boto3.client('apigatewayv2', region_name=self.region_name)
        
        # Cost estimates per hour (USD)
        self.cost_per_hour = {
            'ml.t3.medium': 0.05,
            'ml.t3.large': 0.10,
            'ml.m5.large': 0.12,
            'ml.m5.xlarge': 0.23,
            'ml.m5.2xlarge': 0.46,
            'ml.m5.4xlarge': 0.93,
            'ml.c5.xlarge': 0.20,
            'ml.c5.2xlarge': 0.40,
            'ml.c5.4xlarge': 0.81,
            'ml.p3.2xlarge': 3.83,
            'ml.g4dn.xlarge': 0.71,
            'ml.g5.xlarge': 1.41,
            'ml.g5.2xlarge': 2.03,
            'ml.g5.4xlarge': 4.07,
            'ml.inf1.xlarge': 0.36,
            'ml.inf1.2xlarge': 0.58,
        }
        
    def _detect_region(self) -> str:
        """Detect AWS region from various sources."""
        # Try environment variable first
        import os
        env_region = os.environ.get('AWS_DEFAULT_REGION') or os.environ.get('AWS_REGION')
        if env_region:
            print(f"🌍 Using region from environment: {env_region}")
            return env_region
            
        try:
            # Try from AWS CLI config
            session = boto3.Session()
            if session.region_name:
                print(f"🌍 Using region from AWS config: {session.region_name}")
                return session.region_name
        except:
            pass
            
        try:
            # Try SageMaker session 
            import sagemaker
            session = sagemaker.Session()
            if session.boto_region_name:
                print(f"🌍 Using region from SageMaker session: {session.boto_region_name}")
                return session.boto_region_name
        except:
            pass
            
        # Interactive region selection if none found
        print("⚠️  No AWS region detected. Please select a region:")
        regions = [
            'us-east-1', 'us-west-2', 'eu-west-1', 'eu-central-1', 
            'ap-south-1', 'ap-southeast-1', 'ap-southeast-2', 'ap-northeast-1'
        ]
        
        for i, region in enumerate(regions, 1):
            print(f"  {i}. {region}")
        
        try:
            choice = input("\nEnter region number (1-8) or type region name: ").strip()
            if choice.isdigit() and 1 <= int(choice) <= len(regions):
                selected_region = regions[int(choice) - 1]
            else:
                selected_region = choice
            
            print(f"🌍 Using selected region: {selected_region}")
            return selected_region
        except (KeyboardInterrupt, EOFError):
            print("\n❌ Region selection cancelled")
            raise SystemExit(1)
    
    def _check_aws_credentials(self):
        """Check if AWS credentials are properly configured."""
        try:
            # Try to get caller identity to verify credentials
            sts_client = boto3.client('sts', region_name=self.region_name)
            response = sts_client.get_caller_identity()
            print(f"✅ AWS credentials verified for account: {response.get('Account', 'Unknown')}")
            
        except Exception as e:
            print(f"❌ AWS credentials error: {e}")
            print("\n🔧 To fix this issue:")
            print("1. Configure AWS CLI: aws configure")
            print("2. Or set environment variables:")
            print("   export AWS_ACCESS_KEY_ID='your-access-key'")
            print("   export AWS_SECRET_ACCESS_KEY='your-secret-key'")
            print("   export AWS_DEFAULT_REGION='us-east-1'")
            print("3. Or use IAM role if running on EC2")
            print("\n💡 See README.md for detailed setup instructions")
            raise SystemExit(1)
    
    def scan_endpoints(self) -> List[Dict[str, Any]]:
        """Scan for active SageMaker endpoints."""
        print("🔍 Scanning SageMaker Endpoints...")
        
        endpoints = []
        try:
            response = self.sagemaker_client.list_endpoints()
            
            for endpoint_summary in response['Endpoints']:
                endpoint_name = endpoint_summary['EndpointName']
                
                # Get detailed endpoint info
                endpoint_details = self.sagemaker_client.describe_endpoint(
                    EndpointName=endpoint_name
                )
                
                # Get endpoint configuration
                config_name = endpoint_details['EndpointConfigName']
                config_details = self.sagemaker_client.describe_endpoint_config(
                    EndpointConfigName=config_name
                )
                
                # Calculate cost
                total_cost_per_hour = 0
                instance_info = []
                
                for variant in config_details['ProductionVariants']:
                    instance_type = variant['InstanceType']
                    instance_count = variant['InitialInstanceCount']
                    cost_per_instance = self.cost_per_hour.get(instance_type, 0.50)  # Default estimate
                    variant_cost = cost_per_instance * instance_count
                    total_cost_per_hour += variant_cost
                    
                    instance_info.append({
                        'instance_type': instance_type,
                        'instance_count': instance_count,
                        'cost_per_hour': cost_per_instance,
                        'variant_cost_per_hour': variant_cost
                    })
                
                endpoint_info = {
                    'name': endpoint_name,
                    'status': endpoint_details['EndpointStatus'],
                    'config_name': config_name,
                    'creation_time': endpoint_details['CreationTime'],
                    'instances': instance_info,
                    'total_cost_per_hour': total_cost_per_hour,
                    'daily_cost': total_cost_per_hour * 24,
                    'monthly_cost': total_cost_per_hour * 24 * 30
                }
                
                endpoints.append(endpoint_info)
                
        except Exception as e:
            print(f"❌ Error scanning endpoints: {e}")
            
        return endpoints
    
    def scan_training_jobs(self) -> List[Dict[str, Any]]:
        """Scan for active training jobs."""
        print("🔍 Scanning Training Jobs...")
        
        training_jobs = []
        try:
            response = self.sagemaker_client.list_training_jobs(
                StatusEquals='InProgress'
            )
            
            for job_summary in response['TrainingJobSummaries']:
                job_name = job_summary['TrainingJobName']
                
                # Get detailed job info
                job_details = self.sagemaker_client.describe_training_job(
                    TrainingJobName=job_name
                )
                
                # Extract cost information
                instance_type = job_details['ResourceConfig']['InstanceType']
                instance_count = job_details['ResourceConfig']['InstanceCount']
                cost_per_instance = self.cost_per_hour.get(instance_type, 1.00)
                total_cost_per_hour = cost_per_instance * instance_count
                
                # Calculate runtime
                start_time = job_details['TrainingStartTime']
                current_time = datetime.now(timezone.utc)
                runtime_hours = (current_time - start_time).total_seconds() / 3600
                estimated_cost_so_far = runtime_hours * total_cost_per_hour
                
                job_info = {
                    'name': job_name,
                    'status': job_details['TrainingJobStatus'],
                    'instance_type': instance_type,
                    'instance_count': instance_count,
                    'cost_per_hour': total_cost_per_hour,
                    'runtime_hours': runtime_hours,
                    'estimated_cost_so_far': estimated_cost_so_far,
                    'start_time': start_time
                }
                
                training_jobs.append(job_info)
                
        except Exception as e:
            print(f"❌ Error scanning training jobs: {e}")
            
        return training_jobs
    
    def scan_notebook_instances(self) -> List[Dict[str, Any]]:
        """Scan for notebook instances."""
        print("🔍 Scanning Notebook Instances...")
        
        notebook_instances = []
        try:
            response = self.sagemaker_client.list_notebook_instances()
            
            for instance_summary in response['NotebookInstances']:
                instance_name = instance_summary['NotebookInstanceName']
                
                if instance_summary['NotebookInstanceStatus'] == 'InService':
                    # Get detailed instance info
                    instance_details = self.sagemaker_client.describe_notebook_instance(
                        NotebookInstanceName=instance_name
                    )
                    
                    instance_type = instance_details['InstanceType']
                    cost_per_hour = self.cost_per_hour.get(instance_type, 0.10)
                    
                    # Calculate runtime
                    creation_time = instance_details['CreationTime']
                    current_time = datetime.now(timezone.utc)
                    runtime_hours = (current_time - creation_time).total_seconds() / 3600
                    
                    instance_info = {
                        'name': instance_name,
                        'status': instance_details['NotebookInstanceStatus'],
                        'instance_type': instance_type,
                        'cost_per_hour': cost_per_hour,
                        'daily_cost': cost_per_hour * 24,
                        'runtime_hours': runtime_hours,
                        'creation_time': creation_time
                    }
                    
                    notebook_instances.append(instance_info)
                    
        except Exception as e:
            print(f"❌ Error scanning notebook instances: {e}")
            
        return notebook_instances
    
    def scan_s3_storage(self) -> Dict[str, Any]:
        """Scan for SageMaker-related S3 storage."""
        print("🔍 Scanning S3 Storage...")
        
        storage_info = {
            'buckets': [],
            'total_size_gb': 0,
            'estimated_monthly_cost': 0
        }
        
        try:
            # List all buckets
            buckets = self.s3_client.list_buckets()
            
            sagemaker_buckets = []
            for bucket in buckets['Buckets']:
                bucket_name = bucket['Name']
                
                # Check if it's SageMaker related
                if any(keyword in bucket_name.lower() for keyword in ['sagemaker', 'llm', 'model', 'finetune']):
                    try:
                        # Get bucket size (this is an estimate - full calculation can be expensive)
                        response = self.s3_client.list_objects_v2(Bucket=bucket_name, MaxKeys=1000)
                        
                        total_size = 0
                        object_count = 0
                        
                        if 'Contents' in response:
                            for obj in response['Contents']:
                                total_size += obj['Size']
                                object_count += 1
                        
                        size_gb = total_size / (1024**3)
                        # S3 standard storage cost ~$0.023 per GB per month
                        monthly_cost = size_gb * 0.023
                        
                        bucket_info = {
                            'name': bucket_name,
                            'size_gb': size_gb,
                            'object_count': object_count,
                            'monthly_cost': monthly_cost,
                            'creation_date': bucket['CreationDate']
                        }
                        
                        sagemaker_buckets.append(bucket_info)
                        storage_info['total_size_gb'] += size_gb
                        storage_info['estimated_monthly_cost'] += monthly_cost
                        
                    except Exception as e:
                        print(f"⚠️  Could not analyze bucket {bucket_name}: {e}")
                        
            storage_info['buckets'] = sagemaker_buckets
            
        except Exception as e:
            print(f"❌ Error scanning S3 storage: {e}")
            
        return storage_info
    
    def scan_api_gateways(self) -> Dict[str, Any]:
        """Scan for API Gateway resources."""
        print("🔍 Scanning API Gateways...")
        
        api_info = {
            'rest_apis': [],
            'http_apis': [],
            'websocket_apis': [],
            'total_apis': 0,
            'estimated_monthly_cost': 0
        }
        
        try:
            # Scan REST APIs
            rest_apis = self.apigateway_client.get_rest_apis()
            for api in rest_apis.get('items', []):
                api_id = api['id']
                api_name = api['name']
                
                # Get stages for this API
                try:
                    stages = self.apigateway_client.get_stages(restApiId=api_id)
                    stage_list = [stage['stageName'] for stage in stages.get('item', [])]
                    
                    # Check for caching (adds costs)
                    caching_enabled = False
                    cache_size = 0
                    for stage in stages.get('item', []):
                        if stage.get('cacheClusterEnabled', False):
                            caching_enabled = True
                            cache_size = float(stage.get('cacheClusterSize', '0.5'))
                            break
                    
                    # Estimate monthly cost for caching
                    cache_cost = cache_size * 0.02 * 24 * 30 if caching_enabled else 0
                    
                    rest_api_info = {
                        'id': api_id,
                        'name': api_name,
                        'type': 'REST API',
                        'stages': stage_list,
                        'caching_enabled': caching_enabled,
                        'cache_size_gb': cache_size,
                        'cache_monthly_cost': cache_cost,
                        'created_date': api.get('createdDate'),
                        'description': api.get('description', '')
                    }
                    
                    api_info['rest_apis'].append(rest_api_info)
                    api_info['estimated_monthly_cost'] += cache_cost
                    
                except Exception as e:
                    print(f"⚠️  Could not get stages for REST API {api_id}: {e}")
            
            # Scan HTTP APIs (API Gateway v2)
            try:
                http_apis = self.apigatewayv2_client.get_apis()
                for api in http_apis.get('Items', []):
                    if api.get('ProtocolType') == 'HTTP':
                        api_id = api['ApiId']
                        api_name = api['Name']
                        
                        # Get stages
                        try:
                            stages = self.apigatewayv2_client.get_stages(ApiId=api_id)
                            stage_list = [stage['StageName'] for stage in stages.get('Items', [])]
                        except:
                            stage_list = []
                        
                        http_api_info = {
                            'id': api_id,
                            'name': api_name,
                            'type': 'HTTP API',
                            'stages': stage_list,
                            'created_date': api.get('CreatedDate'),
                            'description': api.get('Description', ''),
                            'route_selection_expression': api.get('RouteSelectionExpression', '')
                        }
                        
                        api_info['http_apis'].append(http_api_info)
            except Exception as e:
                print(f"⚠️  Could not scan HTTP APIs: {e}")
            
            # Scan WebSocket APIs
            try:
                websocket_apis = self.apigatewayv2_client.get_apis()
                for api in websocket_apis.get('Items', []):
                    if api.get('ProtocolType') == 'WEBSOCKET':
                        api_id = api['ApiId']
                        api_name = api['Name']
                        
                        # Get stages
                        try:
                            stages = self.apigatewayv2_client.get_stages(ApiId=api_id)
                            stage_list = [stage['StageName'] for stage in stages.get('Items', [])]
                        except:
                            stage_list = []
                        
                        ws_api_info = {
                            'id': api_id,
                            'name': api_name,
                            'type': 'WebSocket API',
                            'stages': stage_list,
                            'created_date': api.get('CreatedDate'),
                            'description': api.get('Description', '')
                        }
                        
                        api_info['websocket_apis'].append(ws_api_info)
            except Exception as e:
                print(f"⚠️  Could not scan WebSocket APIs: {e}")
            
            api_info['total_apis'] = len(api_info['rest_apis']) + len(api_info['http_apis']) + len(api_info['websocket_apis'])
            
        except Exception as e:
            print(f"❌ Error scanning API Gateway: {e}")
        
        return api_info
    
    def print_scan_results(self, endpoints, training_jobs, notebook_instances, storage_info, api_info=None):
        """Print formatted scan results."""
        print("\n" + "="*80)
        print("🔍 SAGEMAKER COST SCAN RESULTS")
        print("="*80)
        
        total_hourly_cost = 0
        
        # Endpoints
        print(f"\n🚀 ENDPOINTS ({len(endpoints)} found)")
        print("-" * 50)
        if endpoints:
            for ep in endpoints:
                status_emoji = "🟢" if ep['status'] == 'InService' else "🔴"
                print(f"{status_emoji} {ep['name']}")
                print(f"   Status: {ep['status']}")
                print(f"   💰 Cost: ${ep['total_cost_per_hour']:.2f}/hour | ${ep['daily_cost']:.2f}/day | ${ep['monthly_cost']:.2f}/month")
                for instance in ep['instances']:
                    print(f"   📦 {instance['instance_type']} x{instance['instance_count']} = ${instance['variant_cost_per_hour']:.2f}/hour")
                print()
                
                if ep['status'] == 'InService':
                    total_hourly_cost += ep['total_cost_per_hour']
        else:
            print("✅ No endpoints found")
        
        # Training Jobs
        print(f"\n🏋️  TRAINING JOBS ({len(training_jobs)} active)")
        print("-" * 50)
        if training_jobs:
            for job in training_jobs:
                print(f"🔄 {job['name']}")
                print(f"   Status: {job['status']}")
                print(f"   💰 Cost: ${job['cost_per_hour']:.2f}/hour")
                print(f"   ⏱️  Running for: {job['runtime_hours']:.2f} hours")
                print(f"   💸 Cost so far: ${job['estimated_cost_so_far']:.2f}")
                print(f"   📦 {job['instance_type']} x{job['instance_count']}")
                print()
                
                total_hourly_cost += job['cost_per_hour']
        else:
            print("✅ No active training jobs found")
        
        # Notebook Instances
        print(f"\n📓 NOTEBOOK INSTANCES ({len(notebook_instances)} active)")
        print("-" * 50)
        if notebook_instances:
            for nb in notebook_instances:
                print(f"📝 {nb['name']}")
                print(f"   Status: {nb['status']}")
                print(f"   💰 Cost: ${nb['cost_per_hour']:.2f}/hour | ${nb['daily_cost']:.2f}/day")
                print(f"   📦 {nb['instance_type']}")
                print()
                
                total_hourly_cost += nb['cost_per_hour']
        else:
            print("✅ No active notebook instances found")
        
        # S3 Storage
        print(f"\n💾 S3 STORAGE ({len(storage_info['buckets'])} SageMaker buckets)")
        print("-" * 50)
        if storage_info['buckets']:
            for bucket in storage_info['buckets']:
                print(f"🪣 {bucket['name']}")
                print(f"   📊 Size: {bucket['size_gb']:.2f} GB")
                print(f"   💰 Monthly cost: ${bucket['monthly_cost']:.2f}")
                print(f"   📁 Objects: {bucket['object_count']}")
                print()
        else:
            print("✅ No SageMaker-related buckets found")
        
        # API Gateway
        if api_info:
            print(f"\n🌐 API GATEWAY ({api_info['total_apis']} APIs found)")
            print("-" * 50)
            
            if api_info['rest_apis']:
                for api in api_info['rest_apis']:
                    cache_emoji = "🔄" if api['caching_enabled'] else "📡"
                    print(f"{cache_emoji} {api['name']} (REST API)")
                    print(f"   ID: {api['id']}")
                    print(f"   Stages: {', '.join(api['stages']) if api['stages'] else 'None'}")
                    if api['caching_enabled']:
                        print(f"   💰 Cache cost: ${api['cache_monthly_cost']:.2f}/month ({api['cache_size_gb']} GB)")
                    print(f"   📝 Description: {api['description'] or 'No description'}")
                    print()
            
            if api_info['http_apis']:
                for api in api_info['http_apis']:
                    print(f"🚀 {api['name']} (HTTP API)")
                    print(f"   ID: {api['id']}")
                    print(f"   Stages: {', '.join(api['stages']) if api['stages'] else 'None'}")
                    print(f"   📝 Description: {api['description'] or 'No description'}")
                    print()
            
            if api_info['websocket_apis']:
                for api in api_info['websocket_apis']:
                    print(f"🔌 {api['name']} (WebSocket API)")
                    print(f"   ID: {api['id']}")
                    print(f"   Stages: {', '.join(api['stages']) if api['stages'] else 'None'}")
                    print(f"   📝 Description: {api['description'] or 'No description'}")
                    print()
            
            if api_info['total_apis'] == 0:
                print("✅ No API Gateway APIs found")
            else:
                print(f"💡 API Gateway costs depend on usage:")
                print(f"   REST API: $3.50 per million requests")
                print(f"   HTTP API: $1.00 per million requests (cheaper)")
                print(f"   WebSocket: $1.00 per million messages + connection time")
        
        # Summary
        print("\n" + "="*80)
        print("💰 COST SUMMARY")
        print("="*80)
        print(f"🔥 ACTIVE COMPUTE CHARGES: ${total_hourly_cost:.2f}/hour")
        print(f"📅 Daily compute cost: ${total_hourly_cost * 24:.2f}")
        print(f"📊 Monthly compute cost: ${total_hourly_cost * 24 * 30:.2f}")
        print(f"💾 Monthly storage cost: ${storage_info['estimated_monthly_cost']:.2f}")
        
        api_monthly_cost = api_info['estimated_monthly_cost'] if api_info else 0
        if api_monthly_cost > 0:
            print(f"� Monthly API Gateway cost: ${api_monthly_cost:.2f}")
        
        total_monthly = (total_hourly_cost * 24 * 30) + storage_info['estimated_monthly_cost'] + api_monthly_cost
        print(f"🎯 TOTAL MONTHLY ESTIMATE: ${total_monthly:.2f}")
        
        if api_info and api_info['total_apis'] > 0:
            print(f"\n💡 API Gateway note: Costs shown are for caching only.")
            print(f"   Actual costs depend on request volume and data transfer.")
        
        if total_hourly_cost > 0:
            print(f"\n⚠️  WARNING: You have ${total_hourly_cost:.2f}/hour in active charges!")
            print(f"💸 This equals ~${total_hourly_cost * 24 * 30:.0f}/month if left running!")
        
        return total_hourly_cost
    
    def cleanup_resources(self, endpoints, training_jobs, notebook_instances):
        """Cleanup resources to stop charges."""
        print("\n" + "="*80)
        print("🧹 RESOURCE CLEANUP")
        print("="*80)
        
        total_savings = 0
        
        # Cleanup endpoints
        if endpoints:
            print(f"\n🚀 Cleaning up {len(endpoints)} endpoints...")
            for ep in endpoints:
                if ep['status'] == 'InService':
                    try:
                        print(f"🗑️  Deleting endpoint: {ep['name']}")
                        self.sagemaker_client.delete_endpoint(EndpointName=ep['name'])
                        
                        # Also delete endpoint config
                        try:
                            self.sagemaker_client.delete_endpoint_config(
                                EndpointConfigName=ep['config_name']
                            )
                            print(f"✅ Deleted endpoint and config: {ep['name']}")
                        except:
                            print(f"✅ Deleted endpoint: {ep['name']} (config may be shared)")
                        
                        total_savings += ep['total_cost_per_hour']
                        
                    except Exception as e:
                        print(f"❌ Error deleting {ep['name']}: {e}")
        
        # Stop training jobs
        if training_jobs:
            print(f"\n🏋️  Stopping {len(training_jobs)} training jobs...")
            for job in training_jobs:
                try:
                    print(f"⏹️  Stopping training job: {job['name']}")
                    self.sagemaker_client.stop_training_job(TrainingJobName=job['name'])
                    print(f"✅ Stopped: {job['name']}")
                    total_savings += job['cost_per_hour']
                    
                except Exception as e:
                    print(f"❌ Error stopping {job['name']}: {e}")
        
        # Stop notebook instances
        if notebook_instances:
            print(f"\n📓 Stopping {len(notebook_instances)} notebook instances...")
            for nb in notebook_instances:
                try:
                    print(f"⏹️  Stopping notebook: {nb['name']}")
                    self.sagemaker_client.stop_notebook_instance(
                        NotebookInstanceName=nb['name']
                    )
                    print(f"✅ Stopped: {nb['name']}")
                    total_savings += nb['cost_per_hour']
                    
                except Exception as e:
                    print(f"❌ Error stopping {nb['name']}: {e}")
        
        # Summary
        if total_savings > 0:
            print(f"\n💰 CLEANUP COMPLETE!")
            print(f"💸 Hourly savings: ${total_savings:.2f}")
            print(f"📅 Daily savings: ${total_savings * 24:.2f}")
            print(f"📊 Monthly savings: ${total_savings * 24 * 30:.2f}")
        else:
            print("\n✅ No active resources to cleanup - you're not being charged for compute!")
    
    def run_scan(self, cleanup: bool = False):
        """Run the complete scan."""
        print(f"🌍 Scanning AWS Region: {self.region_name}")
        print(f"🕐 Scan Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Perform scans
        endpoints = self.scan_endpoints()
        training_jobs = self.scan_training_jobs()
        notebook_instances = self.scan_notebook_instances()
        storage_info = self.scan_s3_storage()
        api_info = self.scan_api_gateways()
        
        # Print results
        total_hourly_cost = self.print_scan_results(
            endpoints, training_jobs, notebook_instances, storage_info, api_info
        )
        
        # Cleanup if requested
        if cleanup:
            if total_hourly_cost > 0:
                print(f"\n⚠️  You have ${total_hourly_cost:.2f}/hour in active charges!")
                confirm = input("\n🤔 Do you want to cleanup these resources? (yes/no): ").lower().strip()
                
                if confirm in ['yes', 'y']:
                    self.cleanup_resources(endpoints, training_jobs, notebook_instances)
                else:
                    print("❌ Cleanup cancelled - charges will continue")
            else:
                print("\n✅ No active compute resources found - no cleanup needed!")

def main():
    parser = argparse.ArgumentParser(
        description="AWS SageMaker Cost Scanner & Resource Cleanup Tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python cost_estimator_remove_resource.py --scan          # Scan only
  python cost_estimator_remove_resource.py --cleanup       # Scan and cleanup
  python cost_estimator_remove_resource.py --region us-west-2  # Specific region
        """
    )
    
    parser.add_argument(
        '--scan', 
        action='store_true', 
        help='Scan for chargeable resources (default action)'
    )
    
    parser.add_argument(
        '--cleanup', 
        action='store_true', 
        help='Scan and offer to cleanup resources'
    )
    
    parser.add_argument(
        '--region', 
        type=str, 
        help='AWS region to scan (auto-detected if not specified)'
    )
    
    parser.add_argument(
        '--json', 
        action='store_true', 
        help='Output results in JSON format'
    )
    
    args = parser.parse_args()
    
    # Default to scan if no action specified
    if not args.scan and not args.cleanup:
        args.scan = True
    
    try:
        scanner = SageMakerCostScanner(region_name=args.region)
        scanner.run_scan(cleanup=args.cleanup)
        
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
