import os
import asyncio
import uvicorn
import importlib
from typing import List, Dict

from dotenv import load_dotenv

load_dotenv()

server_url = os.environ["SERVER_URL"]

# Server configurations with environment variable-based ports
servers: List[Dict[str, str]] = [
    {
        "name": "title_agent_server",
        "module": "title_agent.server:app",
        "port": int(os.environ["TITLE_AGENT_PORT"])
    },
    {
        "name": "outline_agent_server",
        "module": "outline_agent.server:app",
        "port": int(os.environ["OUTLINE_AGENT_PORT"])
    },
    {
        "name": "routing_agent_server",
        "module": "routing_agent.server:app",
        "port": int(os.environ["ROUTING_AGENT_PORT"])
    },
]

def import_app(module_path: str):
    """Dynamically import the FastAPI app from the module path."""
    try:
        module_name, app_name = module_path.rsplit(":", 1)
        module = importlib.import_module(module_name)
        return getattr(module, app_name)
    except (ImportError, AttributeError) as e:
        raise ValueError(f"Failed to import {module_path}: {str(e)}")

async def start_server(server: Dict[str, str]) -> None:
    """Start a single Uvicorn server asynchronously."""
    try:
        app = import_app(server["module"])
        config = uvicorn.Config(
            app=app,
            #host="0.0.0.0",
            host=server_url,
            port=server["port"],
            log_level="info"
        )
        uvicorn_server = uvicorn.Server(config)
        print(f"Starting {server['name']} on {server_url}:{server['port']}")
        await uvicorn_server.serve()
    except Exception as e:
        print(f"Error starting {server['name']}: {str(e)}")

async def run_client_main():
    from client import main as client_main
    await client_main()

async def main():
    """Run all servers concurrently."""
    tasks = [asyncio.create_task(start_server(server)) for server in servers]

    # Wait briefly to ensure servers are up
    await asyncio.sleep(10)  # Adjust delay if needed
    
    # Call the routing agent client main function
    # It is commented out to avoid blocking the server tasks
    # response = await run_client_main()
    # # Interactive session with the client
    # while True:
    #     user_input = input("User: ")
    #     if user_input.lower() == "quit":
    #         print("Goodbye!")
    #         break
    #     response = await run_client_main()
    #     print(f"Agent: {response}")

    await asyncio.gather(*tasks, return_exceptions=True)
        
if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Shutting down all servers...")
    except Exception as e:
        print(f"Error running servers: {str(e)}")