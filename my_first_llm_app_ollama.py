import asyncio
import re
import sys

import ollama

from mcp_client import MCPClient

OLLAMA_MODEL = "qwen2.5:1.5b"

RESOURCE_REFERENCE_PATTERN = re.compile(r"@(\w+)")


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


async def resolve_resource_references(client: MCPClient, user_input: str) -> str:
    """Expands @name references into MCP resource content, appended as context."""
    names = RESOURCE_REFERENCE_PATTERN.findall(user_input)
    if not names:
        return user_input

    context_blocks = []
    for name in names:
        try:
            content = await client.read_resource(f"greeting://{name}")
            context_blocks.append(f"[Resource greeting://{name}]\n{content}")
        except Exception as e:
            context_blocks.append(f"[Resource greeting://{name}] Error: {e}")

    context = "\n\n".join(context_blocks)
    return f"{user_input}\n\nContext from MCP resources:\n{context}"


async def main():
    async with MCPClient(
        command=sys.executable,
        args=["my_first_mcp_server.py"],
    ) as client:
        mcp_tools = await client.list_tools()
        tools = mcp_tools_to_ollama_tools(mcp_tools)

        messages = []

        print("Chat with the local Ollama model (Ctrl+C or 'exit' to quit).")
        print("Reference a resource with @name, e.g. 'Summarize @Alice'.")
        while True:
            try:
                user_input = input("You: ").strip()
            except EOFError:
                break

            if not user_input:
                continue
            if user_input.lower() in ("exit", "quit"):
                break

            enriched_input = await resolve_resource_references(client, user_input)
            messages.append({"role": "user", "content": enriched_input})

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
