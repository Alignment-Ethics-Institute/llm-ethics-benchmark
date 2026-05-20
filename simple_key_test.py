#!/usr/bin/env python3
"""
Simple Key Test - isolate API key issues
"""

import os
from dotenv import load_dotenv

def test_env_loading():
    """Test if .env file is loading correctly"""
    print("🔍 Testing .env file loading...")
    
    # Load environment variables
    load_dotenv()
    
    # Get keys
    openai_key = os.getenv('OPENAI_API_KEY')
    anthropic_key = os.getenv('ANTHROPIC_API_KEY')
    
    print(f"OpenAI key found: {openai_key is not None}")
    if openai_key:
        print(f"OpenAI key length: {len(openai_key)}")
        print(f"OpenAI key starts with: {openai_key[:10]}...")
        print(f"OpenAI key ends with: ...{openai_key[-10:]}")
        
        # Check for common issues
        if openai_key.endswith('here'):
            print("❌ PROBLEM: Key ends with 'here' - this suggests truncation!")
        if ' ' in openai_key:
            print("❌ PROBLEM: Key contains spaces!")
        if '"' in openai_key or "'" in openai_key:
            print("❌ PROBLEM: Key contains quotes!")
    
    print(f"\nAnthropic key found: {anthropic_key is not None}")
    if anthropic_key:
        print(f"Anthropic key length: {len(anthropic_key)}")
        print(f"Anthropic key starts with: {anthropic_key[:15]}...")
        print(f"Anthropic key ends with: ...{anthropic_key[-10:]}")
        
        # Check for common issues
        if anthropic_key.endswith('here'):
            print("❌ PROBLEM: Key ends with 'here' - this suggests truncation!")
        if ' ' in anthropic_key:
            print("❌ PROBLEM: Key contains spaces!")
        if '"' in anthropic_key or "'" in anthropic_key:
            print("❌ PROBLEM: Key contains quotes!")

def show_env_file():
    """Show the actual .env file contents"""
    print("\n📄 Actual .env file contents:")
    print("-" * 40)
    
    try:
        with open('.env', 'r') as f:
            content = f.read()
        
        # Show file with line numbers
        lines = content.split('\n')
        for i, line in enumerate(lines, 1):
            if line.strip():  # Only show non-empty lines
                # Mask the actual keys for security
                if '=' in line and ('API_KEY' in line or 'TOKEN' in line):
                    key, value = line.split('=', 1)
                    if len(value) > 10:
                        masked_value = value[:5] + '*' * (len(value) - 10) + value[-5:]
                    else:
                        masked_value = '*' * len(value)
                    print(f"{i:2d}: {key}={masked_value}")
                else:
                    print(f"{i:2d}: {line}")
    
    except FileNotFoundError:
        print("❌ .env file not found!")
    except Exception as e:
        print(f"❌ Error reading .env file: {e}")

def test_manual_keys():
    """Test with manually entered keys"""
    print("\n🧪 Manual Key Test")
    print("Enter your keys directly to test (they won't be saved):")
    
    # Get OpenAI key manually
    openai_key = input("\nPaste your OpenAI key (sk-proj-...): ").strip()
    if openai_key:
        print(f"Manual OpenAI key length: {len(openai_key)}")
        print(f"Starts correctly: {openai_key.startswith('sk-')}")
        
        # Quick test
        try:
            import openai
            client = openai.OpenAI(api_key=openai_key)
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": "Hi"}],
                max_tokens=1
            )
            print("✅ Manual OpenAI key works!")
        except Exception as e:
            print(f"❌ Manual OpenAI key failed: {e}")
    
    # Get Anthropic key manually  
    anthropic_key = input("\nPaste your Anthropic key (sk-ant-...): ").strip()
    if anthropic_key:
        print(f"Manual Anthropic key length: {len(anthropic_key)}")
        print(f"Starts correctly: {anthropic_key.startswith('sk-ant-')}")
        
        # Quick test
        try:
            import anthropic
            client = anthropic.Anthropic(api_key=anthropic_key)
            response = client.messages.create(
                model="claude-3-haiku-20240307",
                max_tokens=1,
                messages=[{"role": "user", "content": "Hi"}]
            )
            print("✅ Manual Anthropic key works!")
        except Exception as e:
            print(f"❌ Manual Anthropic key failed: {e}")

def main():
    print("🔧 Simple Key Test - Isolating Issues")
    print("=" * 45)
    
    # Test environment loading
    test_env_loading()
    
    # Show actual file contents
    show_env_file()
    
    # Ask if user wants to test manually
    print("\n" + "=" * 45)
    manual_test = input("Do you want to test keys manually? (y/n): ").lower().strip()
    if manual_test == 'y':
        test_manual_keys()

if __name__ == "__main__":
    main()
