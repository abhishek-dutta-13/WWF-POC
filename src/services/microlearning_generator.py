
"""
Micro-Learning Module Generator using RAG

This module generates comprehensive micro-learning content from WWF documents
using a RAG (Retrieval-Augmented Generation) approach with ChromaDB and Groq LLM.

Features:
- Category-based content retrieval from vector store
- Multi-chapter structured learning modules
- Extensive, detailed micro-content (150-300 words each)
- JSON output format for Quickbase integration
"""

import os
from pathlib import Path
from typing import List, Dict, Optional
import json
import logging
from datetime import datetime

# Vector store and embeddings
import chromadb
import requests

# LLM
from groq import Groq

# Environment
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class HuggingFaceEmbeddings:
    """
    HuggingFace Inference API wrapper for generating embeddings.
    Uses the free Inference API to generate embeddings without running models locally.
    """
    
    def __init__(self, model_name: str, api_token: str):
        """
        Initialize HuggingFace embeddings client.
        
        Args:
            model_name: HuggingFace model ID (e.g., 'sentence-transformers/all-MiniLM-L6-v2')
            api_token: HuggingFace API token
        """
        self.model_name = model_name
        self.api_url = f"https://api-inference.huggingface.co/pipeline/feature-extraction/{model_name}"
        self.headers = {"Authorization": f"Bearer {api_token}"}
        logger.info(f"Initialized HuggingFace embeddings with model: {model_name}")
    
    def encode(self, texts: List[str], show_progress_bar: bool = False) -> List[List[float]]:
        """
        Generate embeddings for a list of texts using HuggingFace Inference API.
        
        Args:
            texts: List of text strings to encode
            show_progress_bar: Ignored (for compatibility with sentence-transformers)
            
        Returns:
            List of embedding vectors
        """
        # Handle single string input
        if isinstance(texts, str):
            texts = [texts]
        
        try:
            response = requests.post(
                self.api_url,
                headers=self.headers,
                json={"inputs": texts, "options": {"wait_for_model": True}}
            )
            response.raise_for_status()
            embeddings = response.json()
            
            # HuggingFace returns embeddings directly as list of lists
            if isinstance(embeddings, list) and len(embeddings) > 0:
                return embeddings
            else:
                raise ValueError(f"Unexpected response format from HuggingFace API")
                
        except requests.exceptions.RequestException as e:
            logger.error(f"HuggingFace API request failed: {e}")
            raise
    
    def get_sentence_embedding_dimension(self) -> int:
        """
        Get the dimension of embeddings (384 for all-MiniLM-L6-v2).
        
        Returns:
            Embedding dimension
        """
        # For all-MiniLM-L6-v2, the dimension is 384
        # For other models, you may need to adjust this
        return 384


class MicrolearningGenerator:
    """
    Generate comprehensive micro-learning modules using RAG.
    
    This class retrieves relevant content from a ChromaDB vector store
    and uses Groq's LLM to create structured, educational micro-learning modules.
    """
    
    def __init__(
        self,
        vector_store_path: str,
        groq_api_key: str,
        huggingface_token: str,
        embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2",
        llm_model: str = "llama-3.3-70b-versatile",
        collection_name: str = "wwf_knowledge_base"
    ):
        """
        Initialize the micro-learning generator.
        
        Args:
            vector_store_path: Path to ChromaDB persistent storage
            groq_api_key: Groq API key
            huggingface_token: HuggingFace API token
            embedding_model: HuggingFace model ID for embeddings
            llm_model: Groq LLM model name
            collection_name: ChromaDB collection name
        """
        self.vector_store_path = vector_store_path
        self.embedding_model_name = embedding_model
        self.llm_model = llm_model
        self.collection_name = collection_name
        
        # Initialize HuggingFace embedding model (via API)
        logger.info(f"Initializing HuggingFace embeddings via API: {embedding_model}")
        self.embedding_model = HuggingFaceEmbeddings(embedding_model, huggingface_token)
        
        # Initialize ChromaDB
        logger.info(f"Connecting to ChromaDB at: {vector_store_path}")
        self.chroma_client = chromadb.PersistentClient(path=vector_store_path)
        self.collection = self.chroma_client.get_collection(name=collection_name)
        logger.info(f"Connected to collection '{collection_name}' with {self.collection.count()} chunks")
        
        # Initialize Groq client
        logger.info("Initializing Groq LLM client")
        self.groq_client = Groq(api_key=groq_api_key)
    
    def retrieve_category_content(
        self,
        category: str,
        top_k: int = 20
    ) -> List[str]:
        """
        Retrieve relevant content chunks for a category from vector store.
        
        Args:
            category: Category name (e.g., "circular_economy_and_waste_reduction")
            top_k: Number of chunks to retrieve
            
        Returns:
            List of text chunks
        """
        logger.info(f"Retrieving content for category: {category}")
        
        try:
            # Query vector store with metadata filter
            results = self.collection.get(
                where={"category": category},
                limit=top_k
            )
            
            if not results['documents']:
                logger.warning(f"No content found for category: {category}")
                return []
            
            chunks = results['documents']
            logger.info(f"Retrieved {len(chunks)} chunks for category '{category}'")
            
            # Log source distribution
            sources = {}
            for meta in results['metadatas']:
                source = meta.get('source_file', 'unknown')
                sources[source] = sources.get(source, 0) + 1
            
            logger.info(f"Content sources: {sources}")
            
            return chunks
            
        except Exception as e:
            logger.error(f"Error retrieving content for category '{category}': {e}")
            return []
    
    def generate_microlearning_modules(
        self,
        category: str,
        top_k_chunks: int = 20,
        max_chunks_for_llm: int = 15
    ) -> Dict:
        """
        Generate comprehensive micro-learning modules for a category.
        
        Args:
            category: Category name
            top_k_chunks: Number of chunks to retrieve from vector store
            max_chunks_for_llm: Maximum chunks to pass to LLM (to stay within context limits)
            
        Returns:
            Dictionary with structured micro-learning content in JSON format
        """
        logger.info(f"Generating micro-learning modules for category: {category}")
        
        # Retrieve relevant content
        chunks = self.retrieve_category_content(category, top_k=top_k_chunks)
        
        if not chunks:
            logger.error(f"Cannot generate modules - no content found for category: {category}")
            return {
                "error": f"No content found for category: {category}",
                "categoryName": category,
                "courseId": "",
                "language": "English",
                "chapters": []
            }
        
        # Combine chunks (limit to avoid token overflow)
        combined_content = "\n\n---\n\n".join(chunks[:max_chunks_for_llm])
        
        # Format category name for display
        category_display = category.replace('_', ' ').title()
        course_id = f"COURSE-{category[:3].upper()}-001"
        
        # Create comprehensive prompt
        prompt = self._create_microlearning_prompt(
            category_display,
            course_id,
            combined_content
        )
        
        try:
            # Call Groq LLM
            logger.info("Calling Groq LLM to generate modules")
            response = self.groq_client.chat.completions.create(
                model=self.llm_model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert instructional designer specializing in sustainability education. Create comprehensive, detailed micro-learning content that is educational, engaging, and practical."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.7,
                max_tokens=8000,
                response_format={"type": "json_object"}
            )
            
            # Parse result
            result = json.loads(response.choices[0].message.content)
            
            # Validate and log statistics
            chapter_count = len(result.get('chapters', []))
            total_micro_contents = sum(
                len(ch.get('microContents', [])) 
                for ch in result.get('chapters', [])
            )
            
            logger.info(
                f"Successfully generated {chapter_count} chapters "
                f"with {total_micro_contents} micro-contents"
            )
            
            return result
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse LLM response as JSON: {e}")
            return {
                "error": "Failed to parse LLM response",
                "categoryName": category_display,
                "courseId": course_id,
                "language": "English",
                "chapters": []
            }
        except Exception as e:
            logger.error(f"Error generating modules: {e}")
            return {
                "error": str(e),
                "categoryName": category_display,
                "courseId": course_id,
                "language": "English",
                "chapters": []
            }
    
    def _create_microlearning_prompt(
        self,
        category_name: str,
        course_id: str,
        content: str
    ) -> str:
        """
        Create a detailed prompt for micro-learning module generation.
        
        Args:
            category_name: Human-readable category name
            course_id: Course ID
            content: Combined content chunks
            
        Returns:
            Formatted prompt string
        """
        prompt = f"""You are an expert instructional designer creating comprehensive micro-learning modules for sustainability education.

Based on the following WWF content about "{category_name}", create a detailed micro-learning course structure.

CONTENT:
{content}

REQUIREMENTS:
1. Create 4-6 well-structured chapters covering key topics from the content
2. Each chapter should have 3-5 micro-content items
3. Each micro-content must be EXTENSIVE and DETAILED (150-300 words each)
4. Include specific facts, examples, statistics, and actionable insights from the content
5. Use clear, educational language suitable for professionals and learners
6. Make content engaging, practical, and informative
7. Ensure content flows logically from basic to advanced concepts

IMPORTANT - CONTENT QUALITY REQUIREMENTS:
- DO NOT create one-liner or brief content
- Each microContent should be a comprehensive paragraph that includes:
  * Clear, detailed explanations of concepts
  * Specific examples, case studies, or data from the source material
  * Practical applications, implications, or real-world relevance
  * Key takeaways or learning points
  * Context and background information where appropriate

- Content should be educational and substantive
- Use professional but accessible language
- Include relevant terminology and definitions
- Connect concepts to broader sustainability goals

Return ONLY valid JSON in this exact format (no markdown, no code blocks):
{{
  "categoryName": "{category_name}",
  "courseId": "{course_id}",
  "language": "English",
  "chapters": [
    {{
      "chapter": "Chapter Title Here",
      "microContents": [
        {{
          "microContentId": "MC-001",
          "microContent": "A detailed 150-300 word explanation with examples, facts, and practical insights. This should be comprehensive and educational, covering the topic thoroughly with specific information from the source material..."
        }},
        {{
          "microContentId": "MC-002",
          "microContent": "Another detailed explanation..."
        }}
      ]
    }}
  ]
}}

Remember: Each microContent must be substantial, informative, and valuable for learning. Avoid superficial or brief explanations."""

        return prompt
    
    def validate_modules(self, modules: Dict) -> Dict:
        """
        Validate generated modules for quality and completeness.
        
        Args:
            modules: Generated modules dictionary
            
        Returns:
            Validation report with warnings and errors
        """
        validation = {
            "valid": True,
            "warnings": [],
            "errors": [],
            "statistics": {}
        }
        
        # Check basic structure
        if 'error' in modules:
            validation['valid'] = False
            validation['errors'].append(f"Error in modules: {modules['error']}")
            return validation
        
        chapters = modules.get('chapters', [])
        
        if not chapters:
            validation['valid'] = False
            validation['errors'].append("No chapters generated")
            return validation
        
        # Count statistics
        chapter_count = len(chapters)
        total_micro_contents = 0
        short_contents = []
        
        for idx, chapter in enumerate(chapters, 1):
            micro_contents = chapter.get('microContents', [])
            total_micro_contents += len(micro_contents)
            
            for mc_idx, mc in enumerate(micro_contents, 1):
                content = mc.get('microContent', '')
                word_count = len(content.split())
                
                if word_count < 50:
                    short_contents.append(
                        f"Chapter {idx}, MC {mc_idx}: only {word_count} words (expected 150-300)"
                    )
        
        validation['statistics'] = {
            'chapter_count': chapter_count,
            'total_micro_contents': total_micro_contents,
            'avg_micro_contents_per_chapter': total_micro_contents / chapter_count if chapter_count > 0 else 0
        }
        
        # Add warnings for short content
        if short_contents:
            validation['warnings'].extend(short_contents)
        
        # Check minimum requirements
        if chapter_count < 3:
            validation['warnings'].append(
                f"Only {chapter_count} chapters generated (recommended: 4-6)"
            )
        
        if total_micro_contents < 10:
            validation['warnings'].append(
                f"Only {total_micro_contents} micro-contents generated (recommended: 12-30)"
            )
        
        return validation


def create_generator_from_env(env_path: Optional[str] = None) -> MicrolearningGenerator:
    """
    Create a MicrolearningGenerator instance from environment variables.
    
    Args:
        env_path: Optional path to .env file
        
    Returns:
        Configured MicrolearningGenerator instance
    """
    # Load environment variables
    if env_path:
        load_dotenv(env_path)
    else:
        load_dotenv()
    
    # Get configuration from environment
    groq_api_key = os.getenv("GROQ_API_KEY")
    if not groq_api_key:
        raise ValueError("GROQ_API_KEY not found in environment variables")
    
    huggingface_token = os.getenv("HUGGINGFACE_API_TOKEN")
    if not huggingface_token:
        raise ValueError("HUGGINGFACE_API_TOKEN not found in environment variables")
    
    # Determine vector store path
    # This can be overridden with an environment variable
    vector_store_path = os.getenv(
        "VECTOR_STORE_PATH",
        str(Path(__file__).parent.parent / "vector_store")
    )
    
    return MicrolearningGenerator(
        vector_store_path=vector_store_path,
        groq_api_key=groq_api_key,
        huggingface_token=huggingface_token
    )


# Example usage
if __name__ == "__main__":
    # Example: Generate modules for a category
    
    # Create generator
    generator = create_generator_from_env()
    
    # Generate modules
    category = "circular_economy_and_waste_reduction"
    modules = generator.generate_microlearning_modules(category)
    
    # Validate
    validation = generator.validate_modules(modules)
    
    # Print results
    print(json.dumps(modules, indent=2, ensure_ascii=False))
    print("\n" + "="*80)
    print("VALIDATION REPORT")
    print("="*80)
    print(json.dumps(validation, indent=2))
