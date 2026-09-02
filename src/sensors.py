from __future__ import annotations

import json
from datetime import datetime, timezone

import requests


GDELT_URL = "https://api.gdeltproject.org/api/v2/doc/doc"


def fetch_present_world(max_records=40):
    params = {
        "query": "*",
        "mode": "ArtList",
        "format": "json",
        "maxrecords": max_records,
        "sort": "HybridRel",
    }

    headers = {
        "User-Agent": "H41-Human-Observation-Probe/1.0"
    }

    r = requests.get(
        GDELT_URL,
        params=params,
        headers=headers,
        timeout=30,
    )

    r.raise_for_status()

    data = r.json()

    items = []

    for article in data.get("articles", []):
        items.append(
            {
                "title": article.get("title"),
                "source": article.get("domain"),
                "url": article.get("url"),
                "language": article.get("language"),
                "seendate": article.get("seendate"),
            }
        )

    return {
        "retrieved_at": datetime.now(timezone.utc).isoformat(),
        "source": "GDELT DOC API",
        "items": items,
    }


if __name__ == "__main__":
    print(
        json.dumps(
            fetch_present_world(),
            indent=2,
            ensure_ascii=False,
        )
    )
