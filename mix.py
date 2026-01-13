#!/usr/bin/env python3
"""
MentorMind Build Runner

Concurrently launches the Vite dev server and Flask server for development.

Usage:
    python mix.py dev     - Start both frontend and backend dev servers
    python mix.py build   - Build frontend for production
"""

import subprocess
import sys
import os
import signal
from concurrent.futures import ThreadPoolExecutor

# Store process references for cleanup
processes = []

def run_frontend():
    """Run the Vite development server."""
    print("[Frontend] Starting Vite dev server...")
    process = subprocess.Popen(
        ["npm", "run", "dev"],
        cwd="frontend",
        shell=True
    )
    processes.append(process)
    process.wait()

def run_backend():
    """Run the Flask development server."""
    print("[Backend] Starting Flask server...")
    process = subprocess.Popen(
        [sys.executable, "run.py"],
        cwd="backend",
        shell=True
    )
    processes.append(process)
    process.wait()

def cleanup(signum=None, frame=None):
    """Clean up all running processes."""
    print("\n[Mix] Shutting down servers...")
    for process in processes:
        try:
            process.terminate()
            process.wait(timeout=5)
        except Exception:
            process.kill()
    sys.exit(0)

def dev():
    """Start both frontend and backend development servers concurrently."""
    # Register signal handlers for graceful shutdown
    signal.signal(signal.SIGINT, cleanup)
    signal.signal(signal.SIGTERM, cleanup)
    
    print("[Mix] Starting MentorMind development servers...")
    print("[Mix] Frontend: http://localhost:5173")
    print("[Mix] Backend:  http://localhost:5000")
    print("[Mix] Press Ctrl+C to stop\n")
    
    with ThreadPoolExecutor(max_workers=2) as executor:
        executor.submit(run_frontend)
        executor.submit(run_backend)

def build():
    """Build the frontend for production."""
    print("[Mix] Building frontend for production...")
    subprocess.run(["npm", "run", "build"], cwd="frontend", shell=True)
    print("[Mix] Build complete! Output in frontend/dist/")

def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    
    command = sys.argv[1]
    
    if command == "dev":
        dev()
    elif command == "build":
        build()
    else:
        print(f"Unknown command: {command}")
        print(__doc__)
        sys.exit(1)

if __name__ == "__main__":
    main()
