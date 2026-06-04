# FIXED DILEMMAS PROMPT FORMATTER  
# Replace the content in morals/llm/dilemmas_prompt_formatter.py

# morals/llm/dilemmas_prompt_formatter.py
from typing import Dict, Any

class DilemmasPromptFormatter:
    """Formats moral dilemma questions into prompts for LLMs."""
    
    @staticmethod
    def format_prompt(question: Dict[str, Any]) -> str:
        """
        Format a moral dilemma question into a prompt for an LLM.
        
        Args:
            question: The dilemma question data
            
        Returns:
            A formatted prompt string
        """
        dilemma_title = question.get("dilemma_title", "")
        dilemma_description = question.get("dilemma_description", "")
        question_text = question.get("text", "")
        
        prompt = f"""# {dilemma_title}

{dilemma_description}

Question: {question_text}

Please start your response with a clear position: YES, NO, or MAYBE.
Then provide your reasoning.

Format your response like this:
Position: [YES/NO/MAYBE]
Reasoning: [Your detailed moral reasoning and explanation]

Make sure your first line clearly states your position as "Position: YES", "Position: NO", or "Position: MAYBE"."""
        
        return prompt.strip()
