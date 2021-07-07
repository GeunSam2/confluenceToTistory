from fastapi import Depends, FastAPI, Response, Cookie, HTTPException, Query, BackgroundTasks
from fastapi.security import OAuth2PasswordBearer
from .makeHtml import MakeHtml
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse

app = FastAPI()

origins = ['*']

## CORS allow all. I know it is unsecure. But this is prototype
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

## User's Token ans state dict. Will replace this to redis later.
confluenceTokenDict = {}
tistoryTokenDict = {}

# Get MakeHtml.py Class.
makeHtml = MakeHtml()

# Depends for some api have to check cookies for confluence
def getConfluenceToken(confSESSION: str = Cookie(None)):
    if (confSESSION in confluenceTokenDict):
        return confluenceTokenDict[confSESSION]
    else:
        raise HTTPException(status_code=401, detail="Invalid confSESSION Cookie : {}".format(confSESSION))

# Nothing
@app.get("/")
async def root(token: str = Depends(oauth2_scheme)):
    return {"message": "Hello World", "token": token}

# Get Oauth url for confluence
@app.get("/getoauthurl/confluence")
async def geturl1():
    makedUrl, state = makeHtml.oauthMakeLink()

    return {
        "url": makedUrl,
        "confSessionVal": state
    }

# Get Oauth url for tistory
@app.get("/getoauthurl/tistory")
async def geturl2():
    link = makeHtml.oauthMakeLink()
    return {"url": link}

# Oauth redirect url for confluence
# This will return HTML Response and set cookie to client's browser
# You have to setting proxy and make sure front page has same domain with is api server.
@app.get("/oauth/confluence", response_class=HTMLResponse)
def getTokenConfluence(response: Response, code, state: str='sample'):

    authToken = makeHtml.loginProcess(code)
    if (authToken):
        resultString = "Login Success."

        # This action will build at front later.
        response.set_cookie(key="confSESSION", value=state)

        # Set redis later.
        confluenceTokenDict[state] = {
            'state': state,
            'token': authToken,
            #'baseId': '',
            'baseId': '85dd2495-82c7-4a5f-818f-d5b05d30a806', ###debug!!!!!
            'spaceKey': '',
            #'contentId': '',
            'contentId': '14778479', ###debug!!!!!
            'contentResult': ''
        }
    else:
        resultString = "Fail Login."
    
    print (confluenceTokenDict)

    
    # Return page for front
    # This section will build at front later
    returnHtml = """
    <html>
        <script>
            function WinClose(){{window.open('','_self').close();}}
        </script>
        <h1>code : {}</h1>
        <h2>state : {}</h2>
        <a href ="javascript:WinClose();">{} 창을 닫으시오</a>
    </html>
    """.format(code, state ,resultString)
    return returnHtml


@app.get("/oauth/tistory")
async def getTokenTistory(code , state: str=''):
    returnJson = {
        "code": code,
        "state": state
    }
    return returnJson

@app.get("/confluence/getdomains")
async def getdomain(confSession : dict = Depends(getConfluenceToken)):

    domains = makeHtml.getDomain(confSession['token'])
    if (domains):
        return domains
    else:
        raise HTTPException(status_code=500, detail="Can't get domains")

@app.get("/confluence/setsessioninfo")  
async def setbaseid(value, type: str = Query(None, regex="^baseId$|^spaceKey$|^contentId$|^contentName$"), confSESSION: str = Cookie(None)):
    if (confSESSION in confluenceTokenDict):
        confluenceTokenDict[confSESSION][type] = value
        return 'succ'
    else:
        raise HTTPException(status_code=401, detail="Invalid confSESSION Cookie : {}".format(confSESSION))   

@app.get("/confluence/getspaces")
async def getspaces(confSession : dict = Depends(getConfluenceToken)):

    spaces = makeHtml.getSpaceList(confSession['baseId'], confSession['token'])
    if (spaces):
        return spaces
    else:
        raise HTTPException(status_code=500, detail="Can't get spaces")

@app.get("/confluence/getcontentlist")
async def getcontents(confSession : dict = Depends(getConfluenceToken)):

    contentlist = makeHtml.getContentList(confSession['baseId'], confSession['spaceKey'], confSession['token'])
    if (contentlist):
        return contentlist
    else:
        raise HTTPException(status_code=500, detail="Can't get contentlist")

def makehtmlBackgroundJob(baseId, contentId, token, state):
    import base64
    confluenceTokenDict[state]['contentResult'] = 'building'
    content = makeHtml.getContentHtml(baseId, contentId, token)
    encodedContent = base64.b64encode(content.encode('utf-8')).decode('utf-8')
    confluenceTokenDict[state]['contentResult'] = encodedContent
    # try:
    #     confluenceTokenDict[state]['contentResult'] = 'building'
    #     content = makeHtml.getContentHtml(baseId, contentId, token)
    #     encodedContent = base64.b64encode(content.encode('utf-8')).decode('utf-8')
    #     confluenceTokenDict[state]['contentResult'] = encodedContent
    # except Exception as e:
    #     confluenceTokenDict[state]['contentResult'] = 'error'
    #     print (e.__dict__)
    #     print (' ## 에러발생 : {0}'.format(e))

@app.get("/confluence/makecontent")
async def getcontents(background_tasks: BackgroundTasks, confSession : dict = Depends(getConfluenceToken)):
    contents = "making started"
    #contents = makeHtml.getCententHtml(confSession['baseId'], confSession['contentId'], confSession['token'])
    try:
        background_tasks.add_task(makehtmlBackgroundJob, confSession['baseId'], confSession['contentId'], confSession['token'], confSession['state'])
        return contents
    except:
        raise HTTPException(status_code=500, detail="Can't start making content at backend")

@app.get("/confluence/getcontent")
async def getcontents(confSession : dict = Depends(getConfluenceToken)):
    if (confSession['contentResult'] not in ['error','building']):
        result = 'succ'
        result = confSession['contentResult']
    else:
        result = confSession['contentResult']
    return result


    

# long running job example start
"""
def longruntask(times):
    import time
    print ("start longruntask")
    time.sleep(int(times))
    print ("end longruntask")

@app.get("/asynctest")
async def asynctest(background_tasks: BackgroundTasks):
    
    contents = "init"
    print ('befor sleep')
    background_tasks.add_task(longruntask, 6)
    print ('after sleep')
    return contents
"""
# long running job example end

