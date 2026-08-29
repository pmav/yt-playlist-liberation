#!/usr/bin/env sh

CONFIG_FILE="${CONFIG_FILE:-config.json}"

eval "$(python3 - "$CONFIG_FILE" <<'PY'
import json
import shlex
import sys

with open(sys.argv[1], encoding="utf-8") as config_file:
    config = json.load(config_file)

download = config["download"]
values = {
    "PLAYLIST": config["playlist"],
    "DOWNLOAD_DIRECTORY": config["download_directory"],
    "AUDIO_QUALITY": download["audio_quality"],
    "AUDIO_FORMAT": download["audio_format"],
    "OUTPUT_TEMPLATE": download["output_template"],
	"EMBED_THUMBNAIL": download["embed_thumbnail"],
}
for name, value in values.items():
    print(f"{name}={shlex.quote(str(value))}")
PY
)"

DOWNLOAD_DIRECTORY="$DOWNLOAD_DIRECTORY/raw"
mkdir -p "$DOWNLOAD_DIRECTORY"

DOWNLOAD_ARCHIVE="cache.txt"
THUMBNAIL_OPTION=""
if [ "$EMBED_THUMBNAIL" = "True" ]; then
	THUMBNAIL_OPTION="--embed-thumbnail"
fi

./yt-dlp \
	--verbose \
	--ignore-errors \
	--extract-audio \
	--audio-quality "$AUDIO_QUALITY" \
	--audio-format "$AUDIO_FORMAT" \
	$THUMBNAIL_OPTION \
	--output "$DOWNLOAD_DIRECTORY/$OUTPUT_TEMPLATE" \
	--download-archive "$DOWNLOAD_DIRECTORY/$DOWNLOAD_ARCHIVE" "$PLAYLIST"
