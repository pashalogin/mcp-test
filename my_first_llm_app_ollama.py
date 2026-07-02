import asyncio
import sys

import ollama

from mcp_client import MCPClient

OLLAMA_MODEL = "qwen2.5:1.5b"


def mcp_tools_to_ollama_tools(mcp_tools):
    return [
        {
            "type": "function",
            "function": {
                "name": tool.name,
                "description": tool.description,
                "parameters": tool.inputSchema,
            },
        }
        for tool in mcp_tools
    ]


async def main():
    async with MCPClient(
        command=sys.executable,
        args=["my_first_mcp_server.py"],
    ) as client:
        mcp_tools = await client.list_tools()
        tools = mcp_tools_to_ollama_tools(mcp_tools)

        messages = []

        print("Chat with the local Ollama model (Ctrl+C or 'exit' to quit).")
        while True:
            try:
                user_input = input("You: ").strip()
            except EOFError:
                break

            if not user_input:
                continue
            if user_input.lower() in ("exit", "quit"):
                break

            messages.append({"role": "user", "content": user_input})

            response = ollama.chat(model=OLLAMA_MODEL, messages=messages, tools=tools)
            messages.append(response.message)

            if response.message.tool_calls:
                for tool_call in response.message.tool_calls:
                    result = await client.call_tool(
                        tool_call.function.name, tool_call.function.arguments
                    )
                    result_text = "\n".join(
                        part.text for part in result.content if part.type == "text"
                    )
                    messages.append({"role": "tool", "content": result_text})

                response = ollama.chat(model=OLLAMA_MODEL, messages=messages, tools=tools)
                messages.append(response.message)

            print(f"Assistant: {response.message.content}")


if __name__ == "__main__":
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    asyncio.run(main())
