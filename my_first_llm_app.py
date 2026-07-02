import asyncio
import os
import sys

from dotenv import load_dotenv

from mcp_client import MCPClient
from core.claude import Claude
from core.tools import ToolManager

load_dotenv()

claude_model = os.getenv("CLAUDE_MODEL", "")
anthropic_api_key = os.getenv("ANTHROPIC_API_KEY", "")

assert claude_model, "Error: CLAUDE_MODEL cannot be empty. Update .env"
assert anthropic_api_key, "Error: ANTHROPIC_API_KEY cannot be empty. Update .env"


async def main():
    claude_service = Claude(model=claude_model)

    async with MCPClient(
        command=sys.executable,
        args=["my_first_mcp_server.py"],
    ) as client:
        clients = {"my_first_client": client}
        tools = await ToolManager.get_all_tools(clients)

        messages = []
        claude_service.add_user_message(messages, "Say hello to Alice")

        response = claude_service.chat(messages, tools=tools)
        claude_service.add_assistant_message(messages, response)

        if response.stop_reason == "tool_use":
            tool_results = await ToolManager.execute_tool_requests(clients, response)
            claude_service.add_user_message(messages, tool_results)
            response = claude_service.chat(messages, tools=tools)

        print(claude_service.text_from_message(response))


if __name__ == "__main__":
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    asyncio.run(main())
