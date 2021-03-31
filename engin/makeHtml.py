import base64
import requests
from bs4 import BeautifulSoup as bs


class MakeHtml:
    def __init__(self):
        # imgBB api key
        imgApiKey = ""
        # user's confluence space baseurl
        self.baseUrl = "https://{userSpaceName}.atlassian.net/wiki"
        # header for api requests
        self.headers = {"Authorization": "Basic {token}"}
        # spaceListDict {"sample": {"id":1234, "key": "SPACE1", "selfUrl": "https://example.com"}}
        self.spaces ={}
        # contentListDict {"id(num)": "title"}
        self.contents = {}
        # htmlBodySoup
        self.htmlSoup = ""
    
    # send restapi requests to confluencer
    def sendRequest(self, url, method, paramDic={}, dataDic={}):
        if (method == "GET"):
            res = requests.get(url, params=paramDic, data=dataDic, headers=self.headers, allow_redirects=True)
        elif (method == "POST"):
            res = requests.post(url, params=paramDic, data=dataDic, headers=self.headers, allow_redirects=True)
        else :
            res = False
        return res
    
    # fill api access information and check api can speak
    def loginProcess(self, email, apiKey, userName, imgApiKey):
        # make token with user's email and api key
        secretText = "{}:{}".format(email, apiKey)
        token = base64.b64encode(secretText.encode('ascii')).decode('ascii')
        self.headers["Authorization"] = "Basic {}".format(token)
        self.imgApiKey = imgApiKey
        # make api url with fill username
        self.baseUrl = "https://{}.atlassian.net/wiki".format(userName)
        # check api
        testUrl = "{}/rest/api/space".format(self.baseUrl)
        res = self.sendRequest(testUrl, "GET")
        return res.status_code
    
    # get space list from 
    def getSpaceList(self):
        spaceListUrl = "{}/rest/api/space".format(self.baseUrl)
        res = self.sendRequest(spaceListUrl, "GET").json()
        for item in res['results']:
            self.spaces[item['name']] = {}
            self.spaces[item['name']]['id'] = item['id']
            self.spaces[item['name']]['key'] = item['key']
            self.spaces[item['name']]['self'] = item['_links']['self']
        return self.spaces

    def getContentList(self, spaceKey):
        params = {"spaceKey": spaceKey}
        contentListUrl = "{}/rest/api/content".format(self.baseUrl)
        res = self.sendRequest(contentListUrl, "GET", params).json()
        for item in res['results']:
            self.contents[item['id']] = item['title']
        return self.contents
    
    def getCententHtml(self, contentId):
        viewType = "view"
        params = {"expand": "body.{}".format(viewType)}
        contentUrl = "{}/rest/api/content/{}".format(self.baseUrl, contentId)
        res = self.sendRequest(contentUrl, "GET", params).json()
        htmlBody = res['body'][viewType]['value']
        self.htmlSoup = bs(htmlBody, 'html.parser')
        print (self.htmlSoup)
        
    def rebuildFormat(self):
        # replace all 'th' tag to 'tr' tag
        for th in self.htmlSoup.findAll('th'):
            th.name = 'td'
        
        # beautify table view
        for table in self.htmlSoup.findAll('table'):
            table.attrs['data-ke-style'] = 'style12'
           
        # append <code> tag inside <pre> tag for beautify code block
        for pre in self.htmlSoup.findAll('pre', class_='syntaxhighlighter-pre'):
            newTag = self.htmlSoup.new_tag('code')
            newTag.string = pre.string
            pre.string = ""
            pre.append(newTag)

            
    # upload image to imgbb and return image's url
    def uploadImg(self, imgBin):
        imgUpload = "https://api.imgbb.com/1/upload"
        param = {'key': self.imgApiKey}
        imgBase64 = base64.b64encode(imgBin).decode('ascii')
        data = {'image': imgBase64}
        res = self.sendRequest(imgUpload, "POST", param, data).json()
        return res['data']['url']
        
    # replace <img> tag for public viwer
    def rebuildImgStore(self):
        for img in self.htmlSoup.findAll('img'):
            imgSrc = img.attrs['src']
            res = self.sendRequest(imgSrc, "GET")
            imgUrl = self.uploadImg(res.content)
            # replace <img> tag's src and delete not use attrs
            img.attrs['src'] = imgUrl
            img.attrs['data-image-src'] = ""
            img.attrs['data-base-url'] = ""
    
    def saveHtmlFile(self, fileName):
        with open("{}.html".format(fileName), "w", -1, "utf-8") as f:
            f.write(str(self.htmlSoup))
        
