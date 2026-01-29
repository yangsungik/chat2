# 구글 뉴스 요약 챗봇

키워드를 입력하면 **구글 뉴스 RSS**로 관련 뉴스 10건을 검색하고,  
간단한 요약(제목 + 설명 기반)을 보여주는 **콘솔/웹용 챗봇**입니다.

## 1. 준비물

- Python 3.9 이상

## 2. 의존성 설치

프로젝트 루트(이 폴더)에서:

```bash
pip install -r requirements.txt
```

`requests`, `flask`, `python-dotenv`, `feedparser` 등이 설치됩니다.

## 3. 환경 변수 — API 키 유출 방지

- **로컬**: 프로젝트 루트에 `.env` 파일을 만들고 넣을 수 있습니다. **`.env`는 `.gitignore`에 포함되어 있으므로 Git에 커밋되지 않습니다.**
- **Vercel 배포**: API 키는 **코드/클라이언트에 넣지 말고**, Vercel 대시보드에서만 설정하세요.
  1. Vercel 프로젝트 → **Settings** → **Environment Variables**
  2. 다음 변수 추가 (Production / Preview / Development 원하는 것 선택):
     - `NAVER_CLIENT_ID` = 네이버 개발자 센터에서 발급한 Client ID
     - `NAVER_CLIENT_SECRET` = 네이버 Client Secret
  3. 저장 후 **재배포**하면 적용됩니다.

서버는 **환경 변수를 우선** 사용합니다. Vercel에 위 변수를 설정해 두면, 웹에서 API 키를 입력할 필요가 없고 키가 클라이언트로 전달되지 않습니다.

## 4. 콘솔 버전 실행 방법

```bash
python news_chatbot.py
```

프롬프트에 검색 **키워드**를 입력하면, 구글 뉴스에서 관련 기사 10건을 가져와 요약해서 보여줍니다.

- 종료: `q`, `quit`, `exit` 중 하나 입력

## 5. 웹 버전 실행 방법

```bash
python web_app.py
```

브라우저에서 `http://127.0.0.1:5000` 에 접속한 뒤, 키워드를 입력하면 구글 뉴스 10건 요약을 볼 수 있습니다. **HTML로 저장** 버튼으로 결과를 HTML 파일로 내려받을 수 있습니다.

## 6. 검색이 안 될 때

- `pip install -r requirements.txt` 로 **feedparser** 포함 의존성을 모두 설치했는지 확인하세요.
- 인터넷 연결을 확인하고, 방화벽/프록시에서 `news.google.com` 접속이 막히지 않는지 봅니다.
- 여전히 결과가 없으면 `python scripts/test_search.py` 또는 `python scripts/test_search.py 인공지능` 로 검색 동작을 확인해 보세요.

## 7. 요약 로직 변경(선택 사항)

현재 요약은 뉴스 설명의 첫 문장을 잘라내어 최대 길이만 제한하는 **아주 단순한 규칙 기반 요약**입니다.  
`news_chatbot.py` 안의 `simple_summarize` 함수를 수정해서,  
OpenAI API 등 외부 LLM을 이용한 고급 요약 기능으로 교체할 수 있습니다.

