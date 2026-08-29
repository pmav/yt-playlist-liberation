#!/usr/bin/env python3

import os
import sys
import json
import re
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError


CONFIG_FILE = "config.json"
with open(CONFIG_FILE, 'r', encoding='utf-8') as config_file:
    CONFIG = json.load(config_file)

MP3_DIR = CONFIG['download_directory'] + "/normalized"
METADATA_FILE = CONFIG['download_directory'] + "/metadata.json"

HOST = CONFIG['metadata']['ollama_host']
MODEL = CONFIG['metadata']['ollama_model']
ENDPOINT = f"{HOST}{CONFIG['metadata']['ollama_endpoint']}"
REQUEST_TIMEOUT = CONFIG['metadata']['request_timeout']
MAX_TOKENS = CONFIG['metadata']['max_tokens']
THINK = CONFIG['metadata']['think']


def extract_text(obj):
    """Recursively extract any text fields from a parsed JSON object."""
    if obj is None:
        return None
    if isinstance(obj, str):
        return obj
    if isinstance(obj, list):
        parts = [p for item in obj for p in [extract_text(item)] if p]
        return "\n".join(parts) if parts else None
    if isinstance(obj, dict):
        # Common Ollama shapes
        # 1) {'response': {...}}
        if 'response' in obj:
            return extract_text(obj['response'])
        # 2) {'content': [...]}
        if 'content' in obj:
            return extract_text(obj['content'])
        # 3) choices/message/content/text patterns
        if 'choices' in obj:
            return extract_text(obj['choices'])
        if 'message' in obj:
            return extract_text(obj['message'])
        if 'text' in obj and isinstance(obj['text'], str):
            return obj['text']
        if 'output' in obj:
            return extract_text(obj['output'])
        # deeper walk: try all values
        for v in obj.values():
            txt = extract_text(v)
            if txt:
                return txt
    return None


def send_request(prompt, timeout=REQUEST_TIMEOUT):
    payload = {
        "model": MODEL,
        "prompt": prompt,
        "max_tokens": MAX_TOKENS,
        "think": THINK
    }

    data = json.dumps(payload).encode("utf-8")
    req = Request(ENDPOINT, data=data, headers={"Content-Type": "application/json"})

    try:
        with urlopen(req, timeout=timeout) as resp:
            body = resp.read().decode("utf-8")

            # Response may be NDJSON (newline-delimited JSON). Try each line.
            parts = []
            for line in body.splitlines():
                line = line.strip()
                if not line:
                    continue
                try:
                    parsed = json.loads(line)
                except Exception:
                    # not JSON, skip
                    continue
                txt = extract_text(parsed)
                if txt:
                    parts.append(txt)

            # If we found text in NDJSON lines, join parts in order and return.
            if parts:
                return ''.join(parts)
            else:
                # Try parsing whole body as JSON
                try:
                    parsed = json.loads(body)
                    txt = extract_text(parsed)
                    if txt:
                        return txt
                    else:
                        # Fallback: return raw body
                        return body
                except Exception:
                    # Not JSON at all: return raw body
                    return body

    except HTTPError as e:
        print(f"HTTP error {e.code}: {e.reason}", file=sys.stderr)
        try:
            print(e.read().decode(), file=sys.stderr)
        except Exception:
            pass
        return None
    except URLError as e:
        print(f"Connection error: {e.reason}", file=sys.stderr)
        return None


if __name__ == '__main__':
    try:
        files = sorted([f for f in os.listdir(MP3_DIR) if f.lower().endswith('.mp3')])
    except FileNotFoundError:
        print(f"Directory not found: {MP3_DIR}", file=sys.stderr)
        sys.exit(1)

    if not files:
        print(f"No mp3 files found in {MP3_DIR}", file=sys.stderr)
        sys.exit(1)

    final_json = []
    for filename in files:
        # Strip extension and leading three-digit track prefix like "063 - "
        base = os.path.splitext(filename)[0]
        clean_name = re.sub(r'^\s*\d{3}\s*[-–—:]\s*', '', base)

        prompt = (
            f"Extract artist and song from: {clean_name}. Return JSON with keys 'artist' and 'song'. Use null for missing values. "
            "Output raw JSON only."
        )

        print("#" * 120)
        print(f"File: {clean_name}")

        result = send_request(prompt)

        if result is None:
            print("<error>")
        else:
            print(result)

        final_json.append({
            "filename": filename,
            "metadata": json.loads(result) if result else None
        })

    # Write json to file
    with open(METADATA_FILE, "w", encoding="utf-8") as f:
        json.dump(final_json, f, indent=4)
