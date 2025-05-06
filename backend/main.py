from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from backend.agent.agent import Agent
import json
from datetime import datetime
from pydantic import BaseModel
import uvicorn
from typing import Dict, Any

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

class AskRequest(BaseModel):
    question: str

store: Dict[str, Any] = {
    "parsed": None,
    "agent": None
}

@app.post("/upload_log")
async def upload_log(request: Request):
    # Parse incoming telemetry JSON
    json_data = await request.json()
    store["parsed"] = json_data

    # timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    # filename = f"telemetry_dump_{timestamp}.json"
    # with open(filename, "w") as f:
    #     json.dump(json_data, f, indent=2)
    # print(f"Saved uploaded telemetry to {filename}")

    # Instantiate the Agent ONCE with parsed data
    store["agent"] = Agent(store["parsed"])
    return {"status": "agent instantiated", "keys": list(json_data.keys())}

@app.post("/ask")
async def ask_question(req: AskRequest):
    agent = store.get("agent")
    if agent is None:
        return {"error": "No flight data uploaded yet. Please POST to /upload_log first."}

    answer = agent.chat(req.question)
    # print("this is answer from chatbot",answer)
    return {"answer": answer}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
