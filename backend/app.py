"""FastAPI entrypoint for deployment.

This service intentionally stays lightweight on startup so Render can keep the
container alive and expose HTTP endpoints without running the simulation loop.
"""

from fastapi import FastAPI

from config import PROJECT_NAME, PROJECT_VERSION, SAFE_RANGES


app = FastAPI(title=PROJECT_NAME, version=PROJECT_VERSION)


@app.get("/")
def root():
    return {
        "message": "API running",
        "project": PROJECT_NAME,
        "version": PROJECT_VERSION,
    }


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/config")
def config():
    return {
        "project": PROJECT_NAME,
        "version": PROJECT_VERSION,
        "safe_ranges": SAFE_RANGES,
    }