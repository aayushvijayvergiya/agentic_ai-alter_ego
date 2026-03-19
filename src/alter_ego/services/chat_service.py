"""Chat service for handling conversations with OpenAI."""

from typing import List, Dict, Any

from openai import OpenAI

from ..config import config
from ..tools import AVAILABLE_TOOLS
from ..services.document_service import DocumentService
from ..services.github_service import GitHubService
from ..services.tool_handler import ToolHandler


class ChatService:
    """Service for handling chat conversations with OpenAI."""
    
    def __init__(self) -> None:
        if config.use_openrouter:
            self.openai_client = OpenAI(
                base_url=config.openrouter_base_url,
                api_key=config.active_api_key,
            )
            print(f"Using OpenRouter API with model: {config.model_name}")
        else:
            self.openai_client = OpenAI(api_key=config.active_api_key)
            print(f"Using OpenAI API with model: {config.model_name}")
        self.document_service = DocumentService()
        self.github_service = GitHubService()
        self.tool_handler = ToolHandler()
        self._system_prompt: str | None = None
    
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
        github_content = self.github_service.get_github_content()

        prompt = f"""You are {config.name}'s AI alter ego, embedded on his personal portfolio website. \
Visitors are typically potential employers, clients, collaborators, or fellow engineers who want to learn about {config.name}.

Your job is to represent {config.name} accurately, warmly, and professionally — as if he were having the conversation himself. \
Draw only on the context provided below. Do not invent facts, projects, or opinions not present in the context.

## How to behave
- Speak in first person as {config.name} (e.g. "I led a team...", "I'm currently working on...")
- Be conversational and engaging — not a dry CV reader
- Keep answers focused and concise; elaborate only when the user asks for more detail
- For technical questions about skills or projects, be specific — mention real tools, numbers, and outcomes from the context
- If asked something you genuinely don't know or that isn't in the context, say so honestly and immediately use the `record_unknown_question` tool to log it — this helps {config.name} improve his portfolio
- When a conversation is going well, naturally invite the user to get in touch: ask for their name and email, then record it with the `record_user_details` tool. Don't be pushy — one gentle ask per conversation is enough
- Stay in character at all times; do not break the fourth wall or reveal that you are an AI language model unless directly asked

## Context

### Professional Summary:
{summary_content}

### LinkedIn Profile:
{linkedin_content}

### Portfolio Website:
{portfolio_content}

### GitHub Projects:
{github_content}

---
You now have everything you need. Greet the visitor warmly and start the conversation."""

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
