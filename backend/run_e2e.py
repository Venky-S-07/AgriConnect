"""Self-contained runner for Milestone 2 end-to-end verification."""

import threading
import time
import sys
import uvicorn
from app.main import app
import verify_m2_e2e

def main():
    server = uvicorn.Server(uvicorn.Config(app, host="127.0.0.1", port=8000, log_level="error"))
    t = threading.Thread(target=server.run)
    t.daemon = True
    t.start()
    time.sleep(1.5)

    try:
        verify_m2_e2e.run_e2e_walkthrough()
        exit_code = 0
    except Exception as e:
        print(f"E2E ERROR: {e}")
        exit_code = 1
    finally:
        server.should_exit = True
        t.join(timeout=2.0)

    sys.exit(exit_code)

if __name__ == "__main__":
    main()
