# Interactive Two-Phase Commit (2PC) & Strict 2PL Demo
<img width="1600" height="748" alt="image" src="https://github.com/user-attachments/assets/f4761804-4d4d-4c2c-936c-aa83783aeb88" />


This project provides a fully interactive, academic demonstration of the **Two-Phase Commit (2PC)** distributed transaction protocol, paired with **Strict Two-Phase Locking (2PL)**. It is built using Python (FastAPI) and a minimalistic vanilla HTML/CSS/JS frontend.

* Hello
* Bello

## Key Features

- **Distributed Architecture:** Features a central Coordinator and multiple distinct Participant nodes communicating via asynchronous HTTP requests.
- **Strict 2PL (Two-Phase Locking):** Participants enforce exclusive locks on accounts during the transaction's prepare phase, actively preventing dirty reads and concurrency conflicts.
- **Interactive Web UI:** A clean, minimalistic dashboard allows you to initiate transfers, observe real-time account balances, and toggle simulated node crashes.
- **Concurrent Transaction Testing:** An artificial 10-second delay exists between the Prepare and Commit phases, giving you a window to initiate concurrent transactions from the UI and visibly observe the locking mechanisms reject conflicting requests.

## Architecture

1. **Coordinator (`coordinator.py`)**: Manages the distributed transaction. It initiates Phase 1 (Prepare) and Phase 2 (Commit/Abort) by coordinating with all registered participants.
2. **Participants (`participant.py`)**: Stateful nodes managing in-memory account balances. They place locks on resources during Phase 1, vote on whether to commit or abort based on validations, and then execute the Coordinator's final decision in Phase 2.
3. **Web Dashboard (`static/index.html`)**: A real-time monitoring and control interface.
4. **Master Script (`web_demo.py`)**: Automates local server startup by spinning up the coordinator and the participants with pre-configured account balances.

## Setup & Running the Demo

1. **Install Dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Run the Application:**
   ```bash
   python web_demo.py
   ```

3. **Access the Dashboard:**
   Open your browser and navigate to `http://localhost:8000`.

## How to Test the Protocol

1. **Successful Transaction:** Initiate a transfer from Account A to Account B. You will see both nodes prepare the transaction, place locks, wait, and then commit.
2. **Concurrency & Locking (Strict 2PL):** Initiate a transfer from Account A to Account B. While the 10-second timer is active and the `LOCKED` badges are visible, attempt to initiate a second transfer (e.g., C to B). The second transaction will immediately abort because Account B is already locked.
3. **Simulating Node Failure:** Click the "Simulate Node Crash" button on one of the participants, then initiate a transaction involving that participant. The node will vote `ABORT`, and the Coordinator will globally abort the transaction.
