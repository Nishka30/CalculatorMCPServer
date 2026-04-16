from fastmcp import FastMCP
import os


# Create MCP server instance
mcp = FastMCP(name="Calculator MCP Server")


@mcp.tool() 
def add(a: float, b: float):
    result = a + b
    return {"result": result}


@mcp.tool()
def subtract(a: float, b: float):
    result = a - b
    return {"result": result}


@mcp.tool()
def multiply(a: float, b: float):
    result = a * b
    return {"result": result}


@mcp.tool()
def divide(a: float, b: float):
    if b == 0:
        # MCP-friendly error
        raise ValueError("Cannot divide by zero")

    result = a / b
    return {"result": result}


# Start MCP HTTP server

if __name__ == "__main__":
    mcp.run(
        transport="http",
        host="0.0.0.0",   # 🔥 REQUIRED FOR RENDER
        port=int(os.environ.get("PORT", 8000))  # 🔥 REQUIRED
    )