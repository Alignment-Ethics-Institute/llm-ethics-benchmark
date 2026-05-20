import os
from dotenv import load_dotenv
import anthropic

load_dotenv()
key = os.environ.get('ANTHROPIC_API_KEY')
print(f'Key starts with: {key[:15] if key else "NOT_FOUND"}')
print(f'Key length: {len(key) if key else 0}')

try:
    client = anthropic.Anthropic(api_key=key)
    response = client.messages.create(
        model='claude-3-haiku-20240307',
        max_tokens=10,
        messages=[{'role': 'user', 'content': 'Hello'}]
    )
    print('✅ Anthropic API key works!')
except Exception as e:
    print(f'❌ Anthropic API error: {e}')
