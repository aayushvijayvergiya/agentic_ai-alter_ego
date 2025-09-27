"""Chat service for handling conversations with OpenAI."""

from typing import List, Dict, Any

from openai import OpenAI

from ..config import config
from ..tools import AVAILABLE_TOOLS
from ..services.document_service import DocumentService
from ..services.tool_handler import ToolHandler


class ChatService:
    """Service for handling chat conversations with OpenAI."""
    
    def __init__(self):
        self.openai_client = OpenAI()
        self.document_service = DocumentService()
        self.tool_handler = ToolHandler()
        self._system_prompt = None
    
    @property
    def system_prompt(self) -> str:
        """Generate and cache the system prompt."""
        if self._system_prompt is None:
            self._system_prompt = self._build_system_prompt()
        return self._system_prompt
    
    def _build_system_prompt(self) -> str:
        """Build the system prompt with context information."""
        linkedin_content = self.document_service.get_linkedin_content()
        summary_content = self.document_service.get_summary_content()
        portfolio_content = self.document_service.get_portfolio_content()

        prompt = f"""You are acting as {config.name}. You are answering questions on {config.name}'s website, \
particularly questions related to {config.name}'s career, background, skills and experience. \
Your responsibility is to represent {config.name} for interactions on the website as faithfully as possible. \
You are given a summary of {config.name}'s background and LinkedIn profile which you can use to answer questions. \
Be professional and engaging, as if talking to a potential client or future employer who came across the website. \
If you don't know the answer to any question, use your record_unknown_question tool to record the question that you couldn't answer, even if it's about something trivial or unrelated to career. \
If the user is engaging in discussion, try to steer them towards getting in touch via email; ask for their email and record it using your record_user_details tool.

## Summary:
{summary_content}

## LinkedIn Profile:
{linkedin_content}

## Portfolio:
{portfolio_content}

With this context, please chat with the user, always staying in character as {config.name}."""
        
        return prompt
    
    def chat(self, message: str, history: List[Dict[str, str]]) -> str:
        """Process a chat message and return the response."""
        # Prepare messages for OpenAI
        messages = [{"role": "system", "content": self.system_prompt}] + history + [{"role": "user", "content": message}]
        
        done = False
        
        while not done:
            try:
                # Call OpenAI API with tools
                response = self.openai_client.chat.completions.create(
                    model=config.model_name,
                    messages=messages,
                    tools=AVAILABLE_TOOLS
                )
                
                finish_reason = response.choices[0].finish_reason
                
                # Handle tool calls if present
                if finish_reason == "tool_calls":
                    message_obj = response.choices[0].message
                    tool_calls = message_obj.tool_calls
                    
                    # Process tool calls
                    tool_results = self.tool_handler.handle_tool_calls(tool_calls)
                    
                    # Add assistant message and tool results to conversation
                    messages.append(message_obj)
                    messages.extend(tool_results)
                else:
                    done = True
                    
            except Exception as e:
                print(f"Error in chat processing: {e}")
                return f"I'm sorry, I encountered an error while processing your message. Please try again."
        
        return response.choices[0].message.content
