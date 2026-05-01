#!/usr/bin/env python
"""
run_api.py — Convenience launcher for the DermaVision API
==========================================================

Usage
-----
    # From repo root (with venv active)
    python run_api.py

    # Custom host/port
    python run_api.py --host 0.0.0.0 --port 8080

    # Production (no reload, multiple workers)
    python run_api.py --no-reload --workers 4

Equivalent uvicorn command
--------------------------
    uvicorn src.api.main:app --reload --host 127.0.0.1 --port 8000

Docs
----
    Swagger UI  → http://localhost:8000/docs
    ReDoc       → http://localhost:8000/redoc
"""

import argparse
import uvicorn


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Run the DermaVision FastAPI server")
    p.add_argument("--host", default="127.0.0.1", help="Bind host (default: 127.0.0.1)")
    p.add_argument("--port", type=int, default=8000, help="Bind port (default: 8000)")
    p.add_argument("--no-reload", dest="reload", action="store_false",
                   help="Disable auto-reload (use in production)")
    p.add_argument("--workers", type=int, default=1,
                   help="Number of worker processes (default: 1, disable reload for >1)")
    p.set_defaults(reload=True)
    return p.parse_args()


if __name__ == "__main__":
    args = parse_args()
    workers = args.workers if not args.reload else 1  # reload incompatible with >1 workers
    print(f"Starting DermaVision API → http://{args.host}:{args.port}")
    print(f"  Swagger UI → http://{args.host}:{args.port}/docs")
    print(f"  ReDoc      → http://{args.host}:{args.port}/redoc")
    uvicorn.run(
        "src.api.main:app",
        host=args.host,
        port=args.port,
        reload=args.reload,
        workers=workers,
    )
