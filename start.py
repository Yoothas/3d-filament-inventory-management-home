#!/usr/bin/env python3
"""
Unified launcher for 3D Filament Inventory Management.
Starts both the Flask API and Streamlit Dashboard in one command.

Usage:
    python start.py              # Start both services
    python start.py --api-only   # Start Flask API only
    python start.py --dash-only  # Start Streamlit Dashboard only
"""

import argparse
import os
import signal
import subprocess
import sys
import time

# Always run from the project directory (so it works from anywhere)
os.chdir(os.path.dirname(os.path.abspath(__file__)))


def main():
    parser = argparse.ArgumentParser(description="Launch Filament Inventory services")
    parser.add_argument("--api-only", action="store_true", help="Start Flask API only")
    parser.add_argument("--dash-only", action="store_true", help="Start Dashboard only")
    args = parser.parse_args()

    start_api = not args.dash_only
    start_dash = not args.api_only

    procs: list[subprocess.Popen] = []

    def shutdown(sig=None, frame=None):
        for p in procs:
            p.terminate()
        for p in procs:
            try:
                p.wait(timeout=5)
            except subprocess.TimeoutExpired:
                p.kill()
        sys.exit(0)

    signal.signal(signal.SIGINT, shutdown)
    signal.signal(signal.SIGTERM, shutdown)

    print("=" * 50)
    print("  3D Filament Inventory Management")
    print("=" * 50)
    print()

    if start_api:
        api_proc = subprocess.Popen(
            [sys.executable, "app.py"],
            stdout=sys.stdout,
            stderr=sys.stderr,
        )
        procs.append(api_proc)
        print("  Flask API:   http://localhost:5000")

    if start_dash:
        if start_api:
            time.sleep(2)  # let Flask finish binding
        dash_proc = subprocess.Popen(
            [
                sys.executable, "-m", "streamlit", "run", "dashboard.py",
                "--server.headless", "true",
                "--browser.gatherUsageStats", "false",
            ],
            stdout=sys.stdout,
            stderr=sys.stderr,
        )
        procs.append(dash_proc)
        print("  Dashboard:   http://localhost:8501")

    print()
    print("  Press Ctrl+C to stop all services")
    print("=" * 50)

    # Wait for any process to exit
    while True:
        for p in procs:
            ret = p.poll()
            if ret is not None:
                print(f"\nProcess exited with code {ret}. Shutting down...")
                shutdown()
        time.sleep(1)


if __name__ == "__main__":
    main()
