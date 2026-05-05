import argparse
import logging
from fastapi import FastAPI
from pydantic import BaseModel
from typing import Dict, List, Any

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

app = FastAPI(title="2PC Participant")

class PrepareRequest(BaseModel):
    transaction_id: str
    from_account: str
    to_account: str
    amount: int

class CompletionRequest(BaseModel):
    transaction_id: str

# State
balances: Dict[str, int] = {}
pending_transactions: Dict[str, List[Dict[str, Any]]] = {}
locked_accounts = set()
simulate_failure = False
port = 0
logger = logging.getLogger("Participant")

@app.post("/prepare")
async def prepare(request: PrepareRequest):
    """Phase 1: Vote based on balances and locks"""
    global simulate_failure
    logger.info(f"Received PREPARE for tx: {request.transaction_id}")
    
    involved = []
    if request.from_account in balances: involved.append(request.from_account)
    if request.to_account in balances: involved.append(request.to_account)
    
    if not involved:
        logger.info(f"No relevant accounts. Voting COMMIT (no-op) for tx: {request.transaction_id}")
        return {"vote": "VOTE_COMMIT"}
        
    if simulate_failure:
        logger.warning(f"Simulating failure! Voting ABORT for tx: {request.transaction_id}")
        simulate_failure = False
        return {"vote": "VOTE_ABORT", "reason": "Simulated node failure"}
    
    # 1. Check for Strict 2PL Locks
    for acc in involved:
        if acc in locked_accounts:
            logger.warning(f"Concurrency conflict! Account {acc} is locked. Voting ABORT for tx: {request.transaction_id}")
            return {"vote": "VOTE_ABORT", "reason": f"Account {acc} is locked by an ongoing transaction"}

    # 2. Check logic and reserve funds
    pending_ops = []
    
    if request.from_account in balances:
        if balances[request.from_account] >= request.amount:
            pending_ops.append({"type": "debit", "account": request.from_account, "amount": request.amount})
        else:
            logger.warning(f"Insufficient funds for tx: {request.transaction_id}")
            return {"vote": "VOTE_ABORT", "reason": f"Insufficient funds in account {request.from_account}"}
            
    if request.to_account in balances:
        pending_ops.append({"type": "credit", "account": request.to_account, "amount": request.amount})
        
    # 3. Apply Locks and save pending transaction
    if pending_ops:
        for acc in involved:
            locked_accounts.add(acc)
            
        pending_transactions[request.transaction_id] = pending_ops
        logger.info(f"Locked accounts {involved}. Voting COMMIT for tx: {request.transaction_id}")
        
    return {"vote": "VOTE_COMMIT"}

@app.post("/commit")
async def commit(request: CompletionRequest):
    """Phase 2: Commit pending changes and release locks"""
    logger.info(f"Received GLOBAL_COMMIT for tx: {request.transaction_id}")
    if request.transaction_id in pending_transactions:
        ops = pending_transactions.pop(request.transaction_id)
        for op in ops:
            if op["type"] == "debit":
                balances[op["account"]] -= op["amount"]
            else:
                balances[op["account"]] += op["amount"]
            locked_accounts.discard(op["account"]) # Release lock
        logger.info(f"Committed changes and released locks for tx: {request.transaction_id}")
        return {"status": "committed"}
    return {"status": "ignored"}

@app.post("/abort")
async def abort(request: CompletionRequest):
    """Phase 2: Rollback pending changes and release locks"""
    logger.warning(f"Received GLOBAL_ABORT for tx: {request.transaction_id}")
    if request.transaction_id in pending_transactions:
        ops = pending_transactions.pop(request.transaction_id)
        for op in ops:
            locked_accounts.discard(op["account"]) # Release lock
        logger.info(f"Rolled back changes and released locks for tx: {request.transaction_id}")
        return {"status": "aborted"}
    return {"status": "ignored"}

@app.post("/simulate_failure")
async def trigger_failure():
    """Toggle simulated failure flag"""
    global simulate_failure
    simulate_failure = not simulate_failure
    logger.warning(f"Failure simulation flag is now: {simulate_failure}")
    return {"status": "success", "simulate_failure": simulate_failure}

@app.get("/status")
async def status():
    """Return local balances and status for the UI"""
    return {
        "balances": balances,
        "pending_transactions": pending_transactions,
        "locked_accounts": list(locked_accounts),
        "simulate_failure": simulate_failure
    }

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, required=True)
    parser.add_argument("--accounts", type=str, required=True, help="Comma separated Account:Balance e.g., A:100,C:50")
    args = parser.parse_args()
    
    port = args.port
    logger = logging.getLogger(f"Participant-{port}")
    
    # Parse accounts
    for acc_str in args.accounts.split(","):
        if ":" in acc_str:
            acc, bal = acc_str.split(":")
            balances[acc] = int(bal)
        
    logger.info(f"Starting participant on port {port} with balances: {balances}")
    
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=port, log_level="error")
