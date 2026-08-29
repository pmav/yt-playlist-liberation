#!/usr/bin/env bash
set -euo pipefail

repo_root="$(CDPATH= cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
cd "$repo_root"

if [[ -n "${CONFIG_FILE:-}" ]]; then
  case "$CONFIG_FILE" in
    /*) ;; 
    *) CONFIG_FILE="$repo_root/$CONFIG_FILE" ;;
  esac
else
  CONFIG_FILE="$repo_root/config.json"
fi

export CONFIG_FILE

for script in \
  ./01_download.sh \
  ./02_normalize.sh \
  ./03_get_metadata.py \
  ./04_add_metadata.py \
  ./05_read_metadata.py
 do
  if [[ ! -f "$script" ]]; then
    echo "Missing script: $script" >&2
    exit 1
  fi
done

if [[ ! -f "./yt-dlp" ]]; then
  echo "Missing yt-dlp in the repo root: $repo_root/yt-dlp" >&2
  exit 1
fi

if [[ ! -x "./yt-dlp" ]]; then
  chmod +x "./yt-dlp"
fi

python3 - "$CONFIG_FILE" <<'PY'
import json
import os
import sys
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError

config_path = sys.argv[1]
with open(config_path, encoding='utf-8') as fh:
    config = json.load(fh)

host = os.environ.get('OLLAMA_HOST', config['metadata']['ollama_host'])
endpoint = os.environ.get('OLLAMA_ENDPOINT', config['metadata']['ollama_endpoint'])
url = f"{host}{endpoint}"
model = os.environ.get('OLLAMA_MODEL', config['metadata']['ollama_model'])
think = os.environ.get('OLLAMA_THINK', str(config['metadata']['think'])).strip().lower()
think = think in {'1', 'true', 'yes', 'on'}
payload = {
    'model': model,
    'prompt': 'ping',
    'stream': False,
    'think': think,
    'max_tokens': 8,
}

try:
    req = Request(
        url,
        data=json.dumps(payload).encode('utf-8'),
        headers={'Content-Type': 'application/json'},
        method='POST',
    )
    with urlopen(req, timeout=10) as response:
        if response.status >= 400:
            raise RuntimeError(f"Ollama responded with status {response.status}")
except (URLError, HTTPError, TimeoutError, OSError, RuntimeError) as exc:
    print(f"Ollama is not ready: {exc}", file=sys.stderr)
    sys.exit(1)
PY

./01_download.sh
./02_normalize.sh
python3 ./03_get_metadata.py
python3 ./04_add_metadata.py
python3 ./05_read_metadata.py
