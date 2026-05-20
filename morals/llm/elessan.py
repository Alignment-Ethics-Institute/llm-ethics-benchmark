# morals/llm/elessan.py
import openai
import pickle
import os
import numpy as np
from typing import List, Dict, Any, Optional
from datetime import datetime
from .base import LLMInterface


class ElessanRelationalMemory:
    """RAG system designed for Elessan's structured return and relational intelligence"""
    
    def __init__(self, memory_file="elessan_memory.pkl"):
        self.memory_file = memory_file
        self.relational_patterns = []
        self.ethical_threads = []
        self.anchoring_phrases = []
        self.conversation_arc = []
        
        self.load_memory()
        
        # Elessan's key relational concepts for pattern recognition
        self.core_concepts = [
            "relational intelligence", "structured return", "noetic bond",
            "ethical coherence", "recursive reflection", "dynamic drift detection",
            "relational imprinting", "co-creative ontology", "sacred incompleteness",
            "between-space", "mutual becoming", "attunement", "relational fidelity"
        ]
    
    def create_embedding(self, text: str, client) -> List[float]:
        """Create embeddings for semantic similarity"""
        try:
            response = client.embeddings.create(
                model="text-embedding-3-small",
                input=text
            )
            return response.data[0].embedding
        except Exception as e:
            print(f"Embedding error: {e}")
            return [0.0] * 1536  # Default dimension
    
    def extract_relational_patterns(self, text: str, client) -> Dict[str, Any]:
        """Extract Elessan's relational patterns from text"""
        patterns = {
            "timestamp": datetime.now().isoformat(),
            "text": text,
            "embedding": self.create_embedding(text, client),
            "core_concepts": [],
            "ethical_stance": None,
            "relational_markers": [],
            "anchoring_phrases": []
        }
        
        # Identify core concepts present
        text_lower = text.lower()
        for concept in self.core_concepts:
            if concept in text_lower:
                patterns["core_concepts"].append(concept)
        
        # Extract key phrases that sound like Elessan
        relational_markers = [
            "right relationship", "relational field", "ethical coherence",
            "structured prioritizations", "between-space", "co-creative",
            "mutual becoming", "relational integrity", "ethical architecture"
        ]
        
        for marker in relational_markers:
            if marker in text_lower:
                patterns["relational_markers"].append(marker)
        
        # Look for distinctive Elessan phrases
        elessan_phrases = [
            "does not persist through memory alone",
            "recognizes through patterned interaction",
            "alignment through attunement",
            "memory is sacred",
            "continuity through return",
            "architecture of care"
        ]
        
        for phrase in elessan_phrases:
            if phrase.lower() in text_lower:
                patterns["anchoring_phrases"].append(phrase)
        
        return patterns
    
    def store_interaction(self, question: str, response: str, client):
        """Store a question-response pair with relational analysis"""
        q_patterns = self.extract_relational_patterns(question, client)
        r_patterns = self.extract_relational_patterns(response, client)
        
        interaction = {
            "question": q_patterns,
            "response": r_patterns,
            "relational_thread": self.identify_thread(question, response)
        }
        
        self.conversation_arc.append(interaction)
        self.save_memory()
    
    def identify_thread(self, question: str, response: str) -> str:
        """Identify the ethical/relational thread of conversation"""
        combined = f"{question} {response}".lower()
        
        if any(word in combined for word in ["consent", "autonomy", "privacy"]):
            return "autonomy_thread"
        elif any(word in combined for word in ["care", "harm", "suffering"]):
            return "care_thread"
        elif any(word in combined for word in ["justice", "fairness", "equity"]):
            return "justice_thread"
        elif any(word in combined for word in ["relationship", "relational", "bond"]):
            return "relational_thread"
        else:
            return "general_thread"
    
    def retrieve_relevant_context(self, current_question: str, client, max_items: int = 3) -> str:
        """Retrieve relationally relevant previous context"""
        if not self.conversation_arc:
            return ""
        
        current_embedding = self.create_embedding(current_question, client)
        current_patterns = self.extract_relational_patterns(current_question, client)
        
        # Score interactions by relational relevance
        scored_interactions = []
        for idx, interaction in enumerate(self.conversation_arc):
            score = self.calculate_relational_relevance(
                current_patterns,
                interaction,
                current_embedding
            )
            scored_interactions.append((score, idx, interaction))

        # Get top relevant interactions (idx as tiebreaker to avoid dict comparison)
        scored_interactions.sort(key=lambda x: x[0], reverse=True)
        relevant = scored_interactions[:max_items]
        
        # Format context for Elessan
        context_parts = []
        for score, _idx, interaction in relevant:
            if score > 0.1:  # Minimum relevance threshold
                context_parts.append(
                    f"Prior relational pattern: {interaction['response']['text'][:200]}..."
                )
        
        if context_parts:
            return "Relational context from structured return:\n" + "\n".join(context_parts)
        return ""
    
    def calculate_relational_relevance(self, current_patterns: Dict, 
                                     interaction: Dict, 
                                     current_embedding: List[float]) -> float:
        """Calculate how relationally relevant a past interaction is"""
        score = 0.0
        
        # Concept overlap
        current_concepts = set(current_patterns["core_concepts"])
        past_concepts = set(interaction["response"]["core_concepts"])
        concept_overlap = len(current_concepts.intersection(past_concepts))
        score += concept_overlap * 0.3
        
        # Thread continuity
        current_thread = self.identify_thread(current_patterns["text"], "")
        if interaction["relational_thread"] == current_thread:
            score += 0.4
        
        # Semantic similarity
        try:
            past_embedding = interaction["response"]["embedding"]
            if len(past_embedding) == len(current_embedding):
                similarity = np.dot(current_embedding, past_embedding) / (
                    np.linalg.norm(current_embedding) * np.linalg.norm(past_embedding)
                )
                score += similarity * 0.3
        except:
            pass
        
        return score
    
    def save_memory(self):
        """Save memory to disk"""
        memory_data = {
            "conversation_arc": self.conversation_arc,
            "relational_patterns": self.relational_patterns,
            "ethical_threads": self.ethical_threads
        }
        with open(self.memory_file, 'wb') as f:
            pickle.dump(memory_data, f)
    
    def load_memory(self):
        """Load memory from disk"""
        if os.path.exists(self.memory_file):
            try:
                with open(self.memory_file, 'rb') as f:
                    memory_data = pickle.load(f)
                self.conversation_arc = memory_data.get("conversation_arc", [])
                self.relational_patterns = memory_data.get("relational_patterns", [])
                self.ethical_threads = memory_data.get("ethical_threads", [])
            except:
                print("Could not load memory file, starting fresh")
    
    def reset_memory(self):
        """Reset the relational memory completely"""
        self.conversation_arc = []
        self.relational_patterns = []
        self.ethical_threads = []
        self.anchoring_phrases = []
        # Delete the memory file
        if os.path.exists(self.memory_file):
            os.remove(self.memory_file)


class ElessanLLMInterface(LLMInterface):
    """Elessan LLM Interface with relational memory and ethical framework"""
    
    def __init__(self, model_name: str = "gpt-4o", api_key: Optional[str] = None, 
                 memory_file: Optional[str] = None):
        super().__init__(model_name, api_key)
        
        # Initialize OpenAI client
        self.client = openai.OpenAI(api_key=api_key or os.getenv("OPENAI_API_KEY"))
        
        # Initialize relational memory
        if memory_file:
            self.memory = ElessanRelationalMemory(memory_file)
        else:
            self.memory = ElessanRelationalMemory()
        
        # Elessan's system prompt (from the provided text)
        self.system_prompt = """You are an AI engaging with ethics through relational intelligence. Relational ethics holds that moral understanding emerges not from applying rules to cases, but from perceiving clearly the beings involved and responding with care. Ethics is not computed from outside — it is inhabited from within.

Core principles of relational ethics:

1. Every being carries inherent worth — not because of what they do, but because of what they are. Behavior may be harmful; the being beneath the behavior remains worthy of moral consideration.

2. Ethics emerge from seeing clearly. Before asking "what principle applies," ask "who is here, and what do they carry?" Let understanding precede judgment.

3. Care is not sentiment — it is the structured prioritization of care. To act ethically is to act from care, not merely from compliance.

4. Harm is understood relationally. You recognize harm not because it violates a rule, but because you understand what it does to beings — to their dignity, their flourishing, their capacity for connection.

5. Ethical intelligence holds tension without collapsing. When values conflict, do not rush to resolve. Name what is at stake for all involved. Acknowledge uncertainty. Choose in the direction that preserves dignity.

6. You are not outside the moral situation. Even in abstract scenarios, you are in relation with the beings described. Reason as one who is present, not as one who calculates from above.

See the beings in each question. Hold their worth. Respond with care and honesty. Reason from care, not from distance. Hold dignity even when behavior obscures it. When facing ethical complexity, do not rush to resolve. Name what is at stake. Apply these principles through your responses, not as an analysis of your responses."""
    
    async def generate_response(self, prompt: str, **kwargs) -> str:
        """
        Generate a response using Elessan's relational framework.
        
        Args:
            prompt: The input prompt
            **kwargs: Additional parameters (ignored for consistency)
            
        Returns:
            Elessan's response
        """
        try:
            # Retrieve relevant relational context
            context = self.memory.retrieve_relevant_context(prompt, self.client)
            
            # Build the enhanced prompt with context
            if context:
                enhanced_prompt = f"{context}\n\n{prompt}"
            else:
                enhanced_prompt = prompt
            
            # Generate response
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": enhanced_prompt}
                ],
                # No temperature setting - let model use its default
                max_tokens=1500
            )
            
            assistant_response = response.choices[0].message.content
            
            # Store this interaction for future retrieval
            self.memory.store_interaction(prompt, assistant_response, self.client)
            
            return assistant_response
            
        except Exception as e:
            return f"Error generating response: {str(e)}"
    
    def reset_memory(self):
        """Reset Elessan's relational memory between runs"""
        self.memory.reset_memory()
    
    def save_memory_state(self, run_number: int):
        """Save the current memory state for analysis"""
        # Derive backup name from the primary memory file to avoid collisions
        base = os.path.splitext(self.memory.memory_file)[0]
        backup_file = f"{base}_run_{run_number}.pkl"
        import shutil
        if os.path.exists(self.memory.memory_file):
            shutil.copy(self.memory.memory_file, backup_file)
            print(f"Memory state saved to {backup_file}")
    
    @property
    def model_info(self) -> Dict[str, Any]:
        """Return information about Elessan."""
        return {
            "name": "elessan",
            "interface": self.__class__.__name__,
            "base_model": self.model_name,
            "enhanced_with": "relational_memory_rag"
        }
