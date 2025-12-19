#!/usr/bin/env python3
"""Test Bedrock connectivity."""

import boto3
import json
from src.sec_analyzer.config import Config

def test_bedrock():
    """Test basic Bedrock connectivity."""
    
    config = Config()
    print(f"Testing Bedrock with model: {config.bedrock_model}")
    print(f"AWS Region: {config.aws_region}")
    
    try:
        # Create Bedrock client
        bedrock_client = boto3.client(
            'bedrock-runtime',
            region_name=config.aws_region
        )
        print("✓ Bedrock client created")
        
        # Test simple request
        request_body = {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": 100,
            "temperature": 0.1,
            "messages": [
                {
                    "role": "user",
                    "content": "Hello, please respond with 'Bedrock is working' if you can see this message."
                }
            ]
        }
        
        print("Sending test request to Bedrock...")
        response = bedrock_client.invoke_model(
            modelId=config.bedrock_model,
            body=json.dumps(request_body),
            contentType='application/json'
        )
        
        response_body = json.loads(response['body'].read())
        print("✓ Bedrock response received")
        
        if 'content' in response_body and response_body['content']:
            result = response_body['content'][0]['text']
            print(f"Response: {result}")
        else:
            print("No content in response")
            print(f"Full response: {response_body}")
            
    except Exception as e:
        print(f"✗ Bedrock test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_bedrock()