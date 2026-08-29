#!/usr/bin/env python3

import json
import os
import sys
from pathlib import Path

from mutagen.id3 import TIT2, TPE1
from mutagen.mp3 import MP3

CONFIG_FILE = Path(os.environ.get("CONFIG_FILE", "config.json"))
CONFIG = json.loads(CONFIG_FILE.read_text(encoding="utf-8"))

DOWNLOAD_DIRECTORY = Path(CONFIG.get("download_directory", "."))
METADATA_FILE = DOWNLOAD_DIRECTORY / "metadata.json"
MP3_DIR = Path(os.environ.get("MP3_DIR", DOWNLOAD_DIRECTORY / "normalized"))


def load_config(config_path):
    with config_path.open(encoding="utf-8") as config_file:
        return json.load(config_file)


def load_metadata(metadata_path):
    with metadata_path.open(encoding="utf-8") as metadata_file:
        records = json.load(metadata_file)

    if not isinstance(records, list):
        raise ValueError("metadata.json must contain a list of records")

    metadata_by_filename = {}
    for record in records:
        if not isinstance(record, dict) or not isinstance(record.get("filename"), str):
            raise ValueError("Each metadata record must contain a filename")

        metadata = record.get("metadata")
        if not isinstance(metadata, dict):
            continue

        artist = metadata.get("artist")
        song = metadata.get("song")
        if isinstance(artist, str) and artist.strip() and isinstance(song, str) and song.strip():
            metadata_by_filename[record["filename"]] = {
                "artist": artist.strip(),
                "title": song.strip(),
            }

    return metadata_by_filename


def add_metadata(file_path, metadata):
    audio = MP3(file_path)
    if audio.tags is None:
        audio.add_tags()

    audio.tags["TPE1"] = TPE1(encoding=3, text=[metadata["artist"]])
    audio.tags["TIT2"] = TIT2(encoding=3, text=[metadata["title"]])
    audio.save()


def main():
    try:
        config = load_config(CONFIG_FILE)
    except (OSError, json.JSONDecodeError) as error:
        print(f"Could not read config: {error}", file=sys.stderr)
        return 1

    if not METADATA_FILE.is_file():
        print(f"Metadata file not found: {METADATA_FILE}", file=sys.stderr)
        return 1
    if not MP3_DIR.is_dir():
        print(f"Directory not found: {MP3_DIR}", file=sys.stderr)
        return 1

    try:
        metadata_by_filename = load_metadata(METADATA_FILE)
    except (OSError, json.JSONDecodeError, ValueError) as error:
        print(f"Could not read metadata: {error}", file=sys.stderr)
        return 1

    mp3_files = sorted(
        file_path for file_path in MP3_DIR.iterdir()
        if file_path.is_file() and file_path.suffix.lower() == ".mp3"
    )
    tagged = 0
    skipped = 0
    failed = 0

    for file_path in mp3_files:
        metadata = metadata_by_filename.get(file_path.name)
        if metadata is None:
            skipped += 1
            print(f"Skipping (no metadata): {file_path.name}")
            continue

        try:
            add_metadata(file_path, metadata)
            tagged += 1
            print(f"Tagged: {file_path.name}\n\t {metadata['artist']} / {metadata['title']}\n")
        except Exception as error:
            failed += 1
            print(f"Failed: {file_path.name}: {error}", file=sys.stderr)

    print(f"Processed: {tagged}, skipped: {skipped}, failed: {failed}")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())