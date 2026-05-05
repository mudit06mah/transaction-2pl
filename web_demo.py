import subprocess
import time
import sys
import signal

def print_header(msg):
    print("\n" + "="*70)
    print(f" {msg} ".center(70, "="))
    print("="*70 + "\n")

def main():
    print_header("STARTING 2PC INTERACTIVE WEB DEMO")
    
    processes = []
    
    def signal_handler(sig, frame):
        print("\nShutting down servers...")
        for p in processes:
            p.terminate()
        sys.exit(0)
        
    signal.signal(signal.SIGINT, signal_handler)

    try:
        # 1. Start Participant 1 on port 8001 with Account A
        print("-> Starting Participant 1 (port 8001, holds Account A: $1000)...")
        p1 = subprocess.Popen([sys.executable, "participant.py", "--port", "8001", "--accounts", "A:1000"])
        processes.append(p1)
        
        # 2. Start Participant 2 on port 8002 with Account B and C
        print("-> Starting Participant 2 (port 8002, holds Account B: $1000, C: $500)...")
        p2 = subprocess.Popen([sys.executable, "participant.py", "--port", "8002", "--accounts", "B:1000,C:500"])
        processes.append(p2)
        
        # 3. Start Coordinator on port 8000
        print("-> Starting Coordinator on port 8000...")
        c = subprocess.Popen([
            sys.executable, "coordinator.py", 
            "--port", "8000", 
            "--participants", "http://127.0.0.1:8001", "http://127.0.0.1:8002"
        ])
        processes.append(c)
        
        print("\nWaiting for servers to initialize...\n")
        time.sleep(3)
        
        print_header("READY!")
        print("The interactive demo is running.")
        print("Please open your web browser and go to:")
        print("\n\t http://localhost:8000 \n")
        print("Press Ctrl+C to stop the servers.")
        
        # Keep the main thread alive
        while True:
            time.sleep(1)
            
    except KeyboardInterrupt:
        pass
    finally:
        print("\nShutting down servers...")
        for p in processes:
            p.terminate()

if __name__ == "__main__":
    main()
