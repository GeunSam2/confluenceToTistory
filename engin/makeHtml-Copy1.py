import base64
import requests
from bs4 import BeautifulSoup as bs
from .secrets import Secret 
import json

class MakeHtml:
    def __init__(self):
        secret = Secret()
        # confluence OAuth AppId and Secrets
        self.confluenceAppId = secret.confluenceAppId
        self.confluenceSecretkey = secret.confluenceSecretkey
        
        # redirectUrl
        self.redirectUrl = 'https://mc.modutech.win:11996/oauth/confluence'
        
        # imgBB api key
        self.imgApiKey = secret.apiKeyImgbb
        # user's confluence space baseurl
        self.baseUrl = "https://api.atlassian.com/ex/confluence/"
        # header for api requests
        self.headers = {"Authorization": "Bearer {token}", 'Accept': 'application/json'}
        # htmlBodySoup
        self.htmlSoup = ""
    
    def oauthMakeLink(self):
        import random
        import string

        def generate_random_key(length):
            return ''.join(random.choice(string.ascii_lowercase + string.digits) for _ in range(length))
        
        state = generate_random_key(30)
        makeLinkUrl = 'https://auth.atlassian.com/authorize'
        params = {
            'audience': 'api.atlassian.com',
            'client_id': self.confluenceAppId,
            'scope': 'read:confluence-space.summary read:confluence-content.all read:confluence-content.summary read:confluence-props search:confluence',
            'redirect_uri': self.redirectUrl,
            'state': state,
            'response_type': 'code',
            'prompt': 'consent'
        }
        url = requests.Request('GET', makeLinkUrl, params=params).prepare().url
        returnJson = {
            "url": url,
            "state": state
        }
        return returnJson
    
    # fill api access information and check api can speak
    def loginProcess(self, authCode):
        getTokenUrl = 'https://auth.atlassian.com/oauth/token'
        headers = self.headers
        headers['Content-Type'] = 'application/json'
        data = {
            'grant_type': 'authorization_code',
            'client_id': self.confluenceAppId,
            'client_secret': self.confluenceSecretkey,
            'code': authCode,
            'redirect_uri': self.redirectUrl
        }
        authRes = requests.post(getTokenUrl, data=json.dumps(data), headers=headers)
        if (authRes.status_code == 200):
            token = authRes.json()['access_token']
            print ('Success to get Token!')
            print ("Tobe : Bearer {}".format(token))
            return "Bearer {}".format(token)
        else:
            print ('Auth Fail!')
            return False
        
        
        #self.headers["Authorization"] = "Bearer {}".format(token)
        
    def selectSpace(self, token):
        getBaseUrl = 'https://api.atlassian.com/oauth/token/accessible-resources'
        getBaseRes = requests.get(getBaseUrl, headers=self.headers)
        if (getBaseRes.status_code == 200):
            baseId = getBaseRes.json()
            print ("Success get Id of domain!")
            print (baseId)
            return baseId
            
            #self.baseUrl = 'https://api.atlassian.com/ex/confluence/{}'.format(baseId)
        else:
            
            print (getBaseRes.status_code)
            return False
        
#         # check api
#         testUrl = "{}/rest/api/space".format(self.baseUrl)
#         print (testUrl)
#         testRes = requests.get(getBaseUrl, headers=self.headers)
#         if (testRes.status_code == 200):
#             print ('Success login!')
#         else:
#             print (testRes.status_code)
#             return False
        
        
    
    # get space list from 
    def getSpaceList(self):
        spaceListUrl = "{}/rest/api/space".format(self.baseUrl)
        res = requests.get(spaceListUrl, headers=self.headers).json()
        
        # spaceListDict {"sample": {"id":1234, "key": "SPACE1", "selfUrl": "https://example.com"}}
        spaces = {}
        for item in res['results']:
            spaces[item['name']] = {}
            spaces[item['name']]['id'] = item['id']
            spaces[item['name']]['key'] = item['key']
        print (spaces)
        return spaces

    def getContentList(self, spaceKey):
        params = {"spaceKey": spaceKey}
        contentListUrl = "{}/rest/api/content".format(self.baseUrl)
        res = requests.get(contentListUrl, params=params, headers=self.headers).json()
        
        # contentListDict {"id(num)": "title"}
        contents = {}
        for item in res['results']:
            contents[item['id']] = item['title']
            
        print (contents)
        return contents
    
    def getCententHtml(self, contentId):
        viewType = "view"
        params = {"expand": "body.{}".format(viewType)}
        contentUrl = "{}/rest/api/content/{}".format(self.baseUrl, contentId)
        res = requests.get(contentUrl, params=params, headers=self.headers).json()
        htmlBody = res['body'][viewType]['value']
        self.htmlSoup = bs(htmlBody, 'html.parser')
        self.rebuildFormat()
        self.rebuildImgStore()
        return self.htmlSoup
        
        
    def rebuildFormat(self):
        # wrap with single tag
        new_tag = self.htmlSoup.new_tag('content')
        body_children = list(self.htmlSoup.children)
        self.htmlSoup.clear()
        self.htmlSoup.append(new_tag)
        for child in body_children:
            new_tag.append(child)  
        
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
        params = {'key': self.imgApiKey}
        imgBase64 = base64.b64encode(imgBin).decode('ascii')
        data = {'image': imgBase64}
        res = requests.post(imgUpload, params=params, data=data).json()
        return res['data']['url']
        
    # replace <img> tag for public viwer
    def rebuildImgStore(self):
        for img in self.htmlSoup.findAll('img'):
            imgSrc = img.attrs['src']
            res = requests.get(imgSrc, headers=self.headers)
            
            imgUrl = self.uploadImg(res.content)
            # replace <img> tag's src and delete not use attrs
            img.attrs['src'] = imgUrl
            img.attrs['data-image-src'] = ""
            img.attrs['data-base-url'] = ""
        print (self.htmlSoup)
    
#     def saveHtmlFile(self, fileName):
#         with open("{}.html".format(fileName), "w", -1, "utf-8") as f:
#             f.write(str(self.htmlSoup))

            
def main():
    make1 = MakeHtml()
    make1.oauthMakeLink()
    authCode = input('Auth Code : ')
    make1.loginProcess(authCode)
    make1.getSpaceList()

    spaceName = input ('input space key : ')
    lists = make1.getContentList(spaceName)

    contendId = input('input content ID : ')
    htmlSoup = make1.getCententHtml(contendId)
    return htmlSoup

if __name__ == "__main__":
    main()
