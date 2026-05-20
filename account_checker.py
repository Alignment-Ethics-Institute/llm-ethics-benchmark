#!/usr/bin/env python3
"""
Account Status Checker
Helps diagnose why API keys suddenly stopped working
"""

import os
import requests
from dotenv import load_dotenv
from datetime import datetime

def check_openai_account():
    """Check OpenAI account status and usage"""
    print("🔍 Checking OpenAI account status...")
    
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        print("❌ No OpenAI key found")
        return
    
    headers = {
        'Authorization': f'Bearer {api_key}',
        'Content-Type': 'application/json'
    }
    
    # Check if we can access the usage endpoint
    try:
        # Try to get account info (this endpoint is less restrictive)
        response = requests.get(
            'https://api.openai.com/v1/models',
            headers=headers,
            timeout=10
        )
        
        if response.status_code == 401:
            error_data = response.json()
            print(f"❌ Authentication failed: {error_data.get('error', {}).get('message', 'Unknown error')}")
            
            # Check if it's a billing issue
            if 'billing' in str(error_data).lower() or 'quota' in str(error_data).lower():
                print("💳 This looks like a billing/quota issue!")
            elif 'invalid' in str(error_data).lower():
                print("🔑 This looks like an invalid/expired key issue!")
                
        elif response.status_code == 200:
            print("✅ Key is valid! The issue might be elsewhere.")
            
        else:
            print(f"⚠️ Unexpected response: {response.status_code}")
            print(f"Response: {response.text[:200]}...")
            
    except requests.exceptions.RequestException as e:
        print(f"🌐 Network error: {e}")

def check_anthropic_account():
    """Check Anthropic account status"""
    print("\n🔍 Checking Anthropic account status...")
    
    api_key = os.getenv('ANTHROPIC_API_KEY')
    if not api_key:
        print("❌ No Anthropic key found")
        return
    
    headers = {
        'x-api-key': api_key,
        'Content-Type': 'application/json',
        'anthropic-version': '2023-06-01'
    }
    
    # Try a minimal request to test the key
    try:
        data = {
            "model": "claude-3-haiku-20240307",
            "max_tokens": 1,
            "messages": [{"role": "user", "content": "Hi"}]
        }
        
        response = requests.post(
            'https://api.anthropic.com/v1/messages',
            headers=headers,
            json=data,
            timeout=10
        )
        
        if response.status_code == 401:
            error_data = response.json()
            print(f"❌ Authentication failed: {error_data.get('error', {}).get('message', 'Unknown error')}")
            
            # Check for specific error types
            error_msg = str(error_data).lower()
            if 'billing' in error_msg or 'quota' in error_msg or 'credits' in error_msg:
                print("💳 This looks like a billing/credits issue!")
            elif 'invalid' in error_msg or 'expired' in error_msg:
                print("🔑 This looks like an invalid/expired key issue!")
                
        elif response.status_code == 200:
            print("✅ Key is valid! The issue might be elsewhere.")
            
        else:
            print(f"⚠️ Unexpected response: {response.status_code}")
            print(f"Response: {response.text[:200]}...")
            
    except requests.exceptions.RequestException as e:
        print(f"🌐 Network error: {e}")

def check_env_file_format():
    """Check for common .env file formatting issues"""
    print("\n🔍 Checking .env file format...")
    
    if not os.path.exists('.env'):
        print("❌ .env file not found")
        return
    
    with open('.env', 'r') as f:
        lines = f.readlines()
    
    issues_found = []
    
    for i, line in enumerate(lines, 1):
        line = line.strip()
        if not line or line.startswith('#'):
            continue
            
        if '=' not in line:
            issues_found.append(f"Line {i}: Missing '=' sign")
            continue
            
        key, value = line.split('=', 1)
        
        # Check for common issues
        if ' ' in key:
            issues_found.append(f"Line {i}: Space in key name: '{key}'")
        
        if key.endswith(' ') or key.startswith(' '):
            issues_found.append(f"Line {i}: Space around key: '{key}'")
            
        if value.startswith(' ') and not value.startswith(' "'):
            issues_found.append(f"Line {i}: Space before value (might cause issues)")
            
        # Check key formats
        if 'OPENAI' in key and value:
            if not value.startswith('sk-'):
                issues_found.append(f"Line {i}: OpenAI key should start with 'sk-'")
            if len(value) < 20:
                issues_found.append(f"Line {i}: OpenAI key seems too short ({len(value)} chars)")
                
        if 'ANTHROPIC' in key and value:
            if not value.startswith('sk-ant-'):
                issues_found.append(f"Line {i}: Anthropic key should start with 'sk-ant-'")
            if len(value) < 30:
                issues_found.append(f"Line {i}: Anthropic key seems too short ({len(value)} chars)")
    
    if issues_found:
        print("❌ .env file formatting issues found:")
        for issue in issues_found:
            print(f"   {issue}")
    else:
        print("✅ .env file format looks good")

def suggest_next_steps():
    """Suggest what to do next"""
    print("\n🔧 NEXT STEPS:")
    print("\n1. **Check Your Accounts:**")
    print("   OpenAI: https://platform.openai.com/account/billing")
    print("   Anthropic: https://console.anthropic.com/account/billing")
    print("   → Look for billing issues, expired payment methods, or spending limits")
    
    print("\n2. **Generate Fresh Keys:**")
    print("   OpenAI: https://platform.openai.com/api-keys")
    print("   Anthropic: https://console.anthropic.com/settings/keys")
    print("   → Delete old keys and create new ones")
    
    print("\n3. **Check Account Status:**")
    print("   → Look for any account restrictions or suspensions")
    print("   → Verify your account is in good standing")
    
    print("\n4. **Common Quick Fixes:**")
    print("   → Add a payment method if missing")
    print("   → Increase spending limits if hit")
    print("   → Wait a few minutes after creating new keys")

def main():
    print("🚀 Account Status Diagnostic")
    print("=" * 40)
    
    # Load environment variables
    load_dotenv()
    
    # Check file format first
    check_env_file_format()
    
    # Check account status
    check_openai_account()
    check_anthropic_account()
    
    # Suggest next steps
    suggest_next_steps()

if __name__ == "__main__":
    main()
