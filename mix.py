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
import platform
from concurrent.futures import ThreadPoolExecutor
import threading

# Store process references for cleanup
processes = []
shutdown_event = threading.Event()

def run_frontend():
    """Run the Vite development server."""
    print("[Frontend] Starting Vite dev server...")
    try:
        process = subprocess.Popen(
            "npm run dev",
            cwd="frontend",
            shell=True,
            creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if platform.system() == "Windows" else 0
        )
        processes.append(process)
        process.wait()
    except Exception as e:
        if not shutdown_event.is_set():
            print(f"[Frontend] Error: {e}")

def run_backend():
    """Run the Flask development server."""
    print("[Backend] Starting Flask server...")
    try:
        process = subprocess.Popen(
            [sys.executable, "run.py"],
            cwd="backend",
            shell=True,
            creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if platform.system() == "Windows" else 0
        )
        processes.append(process)
        process.wait()
    except Exception as e:
        if not shutdown_event.is_set():
            print(f"[Backend] Error: {e}")

def cleanup():
    """Clean up all running processes."""
    shutdown_event.set()
    print("\n[Mix] Shutting down servers...")
    for process in processes:
        try:
            if platform.system() == "Windows":
                # On Windows, use taskkill to terminate process tree
                subprocess.run(
                    f"taskkill /F /T /PID {process.pid}",
                    shell=True,
                    capture_output=True
                )
            else:
                process.terminate()
                process.wait(timeout=5)
        except Exception:
            try:
                process.kill()
            except Exception:
                pass

def dev():
    """Start both frontend and backend development servers concurrently."""
    print("[Mix] Starting MentorMind development servers...")
    print("[Mix] Frontend: http://localhost:5173")
    print("[Mix] Backend:  http://localhost:5000")
    print("[Mix] Press Ctrl+C to stop\n")
    
    try:
        with ThreadPoolExecutor(max_workers=2) as executor:
            frontend_future = executor.submit(run_frontend)
            backend_future = executor.submit(run_backend)
            
            # Wait for both to complete (or be interrupted)
            try:
                while not (frontend_future.done() and backend_future.done()):
                    frontend_future.result(timeout=1)
            except KeyboardInterrupt:
                pass
            except Exception:
                pass
    except KeyboardInterrupt:
        pass
    finally:
        cleanup()

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
