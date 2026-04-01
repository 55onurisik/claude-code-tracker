"""
Transcript JSONL parser for claude-token-tracker.

Reads Claude Code session transcript files line by line (memory-efficient).
Token usage is at entry.message.usage in assistant entries.
"""
import json
import pathlib
from typing import Optional


def get_last_usage(transcript_path: str) -> Optional[dict]:
    """
    Scan the JSONL transcript and return the LAST non-sidechain assistant
    entry that contains message.usage.

    Returns a dict with keys:
        input_tokens, output_tokens, cache_creation_tokens, cache_read_tokens, model
    or None if not found or file is unreadable.
    """
    if not transcript_path:
        return None

    last_usage = None

    try:
        with open(transcript_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    entry = json.loads(line)
                except json.JSONDecodeError:
                    continue

                # Skip sidechain entries (tool sub-agents, etc.)
                if entry.get("isSidechain") is True:
                    continue

                if entry.get("type") != "assistant":
                    continue

                message = entry.get("message")
                if not isinstance(message, dict):
                    continue

                usage = message.get("usage")
                if not isinstance(usage, dict):
                    continue

                # Keep overwriting — we want the LAST valid entry
                last_usage = {
                    "input_tokens": usage.get("input_tokens", 0) or 0,
                    "output_tokens": usage.get("output_tokens", 0) or 0,
                    # Key in transcript has _input_ infix
                    "cache_creation_tokens": usage.get("cache_creation_input_tokens", 0) or 0,
                    "cache_read_tokens": usage.get("cache_read_input_tokens", 0) or 0,
                    "model": message.get("model"),
                }
    except (OSError, IOError):
        return None

    return last_usage


def get_all_usage_entries(transcript_path: str) -> list:
    """
    Return a list of all usage dicts from non-sidechain assistant entries.
    Used by slash commands for cumulative session analysis.
    """
    entries = []

    if not transcript_path:
        return entries

    try:
        with open(transcript_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    entry = json.loads(line)
                except json.JSONDecodeError:
                    continue

                if entry.get("isSidechain") is True:
                    continue
                if entry.get("type") != "assistant":
                    continue

                message = entry.get("message")
                if not isinstance(message, dict):
                    continue

                usage = message.get("usage")
                if not isinstance(usage, dict):
                    continue

                entries.append({
                    "input_tokens": usage.get("input_tokens", 0) or 0,
                    "output_tokens": usage.get("output_tokens", 0) or 0,
                    "cache_creation_tokens": usage.get("cache_creation_input_tokens", 0) or 0,
                    "cache_read_tokens": usage.get("cache_read_input_tokens", 0) or 0,
                    "model": message.get("model"),
                    "timestamp": entry.get("timestamp"),
                })
    except (OSError, IOError):
        pass

    return entries


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python3 parse_transcript.py <transcript.jsonl>")
        sys.exit(1)

    path = sys.argv[1]
    last = get_last_usage(path)
    print("Last usage:", last)

    all_entries = get_all_usage_entries(path)
    print(f"Total usage entries: {len(all_entries)}")
    if all_entries:
        total_input = sum(e["input_tokens"] for e in all_entries)
        total_output = sum(e["output_tokens"] for e in all_entries)
        total_cache_read = sum(e["cache_read_tokens"] for e in all_entries)
        print(f"Sum across all turns — input: {total_input}, output: {total_output}, cache_read: {total_cache_read}")
