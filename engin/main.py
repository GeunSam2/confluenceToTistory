from fastapi import FastAPI

app = FastAPI()


@app.get("/")
async def root():
    return {"message": "Hello World"}

@app.get("/oauth/confluence/")
async def getTokenConfluence(code , state: str=''):
    returnJson = {
        "code": code,
        "state": state
    }
    return returnJson
    


@app.get("/oauth/tistory")
async def getTokenTistory(code , state: str=''):
    returnJson = {
        "code": code,
        "state": state
    }
    return returnJson