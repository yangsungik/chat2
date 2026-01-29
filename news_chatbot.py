import os
import re
import sys
import textwrap
from typing import List, Dict, Optional
from urllib.parse import quote

import feedparser
import requests
from dotenv import load_dotenv


NAVER_NEWS_SEARCH_URL = "https://openapi.naver.com/v1/search/news.json"
GOOGLE_NEWS_RSS_URL = "https://news.google.com/rss/search"
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)


def load_env() -> None:
    """
    Load environment variables from a .env file if present.
    Expected variables:
      - NAVER_CLIENT_ID
      - NAVER_CLIENT_SECRET
    """
    load_dotenv()


def get_naver_credentials() -> Dict[str, str]:
    client_id = os.getenv("NAVER_CLIENT_ID")
    client_secret = os.getenv("NAVER_CLIENT_SECRET")

    if not client_id or not client_secret:
        print(
            "\n[오류] NAVER_CLIENT_ID 또는 NAVER_CLIENT_SECRET 환경 변수가 설정되지 않았습니다.\n"
            ".env 파일 또는 시스템 환경 변수에 다음 값을 설정해 주세요:\n"
            "  NAVER_CLIENT_ID=발급받은_클라이언트_ID\n"
            "  NAVER_CLIENT_SECRET=발급받은_클라이언트_SECRET\n"
        )
        sys.exit(1)

    return {"client_id": client_id, "client_secret": client_secret}


def _strip_html(text: str) -> str:
    """Remove HTML tags from text."""
    if not text:
        return ""
    return re.sub(r"<[^>]+>", " ", text)


def _parse_google_feed(raw: bytes):
    return feedparser.parse(raw)


def search_google_news(keyword: str, limit: int = 10) -> List[Dict]:
    """
    구글 뉴스 RSS를 사용해 뉴스 검색 결과를 가져옵니다.
    기사는 최대 limit개(기본 10개)까지 반환합니다.
    """
    url = f"{GOOGLE_NEWS_RSS_URL}?q={quote(keyword)}&hl=ko&gl=KR&ceid=KR:ko"
    request_headers = {"User-Agent": USER_AGENT}
    feed = None

    try:
        feed = feedparser.parse(url, request_headers=request_headers)
    except Exception:
        pass

    if not feed or not getattr(feed, "entries", None):
        try:
            resp = requests.get(url, headers=request_headers, timeout=15)
            if resp.status_code == 200:
                feed = _parse_google_feed(resp.content)
        except Exception:
            pass

    feed = feed or object()
    entries = getattr(feed, "entries", []) or []
    items: List[Dict] = []
    for entry in entries:
        if len(items) >= limit:
            break
        title = (entry.get("title") or "").strip()
        link = (entry.get("link") or "").strip()
        raw = entry.get("summary") or entry.get("description") or ""
        description = " ".join(_strip_html(str(raw)).split())
        if not title and not link:
            continue
        items.append({"title": title, "description": description, "link": link})

    return items


def search_naver_news(keyword: str, display: int = 10) -> List[Dict]:
    """
    Naver 검색 API를 사용해 뉴스 검색 결과를 가져옵니다.
    (환경 변수 NAVER_CLIENT_ID / NAVER_CLIENT_SECRET 사용)
    """
    creds = get_naver_credentials()
    return search_naver_news_with_creds(
        keyword, display, creds["client_id"], creds["client_secret"]
    )


def search_naver_news_with_creds(
    keyword: str,
    display: int = 10,
    client_id: Optional[str] = None,
    client_secret: Optional[str] = None,
) -> List[Dict]:
    """
    Naver 검색 API를 사용해 뉴스 검색 결과를 가져옵니다.
    client_id, client_secret 이 있으면 사용하고, 없으면 빈 목록을 반환합니다.
    """
    if not client_id or not client_secret:
        return []

    headers = {
        "X-Naver-Client-Id": client_id,
        "X-Naver-Client-Secret": client_secret,
    }
    params = {
        "query": keyword,
        "display": display,
        "sort": "date",
    }
    try:
        resp = requests.get(
            NAVER_NEWS_SEARCH_URL, headers=headers, params=params, timeout=10
        )
        if resp.status_code != 200:
            return []
        data = resp.json()
        return data.get("items", [])
    except Exception:
        return []


def simple_summarize(title: str, description: str, max_len: int = 120) -> str:
    """
    매우 단순한 요약 함수.
    - 설명의 첫 문장 또는 앞부분을 잘라 간단 요약 형태로 반환합니다.
    - 필요하다면 이 부분을 ChatGPT/OpenAI API 등으로 교체할 수 있습니다.
    """
    text = description or ""
    # Naver 응답에는 HTML 태그나 특수문자가 섞여 있을 수 있음
    for tag in ("<b>", "</b>", "&quot;", "&apos;", "&lt;", "&gt;", "&amp;"):
        text = text.replace(tag, " ")

    text = " ".join(text.split())  # 공백 정리

    if not text:
        return title

    if "。" in text:
        first_sentence = text.split("。")[0]
    elif "." in text:
        first_sentence = text.split(".")[0]
    else:
        first_sentence = text

    summary = first_sentence.strip()
    if len(summary) > max_len:
        summary = summary[: max_len - 1].rstrip() + "…"

    return summary


def format_news_item(idx: int, item: Dict) -> str:
    title = (item.get("title") or "").replace("<b>", "").replace("</b>", "")
    description = item.get("description") or ""
    link = item.get("link") or ""

    summary = simple_summarize(title, description)

    wrapped_summary = textwrap.fill(summary, width=80)
    formatted = f"[{idx}] {title}\n{wrapped_summary}\n링크: {link}"
    return formatted


def chat_loop() -> None:
    """
    간단한 콘솔 기반 챗봇 루프.
    """
    print("=== 구글 뉴스 요약 챗봇 ===")
    print("키워드를 입력하면 구글 뉴스에서 관련 기사 10개를 찾아 간단히 요약해 드립니다.")
    print("종료하려면 'q' 또는 'quit'를 입력하세요.\n")

    while True:
        try:
            keyword = input("검색 키워드 입력 > ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n종료합니다.")
            break

        if not keyword:
            print("키워드를 입력해 주세요.\n")
            continue

        if keyword.lower() in {"q", "quit", "exit"}:
            print("종료합니다.")
            break

        print(f"\n'{keyword}' 관련 구글 뉴스 10건 검색 중...\n")
        items = search_google_news(keyword, limit=10)

        if not items:
            print("검색 결과가 없습니다.\n")
            continue

        for i, item in enumerate(items, start=1):
            print(format_news_item(i, item))
            print("-" * 80)

        print()  # 한 줄 공백


if __name__ == "__main__":
    load_env()
    chat_loop()

