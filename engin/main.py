from fastapi import FastAPI

app = FastAPI()

## User's Token ans state dict
confluenceTokenDict = {}
tistoryTokenDict = {}

@app.get("/")
async def root():
    return {"message": "Hello World"}

@app.get("/oauth/confluence")
async def getTokenConfluence(code , state: str=''):
    returnJson = {
        "code": code,
        "state": state
    }
    confluenceTokenDict[state] = code
    returnJson['all'] = confluenceTokenDict
    return returnJson
    


@app.get("/oauth/tistory")
async def getTokenTistory(code , state: str=''):
    returnJson = {
        "code": code,
        "state": state
    }
    return returnJson