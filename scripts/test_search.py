"""키워드 검색 동작 확인용 스크립트. `python scripts/test_search.py` 또는 `python -m scripts.test_search` 로 실행."""
import sys
from pathlib import Path

# 프로젝트 루트를 path에 추가
root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(root))

from news_chatbot import search_google_news

if __name__ == "__main__":
    keyword = sys.argv[1] if len(sys.argv) > 1 else "AI"
    limit = 3
    print(f"검색 키워드: {keyword} (최대 {limit}건)")
    print("-" * 50)
    items = search_google_news(keyword, limit=limit)
    print(f"결과: {len(items)}건")
    for i, x in enumerate(items, 1):
        title = (x.get("title") or "")[:60]
        print(f"  {i}. {title}")
    if not items:
        print("검색 결과가 없습니다. pip install -r requirements.txt 및 네트워크 연결을 확인하세요.")
