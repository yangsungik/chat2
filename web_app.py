import os
from typing import List, Dict

from flask import Flask, render_template, request, jsonify, send_from_directory, session
from dotenv import load_dotenv

from news_chatbot import (
    search_google_news,
    search_naver_news_with_creds,
    simple_summarize,
)


def load_env() -> None:
    load_dotenv()


def build_news_view(keyword: str, limit: int = 10) -> List[Dict]:
    items = search_google_news(keyword, limit=limit)
    view_items: List[Dict] = []

    for i, item in enumerate(items, start=1):
        title_raw = item.get("title", "")
        title = title_raw.replace("<b>", "").replace("</b>", "")
        description = item.get("description", "")
        link = item.get("link", "")

        summary = simple_summarize(title, description)
        view_items.append(
            {
                "index": i,
                "title": title,
                "summary": summary,
                "link": link,
            }
        )

    return view_items


def create_app() -> Flask:
    load_env()
    app = Flask(__name__)
    app.secret_key = os.environ.get("FLASK_SECRET_KEY", "news-chatbot-secret-change-me")

    @app.after_request
    def add_cors(response):
        """다른 출처에서 API 호출 허용. 세션 쿠키는 같은 출처(/news)에서만 사용."""
        response.headers["Access-Control-Allow-Origin"] = "*"
        response.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
        response.headers["Access-Control-Allow-Headers"] = "Content-Type"
        return response

    def _get_naver_creds():
        """환경 변수 우선(Vercel 등), 없으면 세션. API 키는 절대 응답/로그에 포함하지 않음."""
        env_cid = os.environ.get("NAVER_CLIENT_ID", "").strip()
        env_csec = os.environ.get("NAVER_CLIENT_SECRET", "").strip()
        if env_cid and env_csec:
            return env_cid, env_csec
        return session.get("naver_client_id") or "", session.get("naver_client_secret") or ""

    @app.route("/api/naver-keys", methods=["POST", "OPTIONS"])
    def api_naver_keys():
        """네이버 API 키 저장. 환경 변수가 이미 있으면 세션 저장 안 함(유출 방지)."""
        if request.method == "OPTIONS":
            return "", 204
        try:
            if os.environ.get("NAVER_CLIENT_ID") and os.environ.get("NAVER_CLIENT_SECRET"):
                return jsonify({"ok": True, "message": "환경 변수로 설정되어 있습니다. 입력하지 않아도 됩니다."})
            data = request.get_json(force=True, silent=True) or {}
            cid = (data.get("client_id") or "").strip()
            csec = (data.get("client_secret") or "").strip()
            if cid and csec:
                session["naver_client_id"] = cid
                session["naver_client_secret"] = csec
                return jsonify({"ok": True, "message": "저장되었습니다."})
            session.pop("naver_client_id", None)
            session.pop("naver_client_secret", None)
            return jsonify({"ok": True, "message": "키가 삭제되었습니다."})
        except Exception:
            return jsonify({"ok": False, "message": "저장 중 오류가 발생했습니다."}), 400

    @app.route("/api/news", methods=["GET", "OPTIONS"])
    def api_news():
        """뉴스 검색. 환경 변수(NAVER_CLIENT_*) 우선, 없으면 세션. API 키는 응답에 포함하지 않음."""
        if request.method == "OPTIONS":
            return "", 204
        keyword = (request.args.get("keyword") or "").strip()
        if not keyword:
            return jsonify({"error": "키워드를 입력해 주세요.", "items": []}), 400
        try:
            cid, csec = _get_naver_creds()
            if cid and csec:
                items = search_naver_news_with_creds(keyword, 10, cid, csec)
            else:
                items = search_google_news(keyword, limit=10)
            out = []
            for i, item in enumerate(items, start=1):
                title = (item.get("title") or "").replace("<b>", "").replace("</b>", "")
                desc = item.get("description", "")
                link = item.get("link", "")
                summary = simple_summarize(title, desc)
                out.append({"index": i, "title": title, "description": desc, "summary": summary, "link": link})
            return jsonify({"items": out})
        except Exception:
            return jsonify({"error": "뉴스 조회 중 오류가 발생했습니다.", "items": []}), 500

    @app.route("/news")
    def serve_news_html():
        """단일 HTML 페이지 제공. 이 경로로 열면 API 키 없이 검색 가능."""
        return send_from_directory(os.path.dirname(os.path.abspath(__file__)), "news.html")

    @app.route("/", methods=["GET", "POST"])
    def index():
        keyword = ""
        news_items: List[Dict] = []
        error_message = ""

        if request.method == "POST":
            keyword = (request.form.get("keyword") or "").strip()

            if not keyword:
                error_message = "키워드를 입력해 주세요."
            else:
                try:
                    news_items = build_news_view(keyword, limit=10)
                    if not news_items:
                        error_message = "검색 결과가 없습니다."
                except Exception as e:  # noqa: BLE001
                    error_message = f"구글 뉴스 조회 중 오류가 발생했습니다: {e}"

        return render_template(
            "index.html",
            keyword=keyword,
            news_items=news_items,
            error_message=error_message,
        )

    return app


app = create_app()


if __name__ == "__main__":
    port = int(os.getenv("PORT", "5000"))
    app.run(host="0.0.0.0", port=port, debug=True)

