#!/usr/bin/env python3

import os
import csv
import json
import sys
from pathlib import Path
from mutagen.mp3 import MP3

CONFIG_FILE = Path(os.environ.get('CONFIG_FILE', 'config.json'))
try:
    with CONFIG_FILE.open(encoding='utf-8') as config_file:
        CONFIG = json.load(config_file)
except (OSError, json.JSONDecodeError):
    CONFIG = {}

DEFAULT_DIRECTORY = Path(CONFIG.get('download_directory', '.')) / 'normalized'


def tag_text(tag, default=''):
    """Return the first text value from a Mutagen ID3 tag frame."""
    if tag is None:
        return default

    values = getattr(tag, 'text', tag)
    if isinstance(values, (list, tuple)):
        values = values[0] if values else default

    return str(values).strip('"').strip("'").strip()

def get_mp3_metadata(file_path):
    """Extract metadata from an MP3 file."""
    try:
        audio = MP3(file_path)

        # Try to get ID3 tags first (TPE1=Artist, TIT2=Title)
        if hasattr(audio, 'tags') and audio.tags:
            artist = audio.tags.get('TPE1', 'Unknown Artist')
            title = audio.tags.get('TIT2', 'Unknown Title')
            album = audio.tags.get('TALB', '')

            return {
                'file': Path(file_path).name,
                'artist': tag_text(artist, 'Unknown Artist'),
                'title': tag_text(title, 'Unknown Title'),
                'album': tag_text(album)
            }

        # If no ID3 tags, try to get metadata from file info
        if audio:
            return {
                'file': Path(file_path).name,
                'artist': 'Unknown Artist',
                'title': 'Unknown Title',
                'album': ''
            }

    except Exception as e:
        print(f"  ⚠ Error reading {Path(file_path).name}: {str(e)}")
        return {
            'file': Path(file_path).name,
            'artist': 'Unknown Artist',
            'title': 'Unknown Title',
            'album': ''
        }

def scan_directory(directory):
    """Scan directory for all MP3 files."""
    directory = Path(directory)

    if not directory.exists():
        print(f"❌ Directory does not exist: {directory}")
        return []

    print(f"🔍 Scanning directory: {directory}")

    mp3_files = list(directory.glob("*.mp3")) + list(directory.rglob("*.MP3"))

    if not mp3_files:
        print(f"⚠ No MP3 files found in {directory}")
        return []

    return sorted(mp3_files, key=lambda x: x.name)

def display_results(mp3_files):
    """Display all results and save to CSV."""
    if not mp3_files:
        return

    # Print header
    print(f"\n{'File Name':<120} {'Artist':<25} {'Title':<30}")

    for file_path in mp3_files:
        if file_path.exists():
            metadata = get_mp3_metadata(file_path)
            print(f"{metadata['file']:<120} | {metadata['artist'][:25]:<25} | {metadata['title'][:30]}",
                  end='\n')

def main():
    directory = Path(os.environ.get('MP3_DIR', DEFAULT_DIRECTORY))
    if len(sys.argv) > 1:
        directory = Path(sys.argv[1])

    mp3_files = scan_directory(directory)

    if mp3_files:
        display_results(mp3_files)

        # Summary
        print(f"\n✅ Total MP3 files scanned: {len(mp3_files)}")
    else:
        print("⚠ No results to display.")

if __name__ == "__main__":
    main()