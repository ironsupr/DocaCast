from fastapi import FastAPI
from .api.v1.health import router as health_router

app = FastAPI(title="Adobe Hackathon Finale API", version="0.1.0")

# Routers
app.include_router(health_router)

# Optional: run with `python -m backend.app.main`
if __name__ == "__main__":
    import uvicorn
    # Run from the backend directory: python -m app.main
    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=True)
