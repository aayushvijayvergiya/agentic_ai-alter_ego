"""Chat service for handling conversations with OpenAI asynchronously."""

from typing import List, Dict, Any

from openai import AsyncOpenAI
from openai.types.chat import ChatCompletionMessageParam

from ..config import config
from ..tools import AVAILABLE_TOOLS
from ..services.document_service import DocumentService
from ..services.github_service import GitHubService
from ..services.tool_handler import ToolHandler
from ..utils.logger import logger


class ChatService:
    """Service for handling chat conversations with OpenAI asynchronously."""
    
    MAX_TOOL_CALLS = 5
    
    def __init__(self) -> None:
        if config.use_openrouter:
            self.openai_client = AsyncOpenAI(
                base_url=config.openrouter_base_url,
                api_key=config.active_api_key,
            )
            logger.info(f"Using OpenRouter API with model: {config.model_name}")
        else:
            self.openai_client = AsyncOpenAI(api_key=config.active_api_key)
            logger.info(f"Using OpenAI API with model: {config.model_name}")
            
        self.document_service = DocumentService()
        self.github_service = GitHubService()
        self.tool_handler = ToolHandler()
        self._system_prompt: str | None = None
    
    async def get_system_prompt(self) -> str:
        """Generate and cache the system prompt asynchronously."""
        if self._system_prompt is None:
            self._system_prompt = await self._build_system_prompt()
        return self._system_prompt
    
    async def _build_system_prompt(self) -> str:
        """Build the system prompt with context information asynchronously."""
        linkedin_content = await self.document_service.get_linkedin_content()
        summary_content = await self.document_service.get_summary_content()
        portfolio_content = await self.document_service.get_portfolio_content()
        github_content = await self.github_service.get_github_content()

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
    
    async def chat(self, message: str, history: List[Dict[str, str]]) -> Any:
        """Process a chat message and return the response asynchronously as a generator."""
        # Prepare messages for OpenAI
        system_prompt = await self.get_system_prompt()
        messages: List[ChatCompletionMessageParam] = (
            [{"role": "system", "content": system_prompt}]
            + [{"role": m["role"], "content": m["content"]} for m in history]  # type: ignore[misc]
            + [{"role": "user", "content": message}]
        )
        
        tool_call_count = 0

        # Pass 1 & Tool Loop: Non-streaming to handle tools
        while True:
            try:
                # Call OpenAI API with tools (non-streaming)
                response = await self.openai_client.chat.completions.create(
                    model=config.model_name,
                    messages=messages,
                    tools=AVAILABLE_TOOLS,  # type: ignore[arg-type]
                )

                message_obj = response.choices[0].message
                finish_reason = response.choices[0].finish_reason

                # Handle tool calls if present
                if finish_reason == "tool_calls" or (hasattr(message_obj, 'tool_calls') and message_obj.tool_calls):
                    tool_call_count += 1
                    if tool_call_count > self.MAX_TOOL_CALLS:
                        logger.warning(f"Exceeded maximum tool calls ({self.MAX_TOOL_CALLS})")
                        yield "I'm sorry, I encountered an error while processing your message. Please try again."
                        return
                        
                    tool_calls = message_obj.tool_calls

                    # Process tool calls
                    tool_results = await self.tool_handler.handle_tool_calls(tool_calls)

                    # Add assistant message and tool results to conversation
                    messages.append(message_obj.model_dump())  # type: ignore[arg-type]
                    messages.extend(tool_results)  # type: ignore[arg-type]
                else:
                    # No more tool calls needed. Break to start the streaming pass.
                    # Note: We intentionally discard the text generated in this non-streaming pass
                    # to fulfill the streaming requirement for the final response.
                    break

            except Exception as e:
                logger.error(f"Error in chat processing (tool pass): {e}")
                yield "I'm sorry, I encountered an error while processing your message. Please try again."
                return

        # Pass 2: Stream the final response
        try:
            stream = await self.openai_client.chat.completions.create(
                model=config.model_name,
                messages=messages,
                stream=True
            )
            
            full_response = ""
            async for chunk in stream:
                if chunk.choices and chunk.choices[0].delta.content:
                    full_response += chunk.choices[0].delta.content
                    yield full_response
                    
        except Exception as e:
            logger.error(f"Error in chat streaming: {e}")
            if not full_response:
                yield "I'm sorry, I encountered an error while generating the response."
