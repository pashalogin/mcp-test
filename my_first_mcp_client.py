import sys
import asyncio
from contextlib import AsyncExitStack
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


async def main():
    server_params = StdioServerParameters(
        command=sys.executable,
        args=["my_first_mcp_server.py"],
    )

    async with AsyncExitStack() as exit_stack:
        stdio, write = await exit_stack.enter_async_context(stdio_client(server_params))
        session = await exit_stack.enter_async_context(ClientSession(stdio, write))
        await session.initialize()

        tools = await session.list_tools()
        print("Available tools:", [tool.name for tool in tools.tools])

        result = await session.call_tool("say_hello", {"name": "World"})
        print("Tool result:", result.content[0].text)

        resource = await session.read_resource("greeting://World")
        print("Resource result:", resource.contents[0].text)

        prompts = await session.list_prompts()
        print("Available prompts:", [prompt.name for prompt in prompts.prompts])

        prompt = await session.get_prompt("introduce", {"name": "World"})
        print("Prompt result:", prompt.messages[0].content.text)


if __name__ == "__main__":
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    asyncio.run(main())
