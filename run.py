import sys
import asyncio
import uvicorn

if __name__ == "__main__":
    if sys.platform == "win32":
        # ProactorEventLoop is required for Playwright subprocess support on Windows.
        # reload=True is incompatible with ProactorEventLoop (triggers WinError 87
        # in asyncio IOCP socket accept). Keep reload=False in production.
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

    uvicorn.run(
        "backend.main:app",
        host="127.0.0.1",
        port=8000,
        reload=False,   # reload=True conflicts with ProactorEventLoop on Windows
        loop="none",    # don't override our event loop policy
    )
