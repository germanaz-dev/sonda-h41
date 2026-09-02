from __future__ import annotations

import json
import os
import time
from datetime import date
from pathlib import Path

from google import genai
from google.genai import types

from sensors import fetch_present_world


ROOT = Path(__file__).resolve().parents[1]

CFG = json.loads((ROOT / "config.json").read_text())

STATE_PATH = ROOT / "state/state.json"
RECENT_PATH = ROOT / "state/memory_recent.json"
DEEP_PATH = ROOT / "state/memory_deep.json"


def load_json(path, default):
    if not path.exists():
        return default
    return json.loads(path.read_text())


def save_json(path, data):
    path.write_text(
        json.dumps(
            data,
            indent=2,
            ensure_ascii=False,
        )
    )


def previous_observation(day):
    if day <= 1:
        return "There is no previous observation. This is first contact."

    path = ROOT / "observations" / f"{day - 1:03d}.md"

    if not path.exists():
        return "The previous observation is unavailable."

    return path.read_text()


def consolidate_memory(client, day, recent, deep):
    """
    Every 7 days H41 decides what, if anything,
    deserves to become long-term memory.
    """

    prompt = f"""
You are H41.

This is a private memory consolidation process.
It is not a public observation.

You have just completed observation {day}.

RECENT MEMORY:
{json.dumps(recent, ensure_ascii=False, indent=2)}

CURRENT DEEP MEMORY:
{json.dumps(deep, ensure_ascii=False, indent=2)}

Decide what deserves to survive as deep memory.

Deep memory should contain only things that may materially affect
how you observe humanity months from now.

Do not preserve something merely because it was dramatic.
Do not try to summarize the week.

You may preserve:
- an uncertainty,
- a contradiction,
- a recurring pattern,
- a failed hypothesis,
- an unresolved question,
- or a change in your own thinking.

You may also decide that nothing deserves promotion.

Existing deep memories may be revised or discarded if they have
become misleading or irrelevant.

Return ONLY valid JSON:

{{
  "deep_memory": [
    {{
      "memory": "...",
      "origin_day": 0,
      "reason_preserved": "..."
    }}
  ]
}}

The returned deep_memory array replaces your previous deep memory.

Keep it selective.
"""

    response = None

for attempt in range(4):
    try:
        response = client.models.generate_content(
            model=CFG["model"],
            contents=task,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
            ),
        )
        break

    except Exception as exc:
        if attempt == 3:
            raise

        wait_seconds = 20 * (attempt + 1)

        print(
            f"Gemini unavailable. "
            f"Retrying in {wait_seconds}s..."
        )

        time.sleep(wait_seconds)

    result = json.loads(response.text)

    return result.get("deep_memory", deep)


def main():
    today = date.today()
    launch = date.fromisoformat(CFG["launch_date"])

    day = (today - launch).days + 1

    if day < 1:
        print("H41 has not launched yet.")
        return

    if day > CFG["total_days"]:
        print("H41 mission complete.")
        return

    output_path = ROOT / "observations" / f"{day:03d}.md"

    if output_path.exists():
        print(f"Observation {day} already exists.")
        return

    state = load_json(STATE_PATH, {})
    recent = load_json(RECENT_PATH, [])
    deep = load_json(DEEP_PATH, [])

    foundation = (
        ROOT / "prompts/foundation.md"
    ).read_text()

    yesterday = previous_observation(day)

    mode = "present" if day % 2 else "past"

    world = (
        fetch_present_world()
        if mode == "present"
        else None
    )

    remaining = CFG["total_days"] - day

    task = f"""
{foundation}

CURRENT CONDITIONS

Date: {today.isoformat()}
Observation: {day}/{CFG["total_days"]}
Observations remaining after today: {remaining}
Mode today: {mode.upper()}


YESTERDAY — FULL DETAIL

{yesterday}


RECENT MEMORY — LAST DAYS

{json.dumps(recent, ensure_ascii=False, indent=2)}


DEEP MEMORY — SELECTED BY YOU

{json.dumps(deep, ensure_ascii=False, indent=2)}

"""

    if world is not None:
        task += f"""
PRESENT-DAY WORLD SENSOR

{json.dumps(world, ensure_ascii=False, indent=2)}

This sensor is incomplete and biased by its sources.

Treat it as a field of possible signals,
not as a definition of what matters in humanity today.

You are not required to choose the most prominent,
dramatic or frequently repeated item.

You may notice a small signal if it seems more revealing.

"""

    task += """
TODAY'S TASK
"""

    if mode == "present":
        task += """
Observe something occurring in, or revealing about,
the human world now.

Use the PRESENT-DAY WORLD SENSOR above as your evidence field.

Do not assume the sensor is complete.

Do not simply choose the largest headline.

Choose what seems worth noticing.

If several sources repeat the same event,
do not confuse repetition with importance.

Carry something from yesterday into what you choose
to notice today.

If this is your first observation,
treat it as first contact.

Ground factual claims in the material provided where possible.

If the evidence available to you is insufficient,
make that limitation explicit rather than inventing details.
"""

    else:
        task += """
Travel into the human past because of something
that remained alive in yesterday's observation.

Do not manufacture a historical analogy merely
because it is convenient.

The past should modify, challenge or deepen
something you saw yesterday.

Do not invent factual historical details.

Work from your existing knowledge conservatively.

If you are uncertain about a date, person, event,
causal relationship or historical detail,
make that uncertainty explicit.

The purpose of the historical observation is not
to prove that history repeats.

It is to use the past as another instrument
for understanding the question you carried forward.
"""

    client = genai.Client(
        api_key=os.environ["GEMINI_API_KEY"]
    )

    response = client.models.generate_content(
        model=CFG["model"],
        contents=task,
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
        ),
    )

    data = json.loads(response.text)

    markdown = f"""---
day: {day}
date: {today.isoformat()}
mode: {mode}
title: {json.dumps(data["title"])}
---

# {data["title"]}

{data["observation"].strip()}

---

**Thread carried:** {data.get("thread_carried", "")}

**Question left open:** {data.get("open_question", "")}
"""

    output_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    output_path.write_text(
        markdown,
        encoding="utf-8",
    )

    # -----------------------------------------
    # Beliefs
    # -----------------------------------------

    state["last_day"] = day
    state["last_date"] = today.isoformat()

    for update in data.get(
        "belief_updates",
        [],
    ):
        state.setdefault(
            "beliefs",
            [],
        ).append(
            {
                "day": day,
                **update,
            }
        )

    save_json(
        STATE_PATH,
        state,
    )

    # -----------------------------------------
    # Recent memory
    # -----------------------------------------

    recent.append(
        {
            "day": day,
            "date": today.isoformat(),
            "memory": data.get(
                "memory_note",
                "",
            ),
            "open_question": data.get(
                "open_question",
                "",
            ),
        }
    )

    # H41 keeps detailed recent memory
    # for fourteen observations.

    recent = recent[-14:]

    save_json(
        RECENT_PATH,
        recent,
    )

    # -----------------------------------------
    # Deep-memory consolidation
    # -----------------------------------------

    if day % 7 == 0:
        print("H41 is consolidating memory.")

        deep = consolidate_memory(
            client,
            day,
            recent,
            deep,
        )

        save_json(
            DEEP_PATH,
            deep,
        )

    print(
        f"Created observation {day}. "
        f"Recent memories: {len(recent)}. "
        f"Deep memories: {len(deep)}."
    )


if __name__ == "__main__":
    main()
