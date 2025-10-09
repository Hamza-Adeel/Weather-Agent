from fastapi import FastAPI
from pydantic import BaseModel
from agents import Runner, SQLiteSession
from main import weather_Agent
from main import config
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import os

class Message(BaseModel):
    message: str

session = SQLiteSession("Weather_Agent.db")

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://chatbot-ui-henna-rho.vercel.app/",
                   "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/chat")
async def chat(request: Message):
    user_input = request.message.strip()
    if not user_input:
        return {"response": "Please provide a valid message."}

    result = await Runner.run(
        weather_Agent,
        input=user_input, 
        run_config=config,
        session=session,
        )
    return {"response": result.final_output or "Sorry, I couldn't compose that."}


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("server:app", host="0.0.0.0", port=port)