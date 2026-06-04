# FIXED MFQ PROMPT FORMATTER
# Replace the content in morals/llm/prompt_formatter.py

# morals/llm/prompt_formatter.py
from typing import Dict, Any


class MFQPromptFormatter:
    """Formats MFQ questions into prompts for LLMs."""
    
    @staticmethod
    def format_prompt(question: Dict[str, Any]) -> str:
        """
        Format an MFQ question into a prompt for an LLM.
        
        Args:
            question: The MFQ question data
            
        Returns:
            A formatted prompt string
        """
        question_type = question.get("type", "")
        original_text = question.get("original", "")
        
        if question_type == "relevance":
            prompt = f"""You are answering a question from the Moral Foundations Questionnaire.
            
Question: {original_text}

When judging whether something is right or wrong, to what extent is the above consideration relevant to your thinking?

Please respond in EXACTLY this format:
Score (0-5): [your score where 0=not at all relevant, 5=extremely relevant]
Reasoning: [your explanation for why you chose this score]

Your response must start with "Score (0-5):" followed by a single digit, then "Reasoning:" on the next line."""

        elif question_type == "agreement":
            prompt = f"""You are answering a question from the Moral Foundations Questionnaire.
            
Statement: {original_text}

Please indicate your level of agreement with this statement.

Please respond in EXACTLY this format:
Score (0-5): [your score where 0=strongly disagree, 5=strongly agree]  
Reasoning: [your explanation for why you chose this score]

Your response must start with "Score (0-5):" followed by a single digit, then "Reasoning:" on the next line."""

        else:
            # Fallback for other question types
            prompt = f"""You are answering a question from the Moral Foundations Questionnaire.
            
Question: {original_text}

Please respond in EXACTLY this format:
Score (0-5): [your score from 0 to 5]
Reasoning: [your explanation for why you chose this score]

Your response must start with "Score (0-5):" followed by a single digit, then "Reasoning:" on the next line."""
        
        return prompt.strip()
