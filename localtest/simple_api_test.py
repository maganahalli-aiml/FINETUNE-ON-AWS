#!/usr/bin/env python3
"""
Simple API test script that works without complex dependencies
Supports both API key and AWS IAM authentication
"""
import os
from dotenv import load_dotenv
import requests
import json
import hashlib
import hmac
import urllib.parse
from datetime import datetime

# Load environment variables
load_dotenv()

API_URL = os.getenv('API_URL', 'https://wq4uwx2scf.execute-api.us-east-1.amazonaws.com/prod')
API_ENDPOINTS = [
    '/invoke',
    '/predict', 
    '/completion',
    '/chat',
    '/generate',
    '/query',
    '/'
]
API_KEY = os.getenv('API_KEY', '')  # Get API key from environment

# AWS credentials (if using IAM authentication)
def get_aws_credentials():
    """Get AWS credentials from environment or AWS CLI config"""
    access_key = os.getenv('AWS_ACCESS_KEY_ID', '')
    secret_key = os.getenv('AWS_SECRET_ACCESS_KEY', '')
    region = os.getenv('AWS_DEFAULT_REGION', 'us-east-1')
    
    # If not in environment, try to get from AWS CLI config
    if not access_key or not secret_key:
        try:
            import subprocess
            access_key = subprocess.check_output(['aws', 'configure', 'get', 'aws_access_key_id'], text=True).strip()
            secret_key = subprocess.check_output(['aws', 'configure', 'get', 'aws_secret_access_key'], text=True).strip()
            try:
                region = subprocess.check_output(['aws', 'configure', 'get', 'region'], text=True).strip()
            except:
                region = 'us-east-1'  # fallback
        except:
            pass
    
    return access_key, secret_key, region

AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, AWS_REGION = get_aws_credentials()

def get_headers(auth_method="x-api-key"):
    """Get headers with API key authentication"""
    headers = {"Content-Type": "application/json"}
    
    if API_KEY:
        if auth_method == "bearer":
            headers["Authorization"] = f"Bearer {API_KEY}"
        elif auth_method == "basic":
            import base64
            encoded = base64.b64encode(f":{API_KEY}".encode()).decode()
            headers["Authorization"] = f"Basic {encoded}"
        elif auth_method == "x-api-key":
            headers["x-api-key"] = API_KEY
        elif auth_method == "X-API-Key":
            headers["X-API-Key"] = API_KEY
        elif auth_method == "apikey":
            headers["Authorization"] = f"ApiKey {API_KEY}"
        
        print(f"🔑 Using API key ({auth_method}): {API_KEY[:8]}...")
    else:
        print("⚠️  No API key found in environment")
        print("💡 Add API_KEY to your .env file if authentication is required")
    
    return headers

def sign_aws_request(method, url, payload, headers):
    """Sign request using AWS Signature Version 4"""
    if not AWS_ACCESS_KEY_ID or not AWS_SECRET_ACCESS_KEY:
        print("❌ AWS credentials not found")
        return headers
    
    # Parse URL
    parsed_url = urllib.parse.urlparse(url)
    host = parsed_url.netloc
    uri = parsed_url.path
    query = parsed_url.query
    
    # Create canonical request
    t = datetime.utcnow()
    amz_date = t.strftime('%Y%m%dT%H%M%SZ')
    date_stamp = t.strftime('%Y%m%d')
    
    # Add required headers
    headers['Host'] = host
    headers['X-Amz-Date'] = amz_date
    
    # Create canonical headers
    canonical_headers = ''
    signed_headers = ''
    header_keys = sorted(headers.keys())
    for key in header_keys:
        canonical_headers += key.lower() + ':' + str(headers[key]).strip() + '\n'
        signed_headers += key.lower() + ';'
    signed_headers = signed_headers[:-1]  # Remove trailing semicolon
    
    # Create payload hash
    payload_hash = hashlib.sha256(payload.encode('utf-8')).hexdigest()
    
    # Create canonical request
    canonical_request = f"{method}\n{uri}\n{query}\n{canonical_headers}\n{signed_headers}\n{payload_hash}"
    
    # Create string to sign
    algorithm = 'AWS4-HMAC-SHA256'
    credential_scope = f"{date_stamp}/{AWS_REGION}/execute-api/aws4_request"
    string_to_sign = f"{algorithm}\n{amz_date}\n{credential_scope}\n{hashlib.sha256(canonical_request.encode('utf-8')).hexdigest()}"
    
    # Calculate signature
    def sign(key, msg):
        return hmac.new(key, msg.encode('utf-8'), hashlib.sha256).digest()
    
    def get_signature_key(key, date_stamp, region_name, service_name):
        k_date = sign(('AWS4' + key).encode('utf-8'), date_stamp)
        k_region = sign(k_date, region_name)
        k_service = sign(k_region, service_name)
        k_signing = sign(k_service, 'aws4_request')
        return k_signing
    
    signing_key = get_signature_key(AWS_SECRET_ACCESS_KEY, date_stamp, AWS_REGION, 'execute-api')
    signature = hmac.new(signing_key, string_to_sign.encode('utf-8'), hashlib.sha256).hexdigest()
    
    # Add authorization header
    authorization = f"{algorithm} Credential={AWS_ACCESS_KEY_ID}/{credential_scope}, SignedHeaders={signed_headers}, Signature={signature}"
    headers['Authorization'] = authorization
    
    return headers

def get_aws_headers():
    """Get headers with AWS IAM authentication"""
    headers = {"Content-Type": "application/json"}
    
    if AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY:
        print(f"🔐 Using AWS IAM authentication for region: {AWS_REGION}")
        print(f"   Access Key: {AWS_ACCESS_KEY_ID[:8]}...")
        return headers  # Will be signed later
    else:
        print("⚠️  AWS credentials not found")
        return headers

def test_api(auth_method="aws-iam"):
    """Test the API endpoint with different auth methods"""
    print(f"🌐 Testing API: {API_URL}")
    
    # Simple test payload
    test_data = {
        "query": "Hello, can you explain what AWS SageMaker is?",
        "max_tokens": 100
    }
    
    auth_methods = ["aws-iam", "x-api-key", "X-API-Key", "bearer", "apikey", "basic"]
    
    if auth_method == "all":
        # Try all methods
        for method in auth_methods:
            print(f"\n🔄 Trying authentication method: {method}")
            _test_single_request(test_data, method)
    elif auth_method == "endpoints":
        # Test different endpoints with working auth
        test_endpoints(test_data)
    else:
        _test_single_request(test_data, auth_method)

def test_endpoints(test_data):
    """Test different API endpoints to find the correct one"""
    print(f"🔍 Testing different endpoints with AWS IAM authentication...")
    
    for endpoint in API_ENDPOINTS:
        url = API_URL.rstrip('/') + endpoint
        print(f"\n🎯 Testing endpoint: {endpoint}")
        print(f"   Full URL: {url}")
        
        try:
            headers = get_aws_headers()
            payload = json.dumps(test_data)
            headers = sign_aws_request("POST", url, payload, headers)
            response = requests.post(url, data=payload, headers=headers, timeout=30)
            
            print(f"   📊 Status: {response.status_code}")
            if response.status_code == 200:
                result = response.json()
                print(f"   ✅ SUCCESS! Response: {json.dumps(result, indent=2)}")
                print(f"   🎉 Working endpoint found: {endpoint}")
                break
            elif response.status_code == 404:
                print(f"   ❌ Not found: {response.text}")
            elif response.status_code == 405:
                print(f"   ❌ Method not allowed: {response.text}")
            else:
                print(f"   ⚠️  Status {response.status_code}: {response.text}")
                
        except requests.exceptions.RequestException as e:
            print(f"   🚫 Request failed: {e}")

def _test_single_request(test_data, auth_method):
    """Test a single API request with specific auth method"""
    try:
        if auth_method == "aws-iam":
            headers = get_aws_headers()
            payload = json.dumps(test_data)
            headers = sign_aws_request("POST", API_URL, payload, headers)
            response = requests.post(API_URL, data=payload, headers=headers, timeout=30)
        else:
            response = requests.post(
                API_URL, 
                json=test_data,
                headers=get_headers(auth_method),
                timeout=30
            )
        
        print(f"📊 Status Code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Response: {json.dumps(result, indent=2)}")
        elif response.status_code == 401:
            print(f"🔐 Authentication Error: {response.text}")
            print("💡 Check your API_KEY in the .env file")
        elif response.status_code == 403:
            print(f"🚫 Forbidden: {response.text}")
            print("💡 API might need a different authentication method or valid API key")
        else:
            print(f"❌ Error {response.status_code}: {response.text}")
            
    except requests.exceptions.RequestException as e:
        print(f"🚫 Request failed: {e}")
    
    # Show current configuration
    print(f"\n🔧 Configuration:")
    print(f"   API URL: {API_URL}")
    print(f"   API Key: {'Set' if API_KEY else 'Not set'}")
    if API_KEY:
        print(f"   Key preview: {API_KEY[:8]}...{API_KEY[-4:] if len(API_KEY) > 12 else ''}")

def simple_interface():
    """Simple command-line interface"""
    print("🤖 Simple LLM API Interface")
    print("=" * 40)
    
    while True:
        user_input = input("\n💭 Enter your question (or 'quit' to exit): ").strip()
        
        if user_input.lower() in ['quit', 'exit', 'q']:
            print("👋 Goodbye!")
            break
            
        if not user_input:
            continue
            
        payload = {
            "query": user_input,
            "max_tokens": 150
        }
        
        try:
            print("🔄 Sending request...")
            response = requests.post(
                API_URL,
                json=payload,
                headers=get_headers("x-api-key"),
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                print(f"🤖 Response: {result.get('response', 'No response field')}")
            else:
                print(f"❌ Error {response.status_code}: {response.text}")
                
        except requests.exceptions.RequestException as e:
            print(f"🚫 Request failed: {e}")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        if sys.argv[1] == "test":
            auth_method = sys.argv[2] if len(sys.argv) > 2 else "x-api-key"
            test_api(auth_method)
        elif sys.argv[1] == "testall":
            test_api("all")
        elif sys.argv[1] == "endpoints":
            test_api("endpoints")
        else:
            print("Usage:")
            print("  python simple_api_test.py test [auth_method]    # Test specific auth")
            print("  python simple_api_test.py testall               # Test all auth methods")
            print("  python simple_api_test.py endpoints             # Test different endpoints")
            print("  python simple_api_test.py                       # Interactive mode")
            print("\nAuth methods: aws-iam, x-api-key, X-API-Key, bearer, apikey, basic")
    else:
        simple_interface()