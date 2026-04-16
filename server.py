from fastmcp import FastMCP
import os

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
        raise ValueError("Cannot divide by zero")
    result = a / b
    return {"result": result}

if __name__ == "__main__":
    mcp.run(
        transport="http",
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 8000)),
        path="/mcp"  # ← add this
    )