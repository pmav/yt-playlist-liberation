# yt-playlist-liberation

A collection of scripts to download, normalize, and tag MP3 files from YouTube playlists.

## Features

- **Download**: Extract high-quality audio (256K MP3) from YouTube playlists.
- **Normalization**: Batch normalize audio levels using `ffmpeg-normalize`.
- **LLM metadata extraction**: Use a local Ollama model to infer the artist and song title from each MP3 filename and save the results as `metadata.json`.
- **Tagging**: Apply the inferred artist and title values as ID3 tags to matching files.
- **Metadata review**: Read back the stored artist, title, and album tags from MP3 files to verify the results.

## Prerequisites

The workflow expects the following tools and services to be available:

- Python 3
    - mutagen (Install via `pip install mutagen`)
- Docker
- Ollama
- yt-dlp binary at the project root (`./yt-dlp`)

## How to use

1. Edit `config.json` for the playlist and output settings: `playlist` and `download_directory`.

    Example:
    ```json
    "playlist": "<playlist_id>",
    "download_directory": "<output/playlist-name>",
    ```
2. Run the full workflow from the project root:
   ```bash
   ./run-workflow.sh
   ```

## Configuration

The scripts read their shared settings from `config.json`. Update this file before running the workflow to change the playlist, download and normalized directories, metadata filename, download archive, audio settings, normalization workers, or Ollama connection. `CONFIG_FILE` can point to another configuration file when needed.

## Usage

### Run the full workflow in one command
From the project root, you can run the entire pipeline in order:
```bash
./run-workflow.sh
```
This executes the numbered scripts in sequence: download, normalize, metadata extraction, tagging, and final metadata readback.

### 1. Download Playlist
Set the desired playlist and download settings in `config.json`, then run:
```bash
./01_download.sh
```
The script uses `yt-dlp` to download audio from the configured YouTube playlist, convert it to MP3, and embed the available thumbnail. Files are written to `download_directory` and named with the configured output template. The download archive prevents already downloaded entries from being fetched again.

### 2. Normalize Audio
Normalize the downloaded MP3 files:
```bash
./02_normalize.sh
```
The script processes MP3 files from `download_directory` with `ffmpeg-normalize` in Docker. It uses the configured worker count, codec, bitrate, and Docker image, and writes normalized files to `normalized_directory`.

### 3. Extract Metadata
Run `03_get_metadata.py` to generate `metadata.json`:
```bash
./03_get_metadata.py
```
For each MP3 in `normalized_directory` (default: `p3-normalized`), the script asks a local Ollama model to identify the artist and song from the filename. It writes the results, together with the original filenames, to `metadata_file`. Ollama must be running at the configured host, and its model, endpoint, timeout, token limit, and thinking mode are all configurable. `MP3_DIR`, `OLLAMA_HOST`, and `OLLAMA_MODEL` environment variables override the corresponding config values.

### 4. Apply ID3 Tags
Apply the artist and title values from `metadata.json` to matching files:
```bash
./04_add_metadata.py
```
The script matches each JSON record by its exact filename and writes the `artist` and `title` values as ID3 tags to MP3 files in the configured normalized directory. Files without valid matching metadata are skipped.

### 5. Read MP3 Metadata
Display the existing artist, title, and album metadata for MP3 files in a directory:

The script defaults to `download_directory` from `config.json`:
```bash
./05_read_metadata.py
```
The script scans MP3 files in the specified or default directory and displays their metadata (filename, artist, title, and album) in a formatted table. It gracefully handles both single- and multiple-value ID3 frames, extracting the first value when needed.

## File Structure

- `run-workflow.sh`: Run the full workflow end-to-end from the repo root.
- `01_download.sh`: YouTube download script.
- `02_normalize.sh`: Audio normalization script.
- `03_get_metadata.py`: Generate metadata using the filenames and an LLM.
- `04_add_metadata.py`: Apply metadata from `metadata.json` to MP3 files.
- `05_read_metadata.py`: Read and display existing MP3 metadata.
- `config.json`: Shared configuration for scripts 01 through 05.
