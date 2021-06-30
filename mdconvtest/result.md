* * *

### 이슈개요

  * tistory api를 활용하여 게시물 포스팅

tistory에서는 굉장히 개발자 친화적인 [api 문서](https://tistory.github.io/document-tistory-
apis/)를 제공 하고 있었다. ~~(내가 꼬인건지 모르겠지만, 외국 솔루션의 Document 들은 괜히 공식 문서랍시고 설명들을 쓸데없이
어렵게 써놓고 개발자들이 이것 저것 찾아봐야하게 문서를 써놓는 것 같다)~~ < \- 지금 다시 읽어보니 이때 왜 이렇게 화가 나있지..

티스토리의 Open Api는 api사용시 인증방식을 OAuth2.0을 활용하도록 만들어 그 기능을 제공하고 있다. 나중에 사용자들에게
서비스를 제공할 것을 생각해 보니 컨플루언서의 API 인증방식도 가능하다면 OAuth2.0을 활요하면 좋지 않을까 생각하고 찾아보니 해당
인증방식을 지원하고 있었다. 그래서 인증 방식을 모두 OAuth 방식을 활용할 수 있도록 변경하기로 하였다.

## 티스토리 OpenAPI 활용하여 게시물 포스팅 하기

### Tistory Open API 앱 등록

티스토리의 Open API를 사용하기 위해서는 앱 등록을 통해서, 제작할 서비스에 대한 내용을 간단하게 등록하고 `client_id` 라는
것을 발급 받아야 한다. Open API를 활용할 시, OAuth 인증 진행 초반 부터 이 값이 없다면 API를 사용할 수 없다.

앱 등록시 입력하는 `CallBack` 항목에는 이후 서비스될 어플리케이션의 인증 API서버 주소를 써주어, 인증 후에 토큰값을 리다이렉트
하여 받을 수 있도록 한다. 아직 개발을 진행하는 단계라서 주소가 없는 경우에는 임의의 동작하는 주소를 작성하여도 추후에 앱 관리에서 수정할
수 있으니 걱정하지 않고 발급하여도 된다.

  * 티스토리 Open API 앱 등록 페이지 : <https://www.tistory.com/guide/api/manage/register>

![](https://i.ibb.co/98dxTWB/f60733a6fe9f.png)

앱 등록이 완료되면, `App ID` 와 `Secret Key` 를 발급해주는데, 이후 Open Api 활용시 사용되는 값이니 잘 기억해
두도록 한다. (이후 앱 관리 화면에서 다시 확인할 수 있다.)

![](https://i.ibb.co/FhmBK9r/a72acaf801bc.png)

### OAuth2.0 으로 인증받기

OAuth2.0의 간단한 동작 방식은 다음과 같다.

![](https://i.ibb.co/VNCZ468/200cd47d04b0.png)

  1. API를 활용할 서비스(우리가 개발할 서비스)에서 특정 서비스의 사용자 인증이 필요한 경우

  2. 인증이 필요한 서비스(tistory)에 대해서 로그인 팝업등을 띄워주면 사용자가 직접 로그인 하고

  3. 로그인이 성공할 경우 인증이 필요한 서비스(tistory)에서 API를 활용할 서비스(우리가 개발할 서비스)로 인증코드를 발행하여 사전에 등록한 주소(e.g. 개발할 서비스의 백앤드)로 전달한다.

  4. API를 활용할 서비스는 받은 인증코드를 활용하여 인증이 필요한 서비스로부터 적절한 권한이 반영된 토큰을 발행받아 사용할 수 있다.

아직 프론트를 개발하지 않은 상태에서 인증과정을 테스트하기 위해 작성한 POC는 다음과 같았다.

    
    
    import requests
    
    class Tistory:
        def __init__(self):
            pass
        def getAuthCode(self):
            # this section will remake at frontend. this is poc code
            # change redirectUrl for realservice url later
            authCodeUrl = "https://www.tistory.com/oauth/authorize"
            params = {
                "client_id": "앱 등록시 받은 App ID",
                "redirect_uri": "앱 등록시 등록한 CallBack",
                "response_type": "code"
            }
            res = requests.get(authCodeUrl, params=params)
            
            # action this url at browser, and get AccessToken manually just now.
            print ("브라우저에 주소 호출하여 로그인 : {}".format(res.url))
            
        def getAccessToken(self, authCode="getFromClient"):
            authCode = input("authCode : ") # delete this later
            
            getTokenUrl = "https://www.tistory.com/oauth/access_token"
            params = {
                "client_id": "앱 등록시 받은 App ID",
                "client_secret": "앱 등록시 받은 Secret Key",
                "redirect_uri": "앱 등록시 등록한 CallBack",
                "code": authCode,
                "grant_type": "authorization_code"
            }
            res  = requests.get(getTokenUrl, params=params)
            print (res.text)
    
    
    def main():
        ti = Tistory()
        ti.getAuthCode()
        ti.getAccessToken()
        
    if __name__ == "__main__":
        main()

`getAuthCode` 는 사용자가 로그인 할때 접속해야 하는 페이지의 URL을 리턴하는 함수인데, 원래는 프론트가 개발이 되었다면 로그인
팝업을 띄우는 기능에 속하는 기능이다. 현재는 프론트가 없는 상태라, 해당 함수가 리턴해주는 URL을 브라우저에 직접 입력하여 로그인 과정을
거쳐야 한다.

유의할 점은 `redirect_uri` 부분인데, 앱 등록시 등록한 CallBack URL을 입력해야 한다. 로그인에 성공할 경우

    
    
    http://client.redirect.uri?code=authorizationCode

와 같은 형태로 인증코드를 파라미터로 하여 호출되기 때문에 보통은 개발하는 서버에 관련 로직을 넣고, 리스닝 주소를 따로 뽑아서 작성하는
것이 맞다. 하지만 역시 지금은 테스트 환경이기 떄문에, 간단히 동작하는 아무 주소나 앱 등록시 작성하고 호출시에도 해당 주소로 리다이렉트
하도록 하였다. 나는 나의 블로그 주소를 사용하였다. (<http://ykarma1996.tistory.com)>

![](https://i.ibb.co/JcTZLSy/7faadbdba92e.png)

리다이렉트 된 페이지에서 코드를 확인하면, `getAccessToken` 함수가 요구하는 입력값에 해당 인증코드를 입력하면 발행되는 토큰을
확인할 수 있다.

### 페이지 생성하기

  * 블로그 목록 확인

**구분** |  **정보** |  **비고**  
---|---|---  
API 경로  |  `https://www.tistory.com/apis/blog/info` |  
매서드  |  GET  |  
Query 파라미터1  |  access_token  |  값 : OAuth로 발행받은 토큰  
Query 파라미터2  |  output  |  값: json (xml or json 가능)  
호출 목적  |  blogId 확인  |  
  
  * 카테고리 목록 확인

**구분** |  **정보** |  **비고**  
---|---|---  
API 경로  |  `https://www.tistory.com/apis/category/list` |  
매서드  |  GET  |  
Query 파라미터1  |  access_token  |  값 : OAuth로 발행받은 토큰  
Query 파라미터2  |  output  |  값: json (xml or json 가능)  
Query 파라미터3  |  blogName  |  값: 블로그목록 api의 blogId  
호출 목적  |  카테고리 id 확인  |  
  
  * 글작성

티스토리 공식 문서에는 쿼리파라미터로만 안내가 되어 있는데, form data로 전송해도 정상동작하였다. 쿼리파라미터로 본문을 넘기면..
`414 Request-URI Too Long` 에러가 뜬다. 지원하는 파라미터가 많아서 개발에 사용한 파라미터만 정리한다. 자세한 내용은
[공식 문서](https://tistory.github.io/document-tistory-
apis/apis/v1/post/write.html)를 참고하자

**구분** |  **정보** |  **비고**  
---|---|---  
API 경로  |  `https://www.tistory.com/apis/post/write` |  
매서드  |  POST  |  
Form Data 1  |  access_token  |  값 : OAuth로 발행받은 토큰  
Form Data 2  |  output  |  값: json (xml or json 가능)  
Form Data 3  |  blogName  |  값: 블로그목록 api의 blogId  
Form Data 4  |  title  |  값: 글 제목(string)  
Form Data 5  |  content  |  값: 본문 내용(string)  
Form Data 6  |  visibility  |  값: (0: 비공개 - 기본값, 1: 보호, 3: 발행)  
Form Data 7  |  category  |  값: 카테고리 아이디  
Form Data 8  |  tag  |  값: 태그(','로 공백없이 구분한 string)  
Form Data 9  |  acceptCommnet  |  값: 댓글 허용 (0, 1 - 기본값)  
호출 목적  |  글 작성  |  
  
글 작성을 할때 html 문서를 일반 스트링으로 넘기면 제대로 해석하지 못하고 그냥 문자열로 내용이 저장될까봐 걱정했는데, 다행히 적절하게
해석되어 바로 원하는 형태로 보여졌다.

