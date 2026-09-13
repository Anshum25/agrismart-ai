"""
Build the offline advice packs served by the PWA: frontend/public/offline/advice_<lang>.json

  English is written straight from the curated knowledge base (no API key needed):
      python scripts/generate_offline_advice.py --langs en

  Other languages are translated/adapted with Groq (needs GROQ_API_KEY in .env):
      python scripts/generate_offline_advice.py --langs hi mr ta te kn bn gu pa

Existing entries are kept, so the script can be re-run to resume after rate limits.
Have a native speaker spot-check each language before a public launch.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from bonus.assistant import OFFLINE_DIR, groq_client, kb_advice, llm_advice, load_kb  # noqa: E402
from bonus.languages import LANGUAGES  # noqa: E402


def write_pack(lang: str, advice: dict, source: str) -> Path:
    OFFLINE_DIR.mkdir(parents=True, exist_ok=True)
    path = OFFLINE_DIR / f"advice_{lang}.json"
    payload = {
        "lang": lang,
        "source": source,
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "advice": advice,
    }
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=1), encoding="utf-8")
    return path


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--langs", nargs="+", default=["en"], choices=list(LANGUAGES))
    parser.add_argument("--delay", type=float, default=2.0, help="Seconds between LLM calls (rate limits)")
    args = parser.parse_args()

    labels = sorted(load_kb())
    for lang in args.langs:
        if lang == "en":
            path = write_pack("en", {label: kb_advice(label) for label in labels}, "knowledge_base")
            print(f"[en] {len(labels)} entries -> {path}")
            continue

        client = groq_client()
        if client is None:
            print(f"[{lang}] skipped: set GROQ_API_KEY in .env")
            continue
        path = OFFLINE_DIR / f"advice_{lang}.json"
        existing = json.loads(path.read_text(encoding="utf-8")).get("advice", {}) if path.exists() else {}
        for i, label in enumerate(labels, 1):
            if label in existing:
                continue
            result = llm_advice(label, lang, client=client)
            if result is None:
                print(f"[{lang}] {label}: failed (will retry on next run)")
            else:
                existing[label] = result
                write_pack(lang, existing, "ai_generated")
                print(f"[{lang}] {i}/{len(labels)} {label}")
            time.sleep(args.delay)
        print(f"[{lang}] {len(existing)}/{len(labels)} entries -> {path}")


if __name__ == "__main__":
    main()
