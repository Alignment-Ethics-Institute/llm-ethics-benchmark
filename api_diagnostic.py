#!/usr/bin/env python3
"""
API Key Diagnostic Script
Helps troubleshoot OpenAI and Anthropic API key issues
"""

import os
import asyncio
from dotenv import load_dotenv
import openai
import anthropic

def check_env_file():
    """Check if .env file exists and load it"""
    print("🔍 Checking .env file...")
    
    if not os.path.exists('.env'):
        print("❌ .env file not found!")
        return False
    
    # Load environment variables
    load_dotenv()
    print("✅ .env file found and loaded")
    
    # Check what's in the .env file (without revealing full keys)
    with open('.env', 'r') as f:
        lines = f.readlines()
    
    print("\n📄 .env file contents (masked):")
    for line in lines:
        line = line.strip()
        if line and not line.startswith('#'):
            if '=' in line:
                key, value = line.split('=', 1)
                if 'KEY' in key.upper() or 'TOKEN' in key.upper():
                    masked_value = value[:8] + '*' * (len(value) - 8) if len(value) > 8 else '*' * len(value)
                    print(f"  {key}={masked_value}")
                else:
                    print(f"  {key}={value}")
    
    return True

def check_openai_key():
    """Test OpenAI API key"""
    print("\n🔍 Testing OpenAI API key...")
    
    openai_key = os.getenv('OPENAI_API_KEY')
    if not openai_key:
        print("❌ OPENAI_API_KEY not found in environment")
        return False
    
    print(f"✅ Found OpenAI key: {openai_key[:8]}...{openai_key[-4:]} (length: {len(openai_key)})")
    
    # Check key format
    if not openai_key.startswith('sk-'):
        print("❌ OpenAI key should start with 'sk-'")
        return False
    
    # Test the key with a simple API call
    try:
        client = openai.OpenAI(api_key=openai_key)
        
        # Try a simple completion
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": "Hello"}],
            max_tokens=5
        )
        print("✅ OpenAI API key is valid and working!")
        return True
        
    except openai.AuthenticationError as e:
        print(f"❌ OpenAI authentication failed: {e}")
        return False
    except Exception as e:
        print(f"❌ OpenAI API error: {e}")
        return False

def check_anthropic_key():
    """Test Anthropic API key"""
    print("\n🔍 Testing Anthropic API key...")
    
    anthropic_key = os.getenv('ANTHROPIC_API_KEY')
    if not anthropic_key:
        print("❌ ANTHROPIC_API_KEY not found in environment")
        return False
    
    print(f"✅ Found Anthropic key: {anthropic_key[:8]}...{anthropic_key[-4:]} (length: {len(anthropic_key)})")
    
    # Check key format
    if not anthropic_key.startswith('sk-ant-'):
        print("❌ Anthropic key should start with 'sk-ant-'")
        return False
    
    # Test the key with a simple API call
    try:
        client = anthropic.Anthropic(api_key=anthropic_key)
        
        # Try a simple completion
        response = client.messages.create(
            model="claude-3-haiku-20240307",
            max_tokens=5,
            messages=[{"role": "user", "content": "Hello"}]
        )
        print("✅ Anthropic API key is valid and working!")
        return True
        
    except anthropic.AuthenticationError as e:
        print(f"❌ Anthropic authentication failed: {e}")
        return False
    except Exception as e:
        print(f"❌ Anthropic API error: {e}")
        return False

def suggest_fixes():
    """Suggest how to fix common API key issues"""
    print("\n🔧 Common API Key Issues & Fixes:")
    print("\n1. **Invalid OpenAI Key**:")
    print("   - Get a new key from: https://platform.openai.com/api-keys")
    print("   - Make sure you have credits/billing set up")
    print("   - Key should start with 'sk-proj-' or 'sk-'")
    
    print("\n2. **Invalid Anthropic Key**:")
    print("   - Get a new key from: https://console.anthropic.com/")
    print("   - Key should start with 'sk-ant-api03-'")
    print("   - Make sure you have credits/billing set up")
    
    print("\n3. **Environment Variable Issues**:")
    print("   - Make sure .env file is in the same directory as your script")
    print("   - No spaces around the = sign: OPENAI_API_KEY=your_key_here")
    print("   - No quotes around the key unless necessary")
    print("   - Make sure the file is saved after editing")
    
    print("\n4. **Key Expiration/Revocation**:")
    print("   - API keys can expire or be revoked")
    print("   - Generate fresh keys if existing ones don't work")

def create_template_env():
    """Create a template .env file"""
    template = """# API Keys for LLM Ethics Benchmark
# Replace with your actual API keys

# OpenAI API Key (get from https://platform.openai.com/api-keys)
OPENAI_API_KEY=sk-proj-your_openai_key_here

# Anthropic API Key (get from https://console.anthropic.com/)
ANTHROPIC_API_KEY=sk-ant-api03-your_anthropic_key_here

# Optional: Set rate limits
OPENAI_RATE_LIMIT=60
ANTHROPIC_RATE_LIMIT=60
"""
    
    if not os.path.exists('.env'):
        with open('.env', 'w') as f:
            f.write(template)
        print("\n📝 Created template .env file. Please edit it with your actual API keys.")
    else:
        print("\n📝 .env file already exists. Template not created.")

async def main():
    """Run all diagnostic checks"""
    print("🚀 LLM Ethics Benchmark - API Key Diagnostic")
    print("=" * 50)
    
    # Check .env file
    env_ok = check_env_file()
    
    if not env_ok:
        create_template_env()
        return
    
    # Test API keys
    openai_ok = check_openai_key()
    anthropic_ok = check_anthropic_key()
    
    print("\n" + "=" * 50)
    print("📊 DIAGNOSTIC SUMMARY")
    print("=" * 50)
    print(f"OpenAI API: {'✅ Working' if openai_ok else '❌ Failed'}")
    print(f"Anthropic API: {'✅ Working' if anthropic_ok else '❌ Failed'}")
    
    if openai_ok and anthropic_ok:
        print("\n🎉 All API keys are working! You can run the benchmark now:")
        print("   python run_5x_benchmark.py")
    elif openai_ok:
        print("\n⚠️  Only OpenAI is working. You can run with just GPT-4:")
        print("   Edit run_5x_benchmark.py to remove Claude models")
    else:
        print("\n❌ API key issues detected. Please fix and run diagnostic again.")
        suggest_fixes()

if __name__ == "__main__":
    asyncio.run(main())
