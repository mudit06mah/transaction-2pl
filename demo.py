import subprocess
import time
import requests
import sys
import os

def print_header(msg):
    print("\n" + "="*70)
    print(f" {msg} ".center(70, "="))
    print("="*70 + "\n")

def main():
    print_header("STARTING 2PC DISTRIBUTED TRANSACTION DEMO")
    
    # Store references to the subprocesses so we can terminate them later
    processes = []
    
    try:
        # 1. Start Participant 1 on port 8001
        print("-> Starting Participant 1 on port 8001...")
        p1 = subprocess.Popen([sys.executable, "participant.py", "--port", "8001"])
        processes.append(p1)
        
        # 2. Start Participant 2 on port 8002
        print("-> Starting Participant 2 on port 8002...")
        p2 = subprocess.Popen([sys.executable, "participant.py", "--port", "8002"])
        processes.append(p2)
        
        # 3. Start Coordinator on port 8000
        print("-> Starting Coordinator on port 8000...")
        c = subprocess.Popen([
            sys.executable, "coordinator.py", 
            "--port", "8000", 
            "--participants", "http://127.0.0.1:8001", "http://127.0.0.1:8002"
        ])
        processes.append(c)
        
        # Give the FastAPI servers a few seconds to initialize
        print("\nWaiting for servers to initialize...\n")
        time.sleep(3)
        
        # =========================================================
        # SCENARIO 1: Successful Transaction
        # =========================================================
        print_header("SCENARIO 1: Successful Transaction")
        print("Both participants will successfully lock resources and vote to COMMIT.")
        print("-" * 70)
        
        payload_success = {
            "transaction_id": "tx-1001",
            "details": "Transfer $50 from Account A to Account B"
        }
        
        print(f"CLIENT: Sending request to Coordinator: {payload_success}")
        
        # Send request to the coordinator
        response = requests.post("http://127.0.0.1:8000/transaction", json=payload_success)
        
        print("-" * 70)
        print(f"CLIENT: Coordinator Response Code: {response.status_code}")
        print(f"CLIENT: Coordinator Response Body: {response.text}")
        
        # Pause briefly to make logs easier to read
        time.sleep(3)
        
        # =========================================================
        # SCENARIO 2: Failing Transaction (Simulated Participant Abort)
        # =========================================================
        print_header("SCENARIO 2: Failing Transaction (Simulated Abort)")
        print("We will instruct Participant 1 to simulate a failure.")
        print("Participant 1 will vote ABORT. The Coordinator will detect this")
        print("and issue a GLOBAL_ABORT to both participants.")
        print("-" * 70)
        
        # Trigger failure on Participant 1
        print("CLIENT: Instructing Participant 1 (port 8001) to fail the next prepare request...")
        requests.post("http://127.0.0.1:8001/simulate_failure")
        
        payload_fail = {
            "transaction_id": "tx-1002",
            "details": "Transfer $100 from Account B to Account C"
        }
        
        print(f"CLIENT: Sending request to Coordinator: {payload_fail}")
        
        try:
            # Send request to the coordinator
            response2 = requests.post("http://127.0.0.1:8000/transaction", json=payload_fail)
            print("-" * 70)
            print(f"CLIENT: Coordinator Response Code: {response2.status_code}")
            print(f"CLIENT: Coordinator Response Body: {response2.text}")
        except requests.exceptions.RequestException as e:
            # We expect a 400 Bad Request if the transaction aborts, which `requests` handles gracefully
            # unless we use `raise_for_status()`, but it's good practice to wrap it.
            print(f"CLIENT: Request failed: {e}")
            
        time.sleep(3)
        
    finally:
        # =========================================================
        # CLEANUP
        # =========================================================
        print_header("Cleaning up processes")
        print("Shutting down Coordinator and Participants...")
        for p in processes:
            p.terminate()
        for p in processes:
            p.wait()
        print("Done. Goodbye!")

if __name__ == "__main__":
    main()
