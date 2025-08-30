from fastapi import FastAPI

app = FastAPI(title="LookMyStyle API", version="0.1.0")

@app.get("/")
def root():
    return {"ok": True, "app": "LookMyStyle"}

@app.get("/health")
def health():
    return {"status": "healthy"}
