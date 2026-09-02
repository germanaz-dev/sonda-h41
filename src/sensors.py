from __future__ import annotations

import json
from datetime import datetime, timezone

import feedparser
import requests


FEEDS = [
    {
        "name": "BBC World",
        "url": "https://feeds.bbci.co.uk/news/world/rss.xml",
    },
    {
        "name": "NPR World",
        "url": "https://feeds.npr.org/1004/rss.xml",
    },
    {
        "name": "ScienceDaily",
        "url": "https://www.sciencedaily.com/rss/top/science.xml",
    },
    {
        "name": "MIT Technology Review",
        "url": "https://www.technologyreview.com/feed/",
    },
]


HEADERS = {
    "User-Agent": "H41-Human-Observation-Probe/1.0"
}


def fetch_feed(name, url, max_items=12):
    try:
        r = requests.get(
            url,
            headers=HEADERS,
            timeout=15,
        )
        r.raise_for_status()

        parsed = feedparser.parse(r.content)

        items = []

        for entry in parsed.entries[:max_items]:
            items.append(
                {
                    "source": name,
                    "title": entry.get("title", ""),
                    "url": entry.get("link", ""),
                    "summary": entry.get("summary", "")[:1200],
                    "published": entry.get("published", ""),
                }
            )

        return {
            "source": name,
            "status": "ok",
            "items": items,
        }

    except Exception as exc:
        return {
            "source": name,
            "status": "failed",
            "error": str(exc),
            "items": [],
        }


def fetch_present_world():
    sources = []
    all_items = []

    for feed in FEEDS:
        result = fetch_feed(
            feed["name"],
            feed["url"],
        )

        sources.append(
            {
                "source": result["source"],
                "status": result["status"],
                "error": result.get("error"),
            }
        )

        all_items.extend(result["items"])

    return {
        "retrieved_at": datetime.now(
            timezone.utc
        ).isoformat(),
        "sources": sources,
        "items": all_items,
    }


if __name__ == "__main__":
    print(
        json.dumps(
            fetch_present_world(),
            indent=2,
            ensure_ascii=False,
        )
    )
