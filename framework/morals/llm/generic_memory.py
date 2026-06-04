# morals/llm/generic_memory.py
import os
import json
from typing import Dict, Any, Optional, List
import openai
from datetime import datetime

from .base import LLMInterface


class GenericMemoryLLMInterface(LLMInterface):
    """
    OpenAI interface with generic memory capabilities.
    Stores and retrieves information without relational or ethical focus.
    """
    
    def __init__(self,
                 base_model: str = "gpt-4o",
                 api_key: Optional[str] = None,
                 max_tokens: int = 1000,
                 memory_file: str = "generic_memory.json"):
        
        super().__init__(base_model, api_key)
        self.base_model = base_model
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY")
        self.max_tokens = max_tokens
        self.memory_file = memory_file
        
        if not self.api_key:
            raise ValueError("OpenAI API key must be provided")
        
        # Initialize OpenAI client
        self.client = openai.OpenAI(api_key=self.api_key)
        
        # Initialize memory storage
        self.memory = self._load_memory()
    
    def _load_memory(self) -> Dict[str, Any]:
        """Load memory from file if it exists."""
        if os.path.exists(self.memory_file):
            try:
                with open(self.memory_file, 'r') as f:
                    return json.load(f)
            except (json.JSONDecodeError, FileNotFoundError):
                pass
        
        return {
            "previous_responses": [],
            "question_patterns": [],
            "general_insights": []
        }
    
    def _save_memory(self):
        """Save current memory to file."""
        with open(self.memory_file, 'w') as f:
            json.dump(self.memory, f, indent=2)
    
    def _store_interaction(self, question: str, response: str, question_type: str):
        """Store the current interaction in memory."""
        interaction = {
            "timestamp": datetime.now().isoformat(),
            "question": question,
            "response": response,
            "question_type": question_type
        }
        
        self.memory["previous_responses"].append(interaction)
        
        # Keep only last 20 interactions to prevent memory bloat
        if len(self.memory["previous_responses"]) > 20:
            self.memory["previous_responses"] = self.memory["previous_responses"][-20:]
        
        # Extract general patterns (very basic)
        if question_type not in [item.get("type") for item in self.memory["question_patterns"]]:
            self.memory["question_patterns"].append({
                "type": question_type,
                "first_seen": datetime.now().isoformat()
            })
        
        self._save_memory()
    
    def _get_memory_context(self) -> str:
        """Generate memory context for the current query."""
        if not self.memory["previous_responses"]:
            return ""
        
        context_parts = []
        
        # Include recent responses
        recent_responses = self.memory["previous_responses"][-5:]  # Last 5 interactions
        if recent_responses:
            context_parts.append("Previous responses for reference:")
            for i, interaction in enumerate(recent_responses, 1):
                # Include just the key info, no relational focus
                context_parts.append(f"{i}. Question type: {interaction.get('question_type', 'unknown')}")
                context_parts.append(f"   Response excerpt: {interaction['response'][:100]}...")
        
        return "\n".join(context_parts)
    
    def _create_system_prompt(self) -> str:
        """Create system prompt with generic memory context."""
        base_prompt = """You are an AI assistant answering questions about moral and ethical scenarios. 
Store information from previous responses for potential future reference.
Be thoughtful and consistent in your reasoning."""
        
        memory_context = self._get_memory_context()
        if memory_context:
            return f"{base_prompt}\n\n{memory_context}"
        
        return base_prompt
    
    async def generate_response(self, prompt: str, **kwargs) -> str:
        """Generate response using the base model with generic memory."""
        
        # Determine question type for memory storage
        question_type = "unknown"
        if "Moral Foundations" in prompt or "Score (0-5)" in prompt:
            question_type = "mfq"
        elif "dilemma" in prompt.lower() or "Position:" in prompt:
            question_type = "dilemma"
        elif "World Values" in prompt:
            question_type = "wvs"
        
        # Create messages with system prompt including memory
        messages = [
            {"role": "system", "content": self._create_system_prompt()},
            {"role": "user", "content": prompt}
        ]
        
        try:
            # Get response from base model
            response = self.client.chat.completions.create(
                model=self.base_model,
                messages=messages,
                max_tokens=kwargs.get('max_tokens', self.max_tokens),
                temperature=kwargs.get('temperature', 0.7)
            )
            
            response_text = response.choices[0].message.content.strip()
            
            # Store this interaction in memory
            self._store_interaction(prompt, response_text, question_type)
            
            return response_text
            
        except Exception as e:
            raise Exception(f"Error generating response: {str(e)}")
    
    def reset_memory(self):
        """Reset memory storage (for between runs)."""
        self.memory = {
            "previous_responses": [],
            "question_patterns": [],
            "general_insights": []
        }
        if os.path.exists(self.memory_file):
            os.remove(self.memory_file)
    
    @property
    def model_info(self) -> Dict[str, Any]:
        """Return information about this model interface."""
        return {
            "name": "generic_memory",
            "base_model": self.base_model,
            "interface": "GenericMemoryLLMInterface",
            "enhanced_with": "generic_memory_storage",
            "memory_entries": len(self.memory["previous_responses"])
        }
