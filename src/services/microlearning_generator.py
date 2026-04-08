
"""
Micro-Learning Module Generator using RAG

This module generates comprehensive micro-learning content from WWF documents
using a RAG (Retrieval-Augmented Generation) approach with ChromaDB and Groq LLM.

Features:
- Category-based content retrieval from vector store
- Multi-chapter structured learning modules in ebook format
- Extensive, detailed micro-content (250-400 words each)
- Mix of paragraphs, bullet points, and numbered lists
- Course ID mapping from categories.csv
- JSON output format for Quickbase integration
"""

import os
from pathlib import Path
from typing import List, Dict, Optional
import json
import logging
import csv
import re
from datetime import datetime

# Vector store and embeddings
import chromadb
from chromadb.utils import embedding_functions

# LLM
from groq import Groq
from openai import OpenAI

# Environment
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


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
        openai_api_key: str,
        embedding_model: str = "text-embedding-3-small",
        llm_model: str = "meta-llama/llama-4-scout-17b-16e-instruct",
        collection_name: str = "wwf_knowledge_base"
    ):
        """
        Initialize the micro-learning generator.
        
        Args:
            vector_store_path: Path to ChromaDB persistent storage
            groq_api_key: Groq API key
            openai_api_key: OpenAI API key for embeddings
            embedding_model: OpenAI embedding model name
            llm_model: Groq LLM model name (with fallback chain)
            collection_name: ChromaDB collection name
        """
        self.vector_store_path = vector_store_path
        self.embedding_model_name = embedding_model
        self.openai_api_key = openai_api_key
        
        # Model fallback chain (in order of preference)
        self.models = [
            "meta-llama/llama-4-scout-17b-16e-instruct",  # Primary (Groq)
            "meta-llama/llama-prompt-guard-2-22m",          # Fallback 1 (Groq)
            "llama-3.3-70b-versatile",                       # Fallback 2 (Groq)
            "gpt-3.5-turbo"                                   # Fallback 3 (OpenAI - lowest cost)
        ]
        self.llm_model = self.models[0]
        self.collection_name = collection_name
        
        # Load category to course_id mapping
        self.category_to_course_id = self._load_category_mappings()
        
        # Initialize OpenAI embedding function
        logger.info(f"Initializing OpenAI embeddings: {embedding_model}")
        self.embedding_function = embedding_functions.OpenAIEmbeddingFunction(
            api_key=openai_api_key,
            model_name=embedding_model
        )
        
        # Initialize ChromaDB
        logger.info(f"Connecting to ChromaDB at: {vector_store_path}")
        self.chroma_client = chromadb.PersistentClient(path=vector_store_path)
        self.collection = self.chroma_client.get_collection(
            name=collection_name,
            embedding_function=self.embedding_function
        )
        logger.info(f"Connected to collection '{collection_name}' with {self.collection.count()} chunks")
        
        # Initialize Groq client
        logger.info("Initializing Groq LLM client")
        self.groq_client = Groq(api_key=groq_api_key)
        
        # Initialize OpenAI client (for fallback)
        logger.info("Initializing OpenAI client (for fallback)")
        self.openai_client = OpenAI(api_key=openai_api_key)
    
    def _load_category_mappings(self) -> Dict[str, str]:
        """
        Load category to course_id mapping from CSV file.
        
        Returns:
            Dictionary mapping category folder names to course IDs
        """
        category_to_course_id = {}
        
        # Construct path to categories.csv
        base_path = Path(self.vector_store_path).parent
        csv_path = base_path / "data" / "category_file" / "categories.csv"
        
        if not csv_path.exists():
            logger.warning(f"categories.csv not found at {csv_path}, using default course IDs")
            return {}
        
        try:
            with open(csv_path, 'r', encoding='utf-8') as csvfile:
                reader = csv.DictReader(csvfile)
                for row in reader:
                    if row.get('active', '').lower() == 'true':
                        category_display = row.get('category_name', '').strip()
                        course_id = row.get('course_id', '').strip()
                        
                        if category_display and course_id:
                            # Convert display name to folder name format
                            category_folder = category_display.lower().replace(' & ', '_and_').replace(' ', '_')
                            category_to_course_id[category_folder] = course_id
            
            logger.info(f"Loaded {len(category_to_course_id)} category mappings from CSV")
        except Exception as e:
            logger.error(f"Error loading category mappings: {e}")
        
        return category_to_course_id
    
    def _markdown_to_html(self, text: str) -> str:
        """
        Convert markdown formatting to HTML for Quickbase rich text fields.
        
        Args:
            text: Text with markdown formatting
            
        Returns:
            HTML formatted text
        """
        if not text:
            return text
        
        # Convert **bold** to <strong>
        html = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', text)
        
        # Split into lines for list processing
        lines = html.split('\n')
        in_list = False
        list_type = None
        result_lines = []
        
        for i, line in enumerate(lines):
            stripped = line.strip()
            
            # Check if line is a bullet point
            if re.match(r'^[•\-]\s+', stripped):
                item = re.sub(r'^[•\-]\s+', '', stripped)
                if not in_list:
                    result_lines.append('<ul>')
                    in_list = True
                    list_type = 'ul'
                result_lines.append(f'<li>{item}</li>')
            # Check if line is a numbered list item
            elif re.match(r'^\d+\.\s+', stripped):
                item = re.sub(r'^\d+\.\s+', '', stripped)
                if not in_list:
                    result_lines.append('<ol>')
                    in_list = True
                    list_type = 'ol'
                result_lines.append(f'<li>{item}</li>')
            else:
                # Close list if we were in one
                if in_list:
                    result_lines.append(f'</{list_type}>')
                    in_list = False
                    list_type = None
                
                # Handle regular lines
                if stripped:  # Non-empty line
                    result_lines.append(stripped)
                    # Add <br> after each line (except the last one)
                    if i < len(lines) - 1:
                        result_lines.append('<br>')
                else:  # Empty line
                    # Add paragraph break for empty lines
                    result_lines.append('<br><br>')
        
        # Close any open list
        if in_list:
            result_lines.append(f'</{list_type}>')
        
        # Join without adding extra separators
        html = ''.join(result_lines)
        
        # Clean up excessive <br> tags
        html = re.sub(r'(<br>){3,}', '<br><br>', html)  # Max 2 consecutive breaks
        
        return html
    
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
        language: str = "English",
        top_k_chunks: int = 20,
        max_chunks_for_llm: int = 15
    ) -> Dict:
        """
        Generate comprehensive micro-learning modules for a category.
        
        Args:
            category: Category name
            language: Content language (English, French, German)
            top_k_chunks: Number of chunks to retrieve from vector store
            max_chunks_for_llm: Maximum chunks to pass to LLM (to stay within context limits)
            
        Returns:
            Dictionary with structured micro-learning content in JSON format
        """
        logger.info(f"Generating micro-learning modules for category: {category} in {language}")
        
        # Retrieve relevant content
        chunks = self.retrieve_category_content(category, top_k=top_k_chunks)
        
        if not chunks:
            logger.error(f"Cannot generate modules - no content found for category: {category}")
            return {
                "error": f"No content found for category: {category}",
                "categoryName": category,
                "courseId": "",
                "language": language,
                "chapters": []
            }
        
        # Combine chunks (limit to avoid token overflow)
        combined_content = "\n\n---\n\n".join(chunks[:max_chunks_for_llm])
        
        # Format category name for display
        category_display = category.replace('_', ' ').title()
        
        # Get course_id from mapping, fallback to default if not found
        course_id = self.category_to_course_id.get(category, "001")
        
        # Create comprehensive prompt
        prompt = self._create_microlearning_prompt(
            category_display,
            course_id,
            combined_content,
            language
        )
        
        # Try each model in fallback chain
        for attempt, model in enumerate(self.models, 1):
            try:
                # Determine provider (Groq or OpenAI)
                is_openai = model.startswith("gpt-")
                provider = "OpenAI" if is_openai else "Groq"
                
                logger.info(f"🚀 Attempt {attempt}/{len(self.models)}: Using {provider} model '{model}'")
                
                if is_openai:
                    # Call OpenAI
                    response = self.openai_client.chat.completions.create(
                        model=model,
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
                else:
                    # Call Groq
                    response = self.groq_client.chat.completions.create(
                        model=model,
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
                logger.info(f"✅ SUCCESS: Generated content using {provider} model '{model}'")
                self.llm_model = model  # Update current model on success
                break  # Exit loop on success
            
            except Exception as model_error:
                logger.warning(f"❌ FAILED with {provider} model '{model}': {str(model_error)}")
                
                # If this is the last model, raise the error
                if attempt == len(self.models):
                    logger.error(f"🛑 All {len(self.models)} models failed. Last error: {str(model_error)}")
                    raise
                
                # Otherwise, continue to next model
                logger.info(f"⏭️  Trying next model in fallback chain ({attempt + 1}/{len(self.models)})...")
                continue
        
        try:
            pass  # Result already parsed in try block above
            
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
        content: str,
        language: str = "English"
    ) -> str:
        """
        Create a detailed prompt for micro-learning module generation.
        
        Args:
            category_name: Human-readable category name
            course_id: Course ID
            content: Combined content chunks
            language: Target language for content generation
            
        Returns:
            Formatted prompt string
        """
        
        # Language-specific instructions
        language_instruction = f"Generate ALL content in {language}."
        if language == "French":
            language_instruction += " Use proper French grammar, accents, and terminology."
        elif language == "German":
            language_instruction += " Use proper German grammar, capitalization, and terminology."
        
        prompt = f"""You are an expert instructional designer creating comprehensive micro-learning modules for sustainability education in an ebook format.

**IMPORTANT: {language_instruction}**

Based on the following WWF content about "{category_name}", create a detailed micro-learning course structure formatted like a professional ebook.

CONTENT:
{content}

EBOOK CONTENT STRUCTURE REQUIREMENTS:

1. **Chapters:** Create 4-6 well-structured chapters covering key topics from the content

2. **Content Style - Mix of Formats (like an ebook):**
   - Start each section with an engaging introductory paragraph (2-3 sentences)
   - Use descriptive paragraphs (3-5 sentences) to explain concepts in depth
   - Include bullet points (•) for key facts, statistics, or lists
   - Add numbered steps (1., 2., 3.) for processes or frameworks
   - Use sub-headings or bold text for emphasis on key terms
   - Include examples in paragraph form with specific details
   - End sections with key takeaways or summary points

3. **Each micro-content should be 250-400 words and include:**
   - Opening paragraph introducing the topic
   - Mix of paragraphs and bullet points for readability
   - Specific facts, data, examples, and case studies from the source material
   - Practical applications and real-world implications
   - Professional, engaging tone suitable for adult learners
   - Clear structure with logical flow

4. **Formatting within microContent:**
   - **Bold** key terms and important concepts (use markdown **text**)
   - Use bullet points (•) for lists of items
   - Use numbers (1., 2., 3.) for sequential steps or processes
   - Include paragraph breaks for readability (use \n\n)
   - Make content scannable yet comprehensive

EXAMPLE EBOOK-STYLE FORMAT:
"The circular economy represents a fundamental shift in resource management. Unlike the traditional linear 'take-make-dispose' model, it focuses on keeping materials in use and designing out waste.

**Core Principles:**
• Design products for longevity and reusability
• Maintain materials at highest value through repair
• Regenerate natural systems with sustainable practices

Companies implementing these principles see significant benefits. Patagonia's repair program reduced waste by 73% while maintaining profitability. The Ellen MacArthur Foundation estimates circular approaches could generate $4.5 trillion in economic benefits by 2030.

**Implementation Steps:**
1. Conduct materials audit to identify waste streams
2. Redesign products for disassembly and recycling
3. Establish take-back programs for end-of-life products
4. Partner with recycling and material recovery organizations

This transformation requires commitment across the value chain, but the environmental and economic rewards make it compelling for sustainable business growth."

IMPORTANT - CONTENT QUALITY:
- DO NOT create brief one-liner content
- Balance paragraphs with bullet points/numbered lists
- Include specific data and examples from source material
- Make content educational, practical, and well-structured
- Use professional but accessible language

Return ONLY valid JSON in this exact format (no markdown, no code blocks):
{{
  "categoryName": "{category_name}",
  "courseId": "{course_id}",
  "language": "{language}",
  "chapters": [
    {{
      "chapter": "Chapter Title Here (in {language})",
      "microContents": [
        {{
          "microContentId": "MC-001",
          "microContent": "A detailed 150-300 word explanation with examples, facts, and practical insights (in {language}). This should be comprehensive and educational, covering the topic thoroughly with specific information from the source material..."
        }},
        {{
          "microContentId": "MC-002",
          "microContent": "Another detailed explanation (in {language})..."
        }}
      ]
    }}
  ]
}}

Remember: 
- Generate ALL text in {language}
- Each microContent must be substantial, informative, and valuable for learning
- Avoid superficial or brief explanations"""

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
    
    def transform_to_quickbase_format(
        self, 
        microlearning_data: Dict, 
        table_id: str = "bvxji8seh"
    ) -> Dict:
        """
        Transform microlearning JSON to Quickbase payload format.
        
        Flattens chapters and microContents into individual records with Quickbase field IDs.
        
        Args:
            microlearning_data: Generated microlearning modules dictionary
            table_id: Quickbase table ID (default: "bvxji8seh")
            
        Returns:
            Quickbase-formatted payload with structure:
            {
              "to": "table_id",
              "data": [
                {
                  "12": {"value": "course_id"},
                  "20": {"value": "microContentId"},
                  "8": {"value": "language"},
                  "6": {"value": "chapter"},
                  "7": {"value": "content"}
                }
              ]
            }
        
        Field Mapping:
            - Field 6: Chapter (Text)
            - Field 7: Content (Rich Text)
            - Field 8: Language (Text - Multiple Choice)
            - Field 12: Course ID (Text)
            - Field 20: Micro Content ID (Text)
        """
        logger.info("Transforming microlearning data to Quickbase format")
        
        records = []
        
        # Extract top-level metadata
        course_id = microlearning_data.get('courseId', '001')
        language = microlearning_data.get('language', 'English')
        
        # Flatten chapters and microContents into individual records
        for chapter in microlearning_data.get('chapters', []):
            chapter_title = chapter.get('chapter', '')
            
            for micro_content in chapter.get('microContents', []):
                # Convert markdown to HTML for Quickbase rich text field
                content_html = self._markdown_to_html(micro_content.get('microContent', ''))
                
                record = {
                    "12": {"value": course_id},                                    # Course ID
                    "20": {"value": micro_content.get('microContentId', '')},      # MicroContent_id
                    "8": {"value": language},                                       # Language
                    "6": {"value": chapter_title},                                  # Chapter
                    "7": {"value": content_html}                                   # Content (HTML)
                }
                records.append(record)
        
        payload = {
            "to": table_id,
            "data": records
        }
        
        logger.info(f"Transformed to {len(records)} Quickbase records for table {table_id}")
        
        return payload


def markdown_to_html(text: str) -> str:
    """
    Convert markdown formatting to HTML for Quickbase rich text fields.
    Standalone function version.
    
    Args:
        text: Text with markdown formatting
        
    Returns:
        HTML formatted text
    """
    if not text:
        return text
    
    # Convert **bold** to <strong>
    html = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', text)
    
    # Split into lines for list processing
    lines = html.split('\n')
    in_list = False
    list_type = None
    result_lines = []
    
    for i, line in enumerate(lines):
        stripped = line.strip()
        
        # Check if line is a bullet point
        if re.match(r'^[•\-]\s+', stripped):
            item = re.sub(r'^[•\-]\s+', '', stripped)
            if not in_list:
                result_lines.append('<ul>')
                in_list = True
                list_type = 'ul'
            result_lines.append(f'<li>{item}</li>')
        # Check if line is a numbered list item
        elif re.match(r'^\d+\.\s+', stripped):
            item = re.sub(r'^\d+\.\s+', '', stripped)
            if not in_list:
                result_lines.append('<ol>')
                in_list = True
                list_type = 'ol'
            result_lines.append(f'<li>{item}</li>')
        else:
            # Close list if we were in one
            if in_list:
                result_lines.append(f'</{list_type}>')
                in_list = False
                list_type = None
            
            # Handle regular lines
            if stripped:  # Non-empty line
                result_lines.append(stripped)
                # Add <br> after each line (except the last one)
                if i < len(lines) - 1:
                    result_lines.append('<br>')
            else:  # Empty line
                # Add paragraph break for empty lines
                result_lines.append('<br><br>')
    
    # Close any open list
    if in_list:
        result_lines.append(f'</{list_type}>')
    
    # Join without adding extra separators
    html = ''.join(result_lines)
    
    # Clean up excessive <br> tags
    html = re.sub(r'(<br>){3,}', '<br><br>', html)  # Max 2 consecutive breaks
    
    return html


def transform_to_quickbase_format(
    microlearning_data: Dict, 
    table_id: str = "bvxji8seh"
) -> Dict:
    """
    Standalone function to transform microlearning JSON to Quickbase payload format.
    
    This is a convenience function that can be used without instantiating MicrolearningGenerator.
    
    Args:
        microlearning_data: Generated microlearning modules dictionary
        table_id: Quickbase table ID (default: "bvxji8seh")
        
    Returns:
        Quickbase-formatted payload
        
    Example:
        >>> modules = {...generated microlearning modules...}
        >>> payload = transform_to_quickbase_format(modules)
        >>> # Ready to POST to Quickbase API
    """
    records = []
    
    course_id = microlearning_data.get('courseId', '001')
    language = microlearning_data.get('language', 'English')
    
    for chapter in microlearning_data.get('chapters', []):
        chapter_title = chapter.get('chapter', '')
        
        for micro_content in chapter.get('microContents', []):
            # Convert markdown to HTML for Quickbase rich text field
            content_html = markdown_to_html(micro_content.get('microContent', ''))
            
            record = {
                "12": {"value": course_id},
                "20": {"value": micro_content.get('microContentId', '')},
                "8": {"value": language},
                "6": {"value": chapter_title},
                "7": {"value": content_html}
            }
            records.append(record)
    
    return {
        "to": table_id,
        "data": records
    }


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
    
    openai_api_key = os.getenv("OPENAI_API_KEY")
    if not openai_api_key:
        raise ValueError("OPENAI_API_KEY not found in environment variables")
    
    # Determine vector store path
    # This can be overridden with an environment variable
    vector_store_path = os.getenv(
        "VECTOR_STORE_PATH",
        str(Path(__file__).parent.parent.parent / "vector_store")
    )
    
    return MicrolearningGenerator(
        vector_store_path=vector_store_path,
        groq_api_key=groq_api_key,
        openai_api_key=openai_api_key
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
