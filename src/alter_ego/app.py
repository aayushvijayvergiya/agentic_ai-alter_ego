"""Main application module for the Alter Ego chatbot."""

import gradio as gr

from .config import config
from .services import ChatService


class AlterEgoApp:
    """Main application class for the Alter Ego chatbot."""
    
    def __init__(self):
        # Validate configuration
        if not config.validate_config():
            raise ValueError("Invalid configuration. Please check your environment variables.")
        
        self.chat_service = ChatService()
        print(f"Alter Ego application initialized for {config.name}")
    
    def chat_handler(self, message: str, history) -> str:
        """Handle chat messages from Gradio interface."""
        try:
            return self.chat_service.chat(message, history)
        except Exception as e:
            print(f"Error in chat handler: {e}")
            return "I'm sorry, I encountered an error. Please try again."
    
    def launch(self, **kwargs):
        """Launch the Gradio interface."""
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
