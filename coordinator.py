import argparse
import asyncio
import logging
import time
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import httpx
import os

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("Coordinator")

app = FastAPI(title="2PC Coordinator")

# Ensure static dir exists
os.makedirs("static", exist_ok=True)
app.mount("/static", StaticFiles(directory="static"), name="static")

class TransactionRequest(BaseModel):
    transaction_id: str
    from_account: str
    to_account: str
    amount: int
    
class URLRequest(BaseModel):
    url: str

participants = []
transaction_logs = []

def add_log(msg: str):
    timestamp = time.strftime("%H:%M:%S")
    log_msg = f"[{timestamp}] {msg}"
    logger.info(log_msg)
    transaction_logs.append(log_msg)
    if len(transaction_logs) > 50:
        transaction_logs.pop(0)

@app.get("/")
async def root():
    from fastapi.responses import RedirectResponse
    return RedirectResponse(url="/static/index.html")

@app.get("/status")
async def get_status():
    global participants
    participant_states = {}
    
    async with httpx.AsyncClient() as client:
        for p in participants:
            try:
                res = await client.get(f"{p}/status", timeout=1.0)
                if res.status_code == 200:
                    participant_states[p] = res.json()
                else:
                    participant_states[p] = {"error": "Invalid response"}
            except Exception:
                participant_states[p] = {"error": "Offline"}
                
    return {
        "participants": participant_states,
        "logs": transaction_logs
    }

@app.post("/simulate_failure")
async def proxy_simulate_failure(req: URLRequest):
    async with httpx.AsyncClient() as client:
        await client.post(f"{req.url}/simulate_failure", timeout=2.0)
    return {"status": "success"}

async def execute_transaction(request: TransactionRequest):
    add_log(f"--- NEW TRANSACTION: {request.transaction_id} ---")
    add_log(f"[{request.transaction_id}] Transfer ${request.amount} from {request.from_account} to {request.to_account}")
    
    # PHASE 1: PREPARE
    add_log(f"[{request.transaction_id}] PHASE 1: Sending PREPARE to participants.")
    prepare_tasks = []
    
    async with httpx.AsyncClient() as client:
        for p in participants:
            req = client.post(f"{p}/prepare", json=request.model_dump(), timeout=2.0)
            prepare_tasks.append(req)
        
        try:
            responses = await asyncio.gather(*prepare_tasks, return_exceptions=True)
        except Exception as e:
            responses = [e] * len(participants)

    all_prepared = True
    for p, response in zip(participants, responses):
        if isinstance(response, Exception):
            add_log(f"[{request.transaction_id}] ABORT: Participant {p} timed out/failed.")
            all_prepared = False
            break
        
        if response.status_code == 200:
            data = response.json()
            if data.get("vote") == "VOTE_COMMIT":
                add_log(f"[{request.transaction_id}] Participant {p} voted COMMIT")
            else:
                reason = data.get("reason", "Unknown")
                add_log(f"[{request.transaction_id}] ABORT: Participant {p} voted ABORT. Reason: {reason}")
                all_prepared = False
                break
        else:
            add_log(f"[{request.transaction_id}] ABORT: Participant {p} returned error {response.status_code}")
            all_prepared = False
            break

    # SIMULATED DELAY
    if all_prepared:
        add_log(f"[{request.transaction_id}] Simulating 10s network delay. Locks are active.")
        await asyncio.sleep(10)

    # PHASE 2: COMPLETION
    async with httpx.AsyncClient() as client:
        completion_tasks = []
        if all_prepared:
            add_log(f"[{request.transaction_id}] PHASE 2: Sending GLOBAL_COMMIT.")
            for p in participants:
                req = client.post(f"{p}/commit", json={"transaction_id": request.transaction_id}, timeout=2.0)
                completion_tasks.append(req)
            await asyncio.gather(*completion_tasks, return_exceptions=True)
            add_log(f"[{request.transaction_id}] Transaction COMMITTED.")
        else:
            add_log(f"[{request.transaction_id}] PHASE 2: Sending GLOBAL_ABORT.")
            for p in participants:
                req = client.post(f"{p}/abort", json={"transaction_id": request.transaction_id}, timeout=2.0)
                completion_tasks.append(req)
            await asyncio.gather(*completion_tasks, return_exceptions=True)
            add_log(f"[{request.transaction_id}] Transaction ABORTED.")

@app.post("/transaction")
async def process_transaction(request: TransactionRequest, background_tasks: BackgroundTasks):
    # Run the transaction process in the background so the UI doesn't hang waiting for the sleep
    background_tasks.add_task(execute_transaction, request)
    return {"status": "started", "message": "Transaction initiated in background"}

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument("--participants", nargs="+", required=True)
    args = parser.parse_args()
    
    participants = args.participants
    add_log("Coordinator started.")
    
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=args.port, log_level="error")
