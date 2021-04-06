import makeHtml
import requests

class Tistory:
    def __init__(self):
        self.defaultParam = {
            'access_token' : '',
            'output' : 'json'
        }
        from secrets import Secret
        self.secret = Secret()
    def getAuthCode(self):
        # this section will remake at frontend. this is poc code
        # change redirectUrl for realservice url later
        authCodeUrl = "https://www.tistory.com/oauth/authorize"
        params = {
            "client_id": self.secret.tistoryAppId,
            "redirect_uri": "http://ykarma1996.tistory.com/",
            "response_type": "code"
        }
        res = requests.get(authCodeUrl, params=params)
        
        # action this url at browser, and get AccessToken manually just now.
        print (res.url)
        
    def getAccessToken(self, authCode="getFromClient"):
        authCode = input("authCode : ") # delete this later
        
        getTokenUrl = "https://www.tistory.com/oauth/access_token"
        params = {
            "client_id": self.secret.tistoryAppId,
            "client_secret": self.secret.tistorySecretKey,
            "redirect_uri": "http://ykarma1996.tistory.com/",
            "code": authCode,
            "grant_type": "authorization_code"
        }
        res  = requests.get(getTokenUrl, params=params)
        self.defaultParam['access_token'] = res.text.split('=')[1]
    
    def getBlogList(self):
        params = self.defaultParam
        getBlogUrl = "https://www.tistory.com/apis/blog/info"
        res = requests.get(getBlogUrl, params=params)
        
        # Object of key: 'blogName' value: 'blogTitle'
        blogList = {}
        for blog in res.json()['tistory']['item']['blogs']:
            blogList[blog['name']] = blog['title']
        
        # Show to FrontEnd
        print (blogList)
        
    def getcatego(self, blogName):
        params = self.defaultParam
        params['blogName'] = blogName
        getcategoUrl = 'https://www.tistory.com/apis/category/list'
        res = requests.get(getcategoUrl, params=params)
        
        # Object of key : 'catego id' value: 'catego name'
        categoList = {}
        for catego in res.json()['tistory']['item']['categories']:
            categoList[catego['id']] = catego['name']
        
        print (categoList)

        
    # upload image and return image's url
    def uploadImg(self, blogName, imgName, imgBin):
        
        params = self.defaultParam
        params['blogName'] = blogName
        files = {'uploadedfile': (imgName, imgBin)}
        imgUpload = "https://www.tistory.com/apis/post/attach"
        res = requests.post(imgUpload, params=params, files=files).json()
        uploadedImg = res['tistory']['replacer'].replace('##_1N', '##_Image')
        print (uploadedImg)
        if (uploadedImg.split('|')[1] == ''):
            # upload to imgbb for take image thumbanil for large image 
            imgbbUrl = "https://api.imgbb.com/1/upload"
            imgbbParam = {'key': self.secret.apiKeyImgbb}
            data = {'image': imgBin}
            imgThumb = requests.post(imgbbUrl, params=imgbbParam, files=data)
            imgThumbUrl = imgThumb.json()['data']['display_url']
            imgBin2 = requests.get(imgThumbUrl).content
            files2 = {'uploadedfile': (imgName+'v2', imgBin2)}
            res2 = requests.post(imgUpload, params=params, files=files2).json()
            uploadedImg = res2['tistory']['replacer'].replace('##_1N', '##_Image')
            
        return uploadedImg
    
    # replace <img> tag for public viwer
    def rebuildImgStore(self, blogName):
        content, headers = makeHtml.main()
        for img in content.findAll('img'):
            imgName = img.attrs['data-linked-resource-default-alias']
            imgSrc = img.attrs['src']
            print (imgName)
            print (imgSrc)
            res = requests.get(imgSrc, headers=headers)
            
            imgUpload = self.uploadImg(blogName, imgName, res.content)
            # replace <img> tag's src and delete not use attrs
            img.attrs = {}
            img.string = imgUpload
            img.unwrap()
        return (str(content))
    
    def postContent(self, blogName, title, visibility, category, tag, acceptComment):
        content = self.rebuildImgStore(blogName)
        params = self.defaultParam
        params['blogName'] = blogName
        params['title'] = title
        params['content'] = content
        params['visibility'] = visibility
        params['category'] = category
        params['tag'] = tag
        params['acceptComment'] = acceptComment
        
        postUrl = 'https://www.tistory.com/apis/post/write'
        res = requests.post(postUrl, data=params)
        
        print (res.json()['tistory']['url'])

def main():
    ti = Tistory()
    ti.getAuthCode()
    ti.getAccessToken()
    ti.getBlogList()
    
    #categoName = intput()
    blogName = 'ykarma1996'
    ti.getcatego(blogName)
    
    title = input('게시물 제목 : ')
    visibility = 0
    category = input('카테고리 : ')
    tag = input('테그 : ')
    acceptComment = 1
    
    ti.postContent(blogName, title, visibility, category, tag, acceptComment)
    
if __name__ == "__main__":
    main()