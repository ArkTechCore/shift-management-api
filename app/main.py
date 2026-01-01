from fastapi import FastAPI

app = FastAPI(title="Shift Management API", version="0.1.0")

@app.get("/")
def root():
    return {"status": "ok", "service": "shift-management-api"}

@app.get("/health")
def health():
    return {"ok": True}
