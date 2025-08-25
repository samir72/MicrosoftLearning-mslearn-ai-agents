import os
from dotenv import load_dotenv
import httpx
import json
from mcp.server.fastmcp import FastMCP
from starlette.applications import Starlette
from starlette.routing import Mount, Router
from starlette.responses import JSONResponse
from starlette.requests import Request
from uvicorn import run

# Env variables 
load_dotenv()
OPENWEATHER_API_KEY=os.getenv("OPENWEATHER_API_KEY")
mcp = FastMCP("weather-tools")

@mcp.tool()
async def get_weather(city: str, api_key: str) -> str:
    url = f"https://api.openweathermap.org/data/2.5/weather?q={city}&appid={api_key}&units=metric"
    async with httpx.AsyncClient() as client:
        response = await client.get(url)
        if response.status_code == 200:
            data = response.json()
            return f"Weather in {city}: {data['weather'][0]['description']}, Temp: {data['main']['temp']}°C"
        else:
            return "Error fetching weather data."

# Add HTTP router for direct tool calls
tools_router = Router()
@tools_router.route("/get_weather", methods=["POST"])
#@tools_router.post("/get_weather")
async def http_get_weather(request: Request):
    data = await request.json()
    city = data.get('city')
    api_key = data.get('api_key')
    if not city or not api_key:
        return JSONResponse({"error": "Missing city or api_key"}, status_code=400)
    result = await get_weather(city, api_key)
    return JSONResponse({"result": result})

#app = Starlette(routes=[Mount("/tools", app=tools_router), Mount("/", app=mcp.asgi_app)])
app = Starlette(routes=[Mount("/tools", app=tools_router), Mount("/", app=mcp)])

if __name__ == "__main__":
    run(app, host="0.0.0.0", port=8080)