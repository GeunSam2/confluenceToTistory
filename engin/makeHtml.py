import base64
import requests
from bs4 import BeautifulSoup as bs
from .tistoryApi import Tistory
from .secrets import Secret 
import json

tistory = Tistory()

class MakeHtml:
    def __init__(self):
        secret = Secret()
        # confluence OAuth AppId and Secrets
        self.confluenceAppId = secret.confluenceAppId
        self.confluenceSecretkey = secret.confluenceSecretkey
        
        # redirectUrl
        self.redirectUrl = 'https://oauth.modutech.win/oauth/confluence'
        
        # imgBB api key
        self.imgApiKey = secret.apiKeyImgbb
        # user's confluence space baseurl
        self.baseUrl = "https://api.atlassian.com/ex/confluence"
        # header for api requests
        self.headers = {"Authorization": "Bearer {token}", 'Accept': 'application/json'}
        # htmlBodySoup
        self.htmlSoup = ""
    
    def generate_random_key(self, length):
        import random
        import string
        return ''.join(random.choice(string.ascii_lowercase + string.digits) for _ in range(length))
    
    def oauthMakeLink(self):

        state = self.generate_random_key(30)
        makeLinkUrl = 'https://auth.atlassian.com/authorize'
        params = {
            'audience': 'api.atlassian.com',
            'client_id': self.confluenceAppId,
            'scope': 'read:confluence-space.summary read:confluence-content.all read:confluence-content.summary read:confluence-props search:confluence read:confluence-content.permission readonly:content.attachment:confluence',
            'redirect_uri': self.redirectUrl,
            'state': state,
            'response_type': 'code',
            'prompt': 'consent'
        }
        makedUrl = requests.Request('GET', makeLinkUrl, params=params).prepare().url
        
        return makedUrl, state
    
    # fill api access information and check api can speak
    def loginProcess(self, authCode):
        getTokenUrl = 'https://auth.atlassian.com/oauth/token'
        headers = self.headers
        headers['Content-Type'] = 'application/json'
        jsonData = {
            'grant_type': 'authorization_code',
            'client_id': self.confluenceAppId,
            'client_secret': self.confluenceSecretkey,
            'code': authCode,
            'redirect_uri': self.redirectUrl
        }
        authRes = requests.post(getTokenUrl, json=jsonData, headers=headers)
        print (authRes.text)
        if (authRes.status_code == 200):
            token = authRes.json()['access_token']
            
            self.headers["Authorization"] = "Bearer {}".format(token)
            print ("Bearer {}".format(token))
            print ('Success to get Token!')
            return "Bearer {}".format(token)
        else:
            print ('Auth Fail!')
            return False
        
    # get domain
    def getDomain(self, token):
        getBaseUrl = 'https://api.atlassian.com/oauth/token/accessible-resources'
        header = self.headers
        header['Authorization'] = token
        getBaseRes = requests.get(getBaseUrl, headers=header)
        if (getBaseRes.status_code == 200):
            print (getBaseRes.json())
#             baseId = getBaseRes.json()[1]['id']
#             self.baseUrl = 'https://api.atlassian.com/ex/confluence/{}'.format(baseId)
            print ("Success get Id of domain!")
            return (getBaseRes.json())
        else:
            print (getBaseRes.status_code)
            return False
        
    # get space list from 
    def getSpaceList(self, baseId, token):
        header = self.headers
        header['Authorization'] = token
        spaceListUrl = "{}/{}/rest/api/space".format(self.baseUrl, baseId)
        res = requests.get(spaceListUrl, headers=header).json()
        
        # spaceListDict {"sample": {"id":1234, "key": "SPACE1", "selfUrl": "https://example.com"}}
        spaces = {}
        for item in res['results']:
            spaces[item['name']] = {}
            spaces[item['name']]['id'] = item['id']
            spaces[item['name']]['key'] = item['key']
        print (spaces)
        return spaces

    def getContentList(self, baseId, spaceKey, token):
        header = self.headers
        header['Authorization'] = token
        params = {"spaceKey": spaceKey}
        contentListUrl = "{}/{}/rest/api/content".format(self.baseUrl, baseId)
        res = requests.get(contentListUrl, params=params, headers=header).json()
        
        # contentListDict {"id(num)": "title"}
        contents = {}
        for item in res['results']:
            contents[item['id']] = item['title']
            
        print (contents)
        return contents
    
    def getContentHtml(self, baseId, contentId, token):
        viewType = "view"
        header = self.headers
        header['Authorization'] = token
        params = {"expand": "body.{}".format(viewType)}
        contentUrl = "{}/{}/rest/api/content/{}".format(self.baseUrl, baseId, contentId)
        res = requests.get(contentUrl, params=params, headers=header).json()
        htmlBody = res['body'][viewType]['value']
        htmlSoup = bs(htmlBody, 'html.parser')
        rebuildedSoup = self.rebuildFormat(htmlSoup)
        #finalSoup = self.rebuildImgStore(baseId, contentId, rebuildedSoup, token)
        return rebuildedSoup

    def unwrapTds(self, soups):
        for item in soups:
            if (item.p):
                item.p.unwrap()   
        
    def rebuildFormat(self, htmlSoup):
        # wrap with single tag
        new_tag = htmlSoup.new_tag('content')
        body_children = list(htmlSoup.children)
        htmlSoup.clear()
        htmlSoup.append(new_tag)
        for child in body_children:
            new_tag.append(child)  
        
        # replace all 'th' tag to 'tr' tag
        for th in htmlSoup.findAll('th'):
            th.name = 'td'
        
        # beautify table view
        for table in htmlSoup.findAll('table'):
            table.attrs['data-ke-style'] = 'style12'

        # beautify table view2
        # delete 'p' tag inside td tag tree
        Tds = htmlSoup.find_all('td', 'confluenceTd')
        Ths = htmlSoup.find_all('td', 'confluenceTh')
        self.unwrapTds(Tds)
        self.unwrapTds(Ths)

           
        # append <code> tag inside <pre> tag for beautify code block
        for pre in htmlSoup.findAll('pre', class_='syntaxhighlighter-pre'):
            newTag = htmlSoup.new_tag('code')
            newTag.string = pre.string
            pre.string = ""
            pre.append(newTag)
        
        return htmlSoup

            
    # upload image to imgbb and return image's url
    def uploadImg(self, imgBin):
        imgUpload = "https://api.imgbb.com/1/upload"
        params = {'key': self.imgApiKey}
        imgBase64 = base64.b64encode(imgBin).decode('ascii')
        data = {'image': imgBase64}
        res = requests.post(imgUpload, params=params, data=data).json()
        return res['data']['url']
        
    # replace <img> tag for public viwer
    def rebuildImgStore(self, baseId, contentId, token, htmlSoup, forTistory = False, tistoryDict = {}):
        conattachsUrltentUrl = "{}/{}/rest/api/content/{}/child/attachment".format(self.baseUrl, baseId, contentId)
        header = self.headers

        # 컨플루언스 api가 oauth 토큰을 지원하지 않아서 임시로 개인 토큰을 사용
        # 21.08.02 해당 api 에러에 대한 패치가 반영되어서 정상동작함
        header['Authorization'] = token
        attachPool = requests.get(conattachsUrltentUrl, headers=header).json()['results']

        for img in htmlSoup.findAll('img'):
            imgId = img.attrs['data-linked-resource-id']
            # imgSubSrc = [item['_links']['download'] for item in attachPool if item['title'] == imgId][0]
            imgSrc = "{}/{}/download".format(conattachsUrltentUrl, imgId)
            res = requests.get(imgSrc, headers=header)
        
            if (forTistory):
                blogName = tistoryDict['tistoryBlogName']
                token = tistoryDict['tistoryToken']
                imgUpload = tistory.uploadImg(blogName, imgId, res.content, token)
                # replace <img> tag's src and delete not use attrs
                img.attrs = {}
                img.string = imgUpload
                img.unwrap()
            else:
                imgUrl = self.uploadImg(res.content)
                # replace <img> tag's src and delete not use attrs
                img.attrs['src'] = imgUrl
                img.attrs['data-image-src'] = ""
                img.attrs['data-base-url'] = ""
        return htmlSoup
    
    def saveHtmlFile(self, fileName, htmlSoup):
        with open("{}.html".format(fileName), "w", -1, "utf-8") as f:
            f.write(str(htmlSoup))

            
def main():
    make1 = MakeHtml()
    link = make1.oauthMakeLink()
    print (link)
    authCode = input('Auth Code : ')
    make1.loginProcess(authCode)
    
    make1.getDomain()
    
    baseId = input ('baseId : ')
    make1.getSpaceList(baseId)

    spaceName = input ('input space key : ')
    lists = make1.getContentList(baseId, spaceName)

    contendId = input('input content ID : ')
    htmlSoup = make1.getCententHtml(baseId, contendId)
    fileName = input('파일명을 입력하세요 : ')
    make1.saveHtmlFile('output1.html')
    return htmlSoup

if __name__ == "__main__":

    main()