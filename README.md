# YouTube Video Downloader

A web application that allows you to download YouTube videos in high quality MP4 format.

## Features

- Simple and modern web interface
- High-quality video downloads
- Support for various YouTube video formats
- Easy to use with any YouTube URL

## Requirements

- Python 3.8 or higher
- Virtual environment (recommended)

## Installation

1. Clone this repository:
```bash
git clone <repository-url>
cd youtube-downloader
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On macOS/Linux
```

3. Install the required packages:
```bash
pip install -r requirements.txt
```

## Usage

1. Start the application:
```bash
python main.py
```

2. Open your web browser and navigate to:
```
http://localhost:8000
```

3. Paste a YouTube URL and click "Download Video"

4. Once the download is complete, click the download link to save the video

## Notes

- Downloaded videos are temporarily stored in the `downloads` directory
- The application uses yt-dlp to handle YouTube video downloads
- Videos are downloaded in the best available quality

## License

MIT License 