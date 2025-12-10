from fastapi import FastAPI

#create FastAPI object called app
app = FastAPI()

#defines route /health that returns a small JSON response to test the server
@app.get("/health")
def health_check():
    return {"status": "ok"}