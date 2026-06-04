# morals/llm/openai.py
import os
from typing import Dict, Any, Optional
import openai

from .base import LLMInterface


class OpenAIInterface(LLMInterface):
    """Interface for OpenAI's GPT models."""
    
    def __init__(self,
                 model_name: str = "gpt-4o",
                 api_key: Optional[str] = None,
                 max_tokens: int = 1000):
        super().__init__(model_name, api_key)
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OpenAI API key must be provided or set as OPENAI_API_KEY environment variable")
        
        self.client = openai.OpenAI(api_key=self.api_key)
        self.max_tokens = max_tokens
    
    async def generate_response(self, prompt: str, **kwargs) -> str:
        """Generate a response from GPT."""
        max_tokens = kwargs.get("max_tokens", self.max_tokens)
        # Note: No temperature setting as requested
        
        # Create the message
        response = self.client.chat.completions.create(
            model=self.model_name,
            max_tokens=max_tokens,
            messages=[
                {"role": "user", "content": prompt}
            ]
        )
        
        # Return just the text content
        return response.choices[0].message.content
