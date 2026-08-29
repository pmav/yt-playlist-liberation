#!/usr/bin/env sh

CONFIG_FILE="${CONFIG_FILE:-config.json}"

eval "$(python3 - "$CONFIG_FILE" <<'PY'
import json
import shlex
import sys

with open(sys.argv[1], encoding="utf-8") as config_file:
    config = json.load(config_file)

normalize = config["normalize"]
values = {
    "DOWNLOAD_DIRECTORY": config["download_directory"],
    "N_JOBS": normalize["workers"],
    "AUDIO_CODEC": normalize["audio_codec"],
    "AUDIO_BITRATE": normalize["audio_bitrate"],
    "DOCKER_IMAGE": normalize["docker_image"],
}
for name, value in values.items():
    print(f"{name}={shlex.quote(str(value))}")
PY
)"

INPUT_DIRECTORY="$DOWNLOAD_DIRECTORY/raw"
OUTPUT_DIRECTORY="$DOWNLOAD_DIRECTORY/normalized"

mkdir -p "$OUTPUT_DIRECTORY"

echo "Normalizing files in ${INPUT_DIRECTORY} using ${N_JOBS} parallel workers..."

find "$INPUT_DIRECTORY" -maxdepth 1 -type f -iname '*.mp3' -print0 | xargs -0 -P "$N_JOBS" -I {} docker run \
    --rm \
    --volume "$PWD":/tmp \
    --user "$(id -u):$(id -g)" \
    "$DOCKER_IMAGE" "/tmp/{}" \
        -f \
        --extension mp3 \
        --audio-codec "$AUDIO_CODEC" \
        --audio-bitrate "$AUDIO_BITRATE" \
        --output-folder "/tmp/$OUTPUT_DIRECTORY" \
        --progress
