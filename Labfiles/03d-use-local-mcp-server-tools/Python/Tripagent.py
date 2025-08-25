import os
from dotenv import load_dotenv
import time
import json
import httpx
from azure.ai.projects import AIProjectClient
from azure.ai.agents.models import FunctionTool
from azure.identity import DefaultAzureCredential

# Env variables 
load_dotenv()
PROJECT_ENDPOINT=os.getenv("SA_PROJECT_ENDPOINT")
MODEL_DEPLOYMENT_NAME=os.getenv("SA_MODEL_DEPLOYMENT_NAME")
MCP_SERVER_URL=os.getenv("WEATHER_MCP_SERVER_URL") # HTTP endpoint on MCP server
OPENWEATHER_API_KEY=os.getenv("OPENWEATHER_API_KEY")

# Custom tool function that calls MCP server
def fetch_weather_from_mcp(location: str) -> str:
    """
    Fetches weather via MCP server.
    :param location: The city name.
    :return: Weather summary as JSON string.
    """
    payload = {"city": location, "api_key": OPENWEATHER_API_KEY}
    response = httpx.post(MCP_SERVER_URL, json=payload)
    
    if response.status_code == 200:
        print(f"Weather data for {location}: {response.json()}")
        return json.dumps(response.json())
    return json.dumps({"error": "Failed to fetch weather"})

# Initialize client
client = AIProjectClient(endpoint=PROJECT_ENDPOINT, credential=DefaultAzureCredential())

# Create agents
researcher = client.agents.create_agent(
    model=MODEL_DEPLOYMENT_NAME,
    name="ResearcherAgent",
    instructions="Research potential trip destinations for a 5-day trip to Europe in September 2025. Suggest 3 cities."
)

weather_tools = FunctionTool(functions={fetch_weather_from_mcp})
weather_agent = client.agents.create_agent(
    model=MODEL_DEPLOYMENT_NAME,
    name="WeatherAgent",
    instructions="Fetch weather forecasts for given cities using the fetch_weather_from_mcp tool.",
    tools=weather_tools.definitions
)

planner = client.agents.create_agent(
    model=MODEL_DEPLOYMENT_NAME,
    name="PlannerAgent",
    instructions="Compile destinations and weather into a 5-day itinerary Markdown report."
)

# Orchestration function
def run_agent(thread_id, agent_id, user_message):
    client.agents.messages.create(thread_id=thread_id, role="user", content=user_message)
    run = client.agents.runs.create(thread_id=thread_id, agent_id=agent_id)
    while run.status in ["queued", "in_progress", "requires_action"]:
        time.sleep(1)
        run = client.agents.runs.get(thread_id=thread_id, run_id=run.id)
        if run.status == "requires_action":
            tool_calls = run.required_action.submit_tool_outputs.tool_calls
            tool_outputs = []
            for tool_call in tool_calls:
                if tool_call.function.name == "fetch_weather_from_mcp":
                    args = json.loads(tool_call.function.arguments)
                    output = fetch_weather_from_mcp(args["location"])
                    print(f"Tool call output: {output}")
                    tool_outputs.append({"tool_call_id": tool_call.id, "output": output})
            client.agents.runs.submit_tool_outputs(thread_id=thread_id, run_id=run.id, tool_outputs=tool_outputs)
    messages = [msg for msg in client.agents.messages.list(thread_id=thread_id) if msg["role"] == "assistant"]
    #return messages[-1]["content"] if messages else ""
    return messages[0]["content"] if messages else ""

# Run the workflow
thread = client.agents.threads.create()  # Shared thread for simplicity

# Step 1: Research destinations
#destinations = run_agent(thread.id, researcher.id, "Plan a 3-day trip to Europe in September 2025. Return only a comma-separated list of 3 cities.")
destinations = run_agent(thread.id, researcher.id,"Pick three cities in Europe for a trip in September 2025. Respond only with a JSON object with a 'cities' property containing an array of city names.")

print(f"Destinations: {destinations}")

# Step 2: Fetch weather (parse destinations, assume comma-separated)
#cities = [city.strip() for city in destinations.split(",")[:3]]  # e.g., ["Paris", "Rome", "Berlin"]
# Extract the JSON string from the nested structure
json_string = destinations[0]['text']['value']

# Remove the ```json and ``` markers (optional, if you know the string is clean JSON)
# If the string is always wrapped in ```json, you can strip it
json_string = json_string.strip('```json')

# Parse the JSON string into a Python dictionary
parsed_data = json.loads(json_string)

# Retrieve the value of the "cities" key
cities = parsed_data["cities"]
print(cities)  # Output: ['Barcelona', 'Vienna', 'Prague']
print(f"Cities to check weather: {cities}")
weather_data = {}
for city in cities:
    weather = run_agent(thread.id, weather_agent.id, f"Get weather for {city} in September 2025.")
    weather_data[city] = weather
    print(f"Fetched weather for {city}: {weather_data[city]}")
#print(f"Weather Data: {weather_data}")
# Step 3: Plan itinerary
#input_data = f"Destinations: {', '.join(cities)}\nWeather: {json.dumps(weather_data)}"
input_data = weather_data
for city in cities:
    itinerary = run_agent(thread.id, planner.id, f"Create a short 1-day itinerary for a trip to {city} in September 2025. Include destinations and weather data: {input_data[city]}")
    print(f"Itinerary for {city}:\n{itinerary}\n")

#itinerary = run_agent(thread.id, planner.id, f"Create a 5-day itinerary for a trip to three European cities in September 2025. Include destinations and weather data: {input_data[city]}")
#print(f"Final Itinerary : {itinerary}")  # Output the final plan

# Cleanup
client.agents.delete_agent(researcher.id)
client.agents.delete_agent(weather_agent.id)
client.agents.delete_agent(planner.id)
client.agents.threads.delete(thread.id)