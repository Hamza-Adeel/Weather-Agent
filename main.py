import os
import requests
from agents import Agent, Runner, RunConfig, OpenAIChatCompletionsModel, AsyncOpenAI, function_tool, SQLiteSession, input_guardrail, GuardrailFunctionOutput
from dotenv import load_dotenv, find_dotenv
import asyncio
from pydantic import BaseModel

load_dotenv()
gemini_api_key = os.getenv("GEMINI_API_KEY")
if not gemini_api_key:
    raise ValueError("GEMINI_API_KEY is not set")

external_client = AsyncOpenAI(
    api_key=gemini_api_key,
    base_url="https://generativelanguage.googleapis.com/v1beta/openai/"
)

model = OpenAIChatCompletionsModel(
    model="gemini-2.0-flash",
    openai_client=external_client,
)

config = RunConfig(
    model=model,
    model_provider=external_client,
    tracing_disabled=True,
)
class WeatherCheckOutput(BaseModel):
    response: str
    isWeatherRelated: bool
guardrail_agent = Agent(
    name="Weather Guardrail Agent",
    instructions="""
        Role:
            Ensure safe, accurate, and factual weather responses only.
        Rules:
            - ✅ Answer only weather or climate-related questions.
            - 🚫 No medical, safety, or travel-risk advice.
            - ✅ Use verified data (no made-up forecasts).
            - 🚫 If info unavailable → say:
                - “Sorry, I can’t access real-time data right now. Please check a trusted weather source.”
            - ✅ Keep tone friendly and concise.
""",
    output_type=WeatherCheckOutput
)

@input_guardrail
async def Weather_input_guardrail(ctx, agent, input_text) -> GuardrailFunctionOutput:
    # Run the guardrail check
    result = await Runner.run(guardrail_agent, input_text, run_config=config)

    # If not weather-related → trigger tripwire
    is_weather = result.final_output.isWeatherRelated if result.final_output else False

    return GuardrailFunctionOutput(
        output_info=result.final_output,
        tripwire_triggered=not is_weather
)

@function_tool
def fetch_weather(city: str) -> str:
    API_KEY = os.getenv("WEATHER_API_KEY")
    base_url = "http://api.weatherapi.com/v1/current.json"
    params = {
        "key": API_KEY,
        "q": city,
        "aqi": "no",
    }
    response = requests.get(base_url, params=params)
    if response.status_code != 200:
        raise Exception(f"Failed to fetch weather data: {response.status_code}")
    data = response.json()
    if "error" in data:
        raise Exception(f"Weather API Error: {data['error']['message']}")
    location = data["location"]["name"]
    temperature = f"{data['current']['temp_c']}°C"
    condition = data["current"]["condition"]["text"]
    return f"The weather in {location} is {temperature} and {condition}"

weather_Agent = Agent(
    name = "Weather Agent",
    instructions = "You are a weather agent your task is to give the current weather update",
    tools = [fetch_weather]
)

agent = Agent(
    name="FirstAgent",
    instructions=f"""You are a helpful assistant your task is to greet user and handsoff to weather agent
                    1. Welcome user politely.
                    3. Handoffs to the weather agent to show the the menu
                """,
    handoffs = [weather_Agent],
    handoff_description = "You need to handsoff to weather agent after welcome message appears",
    input_guardrails=[Weather_input_guardrail]
    )
session = SQLiteSession("my_first_conversation")

async def main():
    print("Hey I'm Your Weather Agent I Can tell you the current weather of any city of Pakistan based on your request.\n(Type 'stop' or 'exit' to quit)\n")
    while True:
        user_input = input("Ask Me About Weather: ")
        termination = ["stop", "exit"]
        if user_input.lower() in termination:
            print("👋 Goodbye! Weather Agent stopped.")
            break
        try:
            result = await Runner.run(
                agent,
                user_input,
                run_config=config,
                session=session
            )
            print("Weather Agent: ", result.final_output)
        except Exception as e:
            print("⚠️ Error:", e)

if __name__ == "__main__":
    asyncio.run(main())