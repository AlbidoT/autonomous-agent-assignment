from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel
from typing import List, Dict

app = FastAPI(title="Autonomous AI Agent Protocol")

# --- In-Memory DBs ---
agents_db: Dict[str, dict] = {}
usage_summary: Dict[str, int] = {}
processed_requests = set()

# --- Pydantic Models ---
class AgentCreate(BaseModel):
    name: str
    description: str
    endpoint: str

class AgentResponse(BaseModel):
    name: str
    description: str
    endpoint: str
    tags: List[str] = []

class UsageLog(BaseModel):
    caller: str
    target: str
    units: int
    request_id: str

# --- Part 1 & 4: Agent Registry APIs ---
@app.post("/agents", response_model=AgentResponse, status_code=status.HTTP_201_CREATED)
def add_agent(agent: AgentCreate):
    key = agent.name.lower()
    if key in agents_db:
        raise HTTPException(status_code=400, detail="Agent already exists")
    
    # Bonus Option B: Simple keyword extraction
    stops = {"from", "a", "an", "the", "and", "or", "in", "on", "to", "with", "data"}
    words = agent.description.lower().replace(",", "").replace(".", "").split()
    tags = list(set([w for w in words if w not in stops]))

    data = agent.model_dump()
    data["tags"] = tags
    agents_db[key] = data
    return data

@app.get("/agents", response_model=List[AgentResponse])
def list_agents():
    return list(agents_db.values())

@app.get("/search", response_model=List[AgentResponse])
def search_agents(q: str):
    query = q.lower()
    return [a for a in agents_db.values() if query in a["name"].lower() or query in a["description"].lower()]

# --- Part 2 & 3: Usage Logging & Edge Cases ---
@app.post("/usage")
def log_usage(log: UsageLog):
    # Ignore duplicate requests
    if log.request_id in processed_requests:
        return {"status": "ignored", "detail": "Duplicate request_id"}
        
    # Reject unknown target agents
    if log.target.lower() not in agents_db:
        raise HTTPException(status_code=404, detail="Unknown target agent")
        
    processed_requests.add(log.request_id)
    usage_summary[log.target] = usage_summary.get(log.target, 0) + log.units
    
    return {"status": "logged"}

@app.get("/usage-summary")
def get_summary():
    return usage_summary