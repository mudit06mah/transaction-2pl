# Two-Phase Commit (2PC) Protocol Demo

This project provides a simple, fully functioning Python implementation of the Two-Phase Commit (2PC) distributed transaction protocol using FastAPI.

## Architecture

1. **Coordinator (`coordinator.py`)**: Manages the distributed transaction. It initiates Phase 1 (Prepare) and Phase 2 (Commit/Abort) by coordinating with all registered participants.
2. **Participants (`participant.py`)**: Simulate distributed databases or resource managers. They simulate locking resources, checking constraints, and voting to either commit or abort the transaction.
3. **Demo Script (`demo.py`)**: Automates the entire process by spinning up a coordinator and two participants locally, and firing off transactions to demonstrate both successful and failed scenarios.

## Requirements

- Python 3.x
- Dependencies defined in `requirements.txt`

## Setup & Running the Demo

1. **Install Dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Run the Automated Demo:**
   ```bash
   python demo.py
   ```

## What `demo.py` does:

When you run the demo script, you will see heavily commented logs printed to your console demonstrating the distributed protocol:

1. Spins up **one Coordinator** on port `8000`.
2. Spins up **two Participants** on ports `8001` and `8002`.
3. **Scenario 1 (Successful Transaction):** Sends a transaction request to the Coordinator. You will see both participants receive the `PREPARE` request, vote `VOTE_COMMIT`, followed by the Coordinator sending a `GLOBAL_COMMIT` to finalize the transaction.
4. **Scenario 2 (Simulated Failure):** Triggers a simulated failure on Participant 1 via a special endpoint.
5. Sends a second transaction request. Participant 1 will vote `VOTE_ABORT` during Phase 1. The Coordinator detects this failure and issues a `GLOBAL_ABORT` message to roll back the transaction on all participants.
6. Gracefully shuts down all spawned background servers.
