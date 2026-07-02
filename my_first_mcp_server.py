from mcp.server.fastmcp import FastMCP
from mcp.server.fastmcp.prompts import base
from pydantic import Field

mcp = FastMCP("MyFirstMCPServer", log_level="ERROR")


@mcp.tool(
    name="say_hello",
    description="Say hello to someone by name.",
)
def say_hello(
    name: str = Field(description="Name of the person to greet"),
) -> str:
    return f"Hello, {name}!"


@mcp.resource("greeting://{name}", mime_type="text/plain")
def greeting_resource(name: str) -> str:
    return f"Hello, {name}! This is a resource, not a tool response."


@mcp.prompt(
    name="introduce",
    description="Generate a prompt asking the assistant to introduce someone by name.",
)
def introduce(
    name: str = Field(description="Name of the person to introduce"),
) -> list[base.Message]:
    prompt = f"Write a short, friendly introduction for a person named {name}."
    return [base.UserMessage(prompt)]


if __name__ == "__main__":
    mcp.run(transport="stdio")
