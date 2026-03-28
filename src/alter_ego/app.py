"""Main application module for the Alter Ego chatbot."""

import gradio as gr

from .config import config
from .services import ChatService
from .utils.logger import logger


class AlterEgoApp:
    """Main application class for the Alter Ego chatbot."""
    
    def __init__(self):
        # Validate configuration
        if not config.validate_config():
            raise ValueError("Invalid configuration. Please check your environment variables.")
        
        self.chat_service = ChatService()
        logger.info(f"Alter Ego application initialized for {config.name}")
    
    async def chat_handler(self, message: str, history):
        """Handle chat messages from Gradio interface asynchronously."""
        # Basic Rate Limiting
        user_message_count = sum(1 for m in history if m.get("role") == "user")
        if user_message_count >= config.max_messages_per_session:
            yield f"Thank you for chatting! We've reached the limit of {config.max_messages_per_session} messages for this session. Please feel free to reach out to me directly via email!"
            return

        try:
            # Check if chat returns an async generator (streaming)
            response = self.chat_service.chat(message, history)
            if hasattr(response, '__aiter__'):
                async for chunk in response:
                    yield chunk
            else:
                # Fallback for non-streaming
                yield await response
        except Exception as e:
            logger.error(f"Error in chat handler: {e}")
            yield "I'm sorry, I encountered an error. Please try again."
    
    def launch(self, **kwargs):
        """Launch the Gradio interface."""
        if config.portfolio_domain:
            # Allow embedding from the specified portfolio domain
            kwargs.setdefault("allowed_iframe_origins", [config.portfolio_domain])
            
        interface = gr.ChatInterface(
            self.chat_handler,
            type="messages",
            title="Aayush's Digital Twin 🤖",
            description="Powered by open-source models, so responses might take a sec — appreciate your patience! Ask me anything about Aayush's background, skills, and experience."
        )
        
        return interface.launch(**kwargs)


def create_app() -> AlterEgoApp:
    """Factory function to create the application."""
    return AlterEgoApp()
