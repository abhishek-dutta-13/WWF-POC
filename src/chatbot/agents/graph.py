"""
Chatbot Workflow Orchestration - Coordinates all agents
"""
import logging
from pathlib import Path
from typing import Dict, List
from chatbot.models import UserContext, Source
from chatbot.agents.supervisor import SupervisorAgent
from chatbot.agents.rag_agent import RAGAgent
from chatbot.agents.web_search_agent import WebSearchAgent
from chatbot.agents.response_agent import ResponseAgent

logger = logging.getLogger(__name__)


class ChatbotWorkflow:
    """
    Orchestrates the chatbot workflow:
    Query → Supervisor → RAG/Web/Hybrid → Response Generation
    """
    
    def __init__(
        self,
        vector_store_path: str = None,
        collection_name: str = "wwf_knowledge_base"
    ):
        """
        Initialize chatbot workflow with all agents
        
        Args:
            vector_store_path: Path to ChromaDB vector store (defaults to project root/vector_store)
            collection_name: ChromaDB collection name
        """
        logger.info("[Chatbot Workflow] Initializing agents...")
        
        # Calculate absolute path to vector_store if not provided
        if vector_store_path is None:
            # Get path relative to this file: graph.py is in src/chatbot/agents/
            # Go up 3 levels to project root, then into vector_store
            vector_store_path = str(Path(__file__).parent.parent.parent.parent / "vector_store")
        
        logger.info(f"[Chatbot Workflow] Using vector store path: {vector_store_path}")
        
        # Initialize all agents
        self.supervisor = SupervisorAgent()
        self.rag_agent = RAGAgent(
            vector_store_path=vector_store_path,
            collection_name=collection_name
        )
        self.web_search_agent = WebSearchAgent()
        self.response_agent = ResponseAgent()
        
        logger.info("[Chatbot Workflow] All agents initialized successfully")
    
    def process_message(
        self,
        query: str,
        user_context: UserContext,
        language: str = "English"
    ) -> Dict:
        """
        Process user message through the agent workflow
        
        Args:
            query: User's query
            user_context: User information
            language: Response language (English, French, German)
        
        Returns:
            Dictionary with:
                - response: Generated response text
                - sources: List of Source objects
                - agent_used: Which agent(s) were used
                - pdf_requested: Whether PDF export was requested
        """
        logger.info(f"[Workflow] Processing query in {language}: {query[:50]}...")
        
        # Step 1: Route the query
        route = self.supervisor.route_query(query, user_context.location)
        logger.info(f"[Workflow] Supervisor routed to: {route.upper()}")
        
        # Step 2: Handle simple greetings without RAG/web search
        if route == 'greeting':
            # Generate a simple, friendly greeting response
            greeting_responses = {
                'English': f"Hello {user_context.name}! 👋 How can I help you today? Feel free to ask me about sustainability, conservation, circular economy, or any WWF-related topics.",
                'French': f"Bonjour {user_context.name}! 👋 Comment puis-je vous aider aujourd'hui? N'hésitez pas à me poser des questions sur la durabilité, la conservation, l'économie circulaire ou tout sujet lié au WWF.",
                'German': f"Hallo {user_context.name}! 👋 Wie kann ich Ihnen heute helfen? Fragen Sie mich gerne zu Nachhaltigkeit, Naturschutz, Kreislaufwirtschaft oder WWF-Themen."
            }
            
            response = greeting_responses.get(language, greeting_responses['English'])
            
            return {
                'response': response,
                'sources': [],
                'agent_used': 'greeting',
                'pdf_requested': False
            }
        
        # Step 2b: Handle off-topic queries (not sustainability/environment related)
        if route == 'off_topic':
            off_topic_responses = {
                'English': (
                    f"I'm sorry {user_context.name}, but I'm a specialist assistant focused exclusively on "
                    f"sustainability, environmental conservation, and WWF-related topics. "
                    f"I'm unable to help with this particular question.\n\n"
                    f"I'd be happy to assist you with questions about:\n"
                    f"• Climate change and global warming\n"
                    f"• Biodiversity and wildlife conservation\n"
                    f"• Circular economy and waste reduction\n"
                    f"• Sustainable agriculture and natural resources\n"
                    f"• WWF initiatives and reports\n\n"
                    f"Please feel free to ask a question in any of these areas!"
                ),
                'French': (
                    f"Je suis désolé {user_context.name}, mais je suis un assistant spécialisé dans la "
                    f"durabilité, la conservation de l'environnement et les sujets liés au WWF. "
                    f"Je ne peux pas aider avec cette question."
                ),
                'German': (
                    f"Es tut mir leid {user_context.name}, aber ich bin ein Spezialist für Nachhaltigkeit, "
                    f"Umweltschutz und WWF-Themen. Ich kann bei dieser Frage leider nicht helfen."
                ),
            }
            response = off_topic_responses.get(language, off_topic_responses['English'])
            return {
                'response': response,
                'sources': [],
                'agent_used': 'off_topic',
                'pdf_requested': False
            }

        # Step 2b: Handle invalid/nonsensical queries
        if route == 'invalid_query':
            invalid_responses = {
                'English': f"I'm sorry, but I need a bit more information to help you properly. Could you please ask a complete question about sustainability, conservation, or WWF topics?\n\nFor example:\n• What is circular economy?\n• How can I reduce waste?\n• Tell me about WWF's conservation efforts",
                'French': f"Désolé, mais j'ai besoin d'un peu plus d'informations pour vous aider correctement. Pourriez-vous poser une question complète sur la durabilité, la conservation ou les sujets liés au WWF?",
                'German': f"Entschuldigung, aber ich benötige etwas mehr Informationen, um Ihnen richtig helfen zu können. Könnten Sie bitte eine vollständige Frage zu Nachhaltigkeit, Naturschutz oder WWF-Themen stellen?"
            }
            
            response = invalid_responses.get(language, invalid_responses['English'])
            
            return {
                'response': response,
                'sources': [],
                'agent_used': 'invalid_query',
                'pdf_requested': False
            }
        
        # Step 3: Check for PDF export request
        if route == 'pdf_export':
            return {
                'response': "I'll prepare a PDF export of our conversation for you.",
                'sources': [],
                'agent_used': 'pdf_export',
                'pdf_requested': True
            }
        
        # Step 4: Gather context based on routing
        rag_context = ""
        web_context = ""
        sources = []
        actual_agent_used = route
        
        if route in ['rag', 'hybrid']:
            logger.info("[Workflow] Calling RAG Agent...")
            rag_context, rag_sources = self.rag_agent.retrieve(
                query=query,
                user_location=user_context.location
            )
            sources.extend(rag_sources)
            logger.info(f"[Workflow] RAG Agent returned {len(rag_sources)} sources")
            
            # Smart fallback: If RAG route but no good results, try web search instead
            if route == 'rag' and len(rag_sources) < 2:
                logger.warning(f"[Workflow] RAG returned insufficient results ({len(rag_sources)} sources). Falling back to web search for better coverage.")
                logger.info("[Workflow] Calling Web Search Agent (fallback)...")
                web_context, web_sources = self.web_search_agent.search(
                    query=query,
                    user_location=user_context.location
                )
                sources.extend(web_sources)
                logger.info(f"[Workflow] Web Search Agent returned {len(web_sources)} sources")
                actual_agent_used = 'web_search'  # Update to reflect actual agent used
        
        if route in ['web_search', 'hybrid']:
            logger.info("[Workflow] Calling Web Search Agent...")
            web_context, web_sources = self.web_search_agent.search(
                query=query,
                user_location=user_context.location
            )
            sources.extend(web_sources)
            logger.info(f"[Workflow] Web Search Agent returned {len(web_sources)} sources")
        
        # Step 5: Generate response
        logger.info(f"[Workflow] Generating response in {language} with Response Agent...")
        response = self.response_agent.generate_response(
            query=query,
            user_context=user_context,
            rag_context=rag_context,
            web_context=web_context,
            language=language
        )
        
        # Step 6: Return result
        result = {
            'response': response,
            'sources': sources,
            'agent_used': actual_agent_used,  # Use actual agent (may differ from route due to fallback)
            'pdf_requested': False
        }
        
        logger.info(f"[Workflow] Completed with {len(sources)} total sources using {actual_agent_used} agent")
        
        return result
    
    def generate_welcome_message(self, user_context: UserContext) -> str:
        """
        Generate welcome message for new session
        
        Args:
            user_context: User information
        
        Returns:
            Welcome message
        """
        return self.response_agent.generate_welcome_message(user_context)
