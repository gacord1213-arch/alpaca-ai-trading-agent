"""
news_data.py — ambil berita terbaru saham dari Alpaca News API.
Dipakai agent untuk analisis sentimen (Claude yang menilai bullish/bearish).
"""
from datetime import datetime, timedelta
from alpaca.data.historical.news import NewsClient
from alpaca.data.requests import NewsRequest
import config

_news = NewsClient(config.API_KEY, config.API_SECRET)


def get_news(symbol: str, limit: int = 5, days_back: int = 5) -> list:
    """Ambil headline berita terbaru untuk 1 simbol (ringkas, siap dinilai LLM)."""
    try:
        req = NewsRequest(
            symbols=symbol,
            start=datetime.now() - timedelta(days=days_back),
            limit=limit,
            include_content=False,
            sort="desc",
        )
        res = _news.get_news(req)
        out = []
        for n in res.data.get("news", []):
            out.append({
                "headline": n.headline,
                "summary": (n.summary or "")[:280],
                "source": n.source,
                "created_at": str(n.created_at)[:10],
            })
        return out
    except Exception as e:
        return [{"error": str(e)}]


if __name__ == "__main__":
    import json
    print(json.dumps(get_news("AAPL"), indent=2, default=str))
