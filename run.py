import sys
import asyncio
import uvicorn

if __name__ == "__main__":
    if sys.platform == "win32":
        # Force ProactorEventLoop on Windows so Playwright can use subprocesses
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    
    # Run uvicorn programmatically, setting loop="none" so it doesn't try to 
    # override the ProactorEventLoopPolicy we just set.
    uvicorn.run("backend.main:app", host="127.0.0.1", port=8000, reload=True, loop="none")
