from fastapi import Depends, FastAPI, Response, Cookie, HTTPException, Query, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer
from fastapi.responses import HTMLResponse
from .makeHtml import MakeHtml
from .tistoryApi import Tistory
import html2text
import base64

app = FastAPI()

origins = ['*']

# Base64 Function
def base64encode(content):
    return base64.b64encode(content.encode('utf-8')).decode('utf-8')
def base64decode(base64content):
    return base64.b64decode(base64content.encode('utf-8')).decode('utf-8')

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
userSessionDict = {}

# Get MakeHtml.py Class.
makeHtml = MakeHtml()
tistory = Tistory()

# Depends for some api have to check cookies for confluence
def getConfluenceToken(confSESSION: str = Cookie(None)):
    if (confSESSION in userSessionDict):
        return userSessionDict[confSESSION]
    else:
        raise HTTPException(status_code=401, detail="Invalid confSESSION Cookie : {}".format(confSESSION))

def getTistoryToken(confSession: dict = Depends(getConfluenceToken)):
    if (confSession['tistoryToken'] != ''):
        return confSession
    else:
        raise HTTPException(status_code=401, detail="You didn't tistory login yet")

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
async def geturl2(confSession : dict = Depends(getConfluenceToken)):
    link = tistory.oauthMakeLink(confSession['state'])
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
        userSessionDict[state] = {
            'state': state,
            'token': authToken,
            #'baseId': '',
            'baseId': '85dd2495-82c7-4a5f-818f-d5b05d30a806', ###debug!!!!!
            'spaceKey': '',
            #'contentId': '',
            'contentId': '14778479', ###debug!!!!!
            'contentResult': '',
            'tistoryToken': '',
            'tistoryBlogName': 'ykarma1996',
            'tistoryCategory': '512221'
        }
    else:
        resultString = "Fail Login."
    
    print (userSessionDict)    
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
    tToken = tistory.getAccessToken(code)
    if (tToken):
        userSessionDict[state]['tistoryToken'] = tToken
    else:
        tToken = "Something wrong"
        raise HTTPException(status_code=401, detail="Something Wrong with tistory authentication")
    returnJson = {
        "code": code,
        "state": state,
        "token": tToken
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
async def setSessionInfo(value, type: str = Query(None, regex="^baseId$|^spaceKey$|^contentId$|^contentName$|^tistoryBlogName$|^tistoryCategory$"), confSESSION: str = Cookie(None)):
    if (confSESSION in userSessionDict):
        userSessionDict[confSESSION][type] = value
        return 'succ'
    else:
        raise HTTPException(status_code=401, detail="Invalid confSESSION Cookie : {}".format(confSESSION))   

@app.get("/confluence/getspaces")
async def getSpaces(confSession : dict = Depends(getConfluenceToken)):

    spaces = makeHtml.getSpaceList(confSession['baseId'], confSession['token'])
    if (spaces):
        return spaces
    else:
        raise HTTPException(status_code=500, detail="Can't get spaces")

@app.get("/confluence/getcontentlist")
async def getContentList(confSession : dict = Depends(getConfluenceToken)):

    contentlist = makeHtml.getContentList(confSession['baseId'], confSession['spaceKey'], confSession['token'])
    if (contentlist):
        return contentlist
    else:
        raise HTTPException(status_code=500, detail="Can't get contentlist")

def makehtmlBackgroundJob(baseId, contentId, token, state, allSessionInfo, uploadTistory=False):
    try:
        userSessionDict[state]['contentResult'] = 'building'
        content = makeHtml.getContentHtml(baseId, contentId, token)
        convcontent = makeHtml.rebuildImgStore(baseId, contentId, token, content, uploadTistory, allSessionInfo)
        userSessionDict[state]['contentResult'] = content
    except Exception as e:
        userSessionDict[state]['contentResult'] = 'error'
        print (' ## 에러발생 : {0}'.format(e))

@app.get("/confluence/makecontent")
async def makeContent(fortistory : int, background_tasks: BackgroundTasks, confSession : dict = Depends(getConfluenceToken)):
    try:
        if (confSession['contentResult'] not in ['building']):
            if (fortistory == 1): uploadTistory = True
            else : uploadTistory = False
            background_tasks.add_task(makehtmlBackgroundJob, confSession['baseId'], confSession['contentId'], confSession['token'], confSession['state'], confSession, uploadTistory)
            return "making started"
        else:
            return "already building"
    except:
        raise HTTPException(status_code=500, detail="Can't start making content at backend")

def convContentByMd(html):
    md = html2text.html2text(html)
    with open ('../result.md', 'w') as f:
        f.write(md)
    return md

def convContentByPdf(html):
    pdf = html2text.html2text(html)
    return pdf

@app.get("/confluence/getcontent")
async def getContent(type: str = Query(None, regex="^md$|^pdf$|^html$"), confSession : dict = Depends(getConfluenceToken)):
    if (confSession['contentResult'] not in ['error','building','']):
        if (type == 'html'): 
            result = str(confSession['contentResult'])
        elif (type == 'md'): 
            result = convContentByMd(str(confSession['contentResult']))
        elif (type == 'pdf'): 
            result = convContentByMd(str(confSession['contentResult']))
    else:
        result = confSession['contentResult']
    return result
    
@app.get("/tistory/getblogs")
async def getBlogs(tistorySession : dict = Depends(getTistoryToken)):
    blogList = tistory.getBlogList(tistorySession['tistoryToken'])
    return blogList

@app.get("/tistory/getcategory")
async def getCategory(tistorySession : dict = Depends(getTistoryToken)):
    categorys = tistory.getcatego(tistorySession['tistoryBlogName'], tistorySession['tistoryToken'])
    return categorys

@app.get("/tistory/postcontent")
async def postContent(title, visibility : int = 1, tag : str = '', acceptComment : int = 1, tistorySession : dict = Depends(getTistoryToken)):
    if (tistorySession['contentResult'] not in ['error','building','']):
        postedUrl = tistory.postContent(str(tistorySession['contentResult']), tistorySession['tistoryBlogName'], title, visibility, tistorySession['tistoryCategory'], tag, acceptComment, tistorySession['tistoryToken'])
    return postedUrl

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

