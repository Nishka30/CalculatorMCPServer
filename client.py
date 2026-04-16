import httpx
import json
import uuid

URL = "http://127.0.0.1:8000/mcp"


#starts communication with server 
def create_session(client):
    payload = {
        "jsonrpc": "2.0",  #MCP uses JSON-RPC 2.0 protocol for communication
        "id": str(uuid.uuid4()), 
        "method": "initialize", #starting a session with the server by calling initialize method
        "params": {
            "protocolVersion": "2024-11-05", 
            "capabilities": {}, 
            "clientInfo": {
                "name": "my-client", 
                "version": "1.0.0"
            }
        }
    }
    #sending post request to the server with the payload to initialize a session. 
    #The server should respond with a session ID that we will use for subsequent tool calls.
    #I can accept normal JSON OR streaming (SSE)

    response = client.post(
        URL,
        json=payload,
        headers={
            "Accept": "application/json, text/event-stream", #client can handle both normal JSON response and streaming SSE response
            "Content-Type": "application/json" #telling server that we are sending JSON data in the request body
        }
    )
    #Server sends session ID in headers, we need to extract it for future calls.
    session_id = response.headers.get("Mcp-Session-Id")
    if not session_id:
        raise Exception(f"Failed to get session ID. Status: {response.status_code}, Body: {response.text}")

    print("Session ID:", session_id)
    return session_id


# CALL TOOL (STREAMED SSE)
#calling a tool on the server by sending a JSON-RPC request to the /mcp endpoint.
def call_tool(client, session_id, tool, a, b):
    payload = { 
        "jsonrpc": "2.0",
        "id": str(uuid.uuid4()),
        "method": "tools/call",  #this is the method defined by MCP spec for calling tools
        "params": {
            "name": tool, 
            "arguments": {
                "a": float(a),
                "b": float(b)
            }
        }
    }
    #We use client.stream to handle both normal JSON response and streaming SSE response from the server.
    with client.stream(  
        "POST", #HTTP POST request to the /mcp endpoint with the tool call payload and session ID in headers for authentication.
        URL,
        json=payload, 
        headers={
            "Accept": "application/json, text/event-stream",
            "Content-Type": "application/json",
            "Mcp-Session-Id": session_id
        }
    ) as response: #checking the content type of the response to determine if it's a normal JSON response or a streaming SSE response.

        content_type = response.headers.get("content-type", "") 

        # SSE stream
        if "text/event-stream" in content_type: 
            for line in response.iter_lines(): 
                if line.startswith("data:"):
                    raw = line[len("data:"):].strip() 
                    try:
                        data = json.loads(raw) 
                        if "result" in data: 
                            content = data["result"].get("content", [])  
                            for item in content: 
                                if item.get("type") == "text":
                                    text = item["text"]
                                    try:
                                        parsed = json.loads(text)

                                        # If it's structured output
                                        if isinstance(parsed, dict) and "result" in parsed:
                                            print("Result:", parsed["result"])
                                        else:
                                            print("Result:", parsed)

                                    except json.JSONDecodeError:
                                        # If it's plain text
                                        print("Result:", text)
                        elif "error" in data:
                            print("Error:", data["error"]["message"])
                    except json.JSONDecodeError: #
                        print("Raw SSE data:", raw)

        # Plain JSON response
        elif "application/json" in content_type: 
            data = json.loads(response.read()) #
            if "result" in data:
                content = data["result"].get("content", [])
                for item in content:
                    if item.get("type") == "text":
                        text = item["text"]

                        try:
                            parsed = json.loads(text)

                            # If it's structured output
                            if isinstance(parsed, dict) and "result" in parsed:
                                print("Result:", parsed["result"])
                            else:
                                print("Result:", parsed)

                        except json.JSONDecodeError:
                            # If it's plain text
                            print("Result:", text)
            elif "error" in data:
                print("Error:", data["error"]["message"])
            else:
                print("Response:", data)

        else:
            print("Unexpected content type:", content_type)
            print(response.read())

##creating an HTTP client using httpx library to communicate with the MCP server. 
# We first create a session with the server to get a session ID, and then we enter a loop where we prompt the user 
# to enter a tool (operation) and its arguments. 
# We call the specified tool on the server and print the result or any errors that occur.

if __name__ == "__main__": 
    with httpx.Client(timeout=None) as client:
        session_id = create_session(client)

        while True:
            tool = input("\nEnter operation (add/subtract/multiply/divide or exit): ")

            if tool == "exit":
                break

            if tool not in ["add", "subtract", "multiply", "divide"]:
                print("Invalid operation")
                continue

            try:
                a = float(input("Enter first number: "))
                b = float(input("Enter second number: "))
                call_tool(client, session_id, tool, a, b)

            except ValueError:
                print("Invalid input")