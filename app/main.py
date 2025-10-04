from fastapi import FastAPI

app = FastAPI(title="Expense Splitter API")

@app.get("/")
def read_root():
    return {"message": "Hello, Debugging Divas!"}

@app.get("/health")
def health():
    return {"status": "ok"}
