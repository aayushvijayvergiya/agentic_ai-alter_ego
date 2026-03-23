"""Tool handlers for processing OpenAI function calls."""

import json
from typing import Dict, Any, List

from ..models import UserDetails, UnknownQuestion, ToolResult
from ..services.notification_service import NotificationService
from ..utils.logger import logger


class ToolHandler:
    """Handler for processing tool calls from OpenAI asynchronously."""
    
    def __init__(self):
        self.notification_service = NotificationService()
    
    async def record_user_details(self, email: str, name: str = "Name not provided", notes: str = "not provided") -> Dict[str, str]:
        """Record user contact details and send notification asynchronously."""
        user_details = UserDetails(email=email, name=name, notes=notes)
        
        # Send notification
        await self.notification_service.notify_user_interest(
            email=user_details.email,
            name=user_details.name,
            notes=user_details.notes
        )
        
        return {"recorded": "ok"}
    
    async def record_unknown_question(self, question: str) -> Dict[str, str]:
        """Record an unknown question and send notification asynchronously."""
        unknown_question = UnknownQuestion(question=question)
        
        # Send notification
        await self.notification_service.notify_unknown_question(unknown_question.question)
        
        return {"recorded": "ok"}
    
    async def handle_tool_calls(self, tool_calls) -> List[Dict[str, Any]]:
        """Process multiple tool calls and return results asynchronously."""
        results = []
        
        for tool_call in tool_calls:
            tool_name = tool_call.function.name
            arguments = json.loads(tool_call.function.arguments)
            
            logger.info(f"Tool called: {tool_name}")
            
            # Get the appropriate handler method
            handler_method = getattr(self, tool_name, None)
            
            if handler_method:
                try:
                    result = await handler_method(**arguments)
                except Exception as e:
                    logger.error(f"Error executing tool {tool_name}: {e}")
                    result = {"error": f"Tool execution failed: {str(e)}"}
            else:
                logger.warning(f"Unknown tool: {tool_name}")
                result = {"error": f"Unknown tool: {tool_name}"}
            
            # Create tool result
            tool_result = ToolResult(
                role="tool",
                content=json.dumps(result),
                tool_call_id=tool_call.id
            )
            
            results.append({
                "role": tool_result.role,
                "content": tool_result.content,
                "tool_call_id": tool_result.tool_call_id
            })
        
        return results
