from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
import yt_dlp
import random
import os
import json
from pathlib import Path

app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create cookies directory if it doesn't exist
cookies_dir = Path("cookies")
cookies_dir.mkdir(exist_ok=True)

# Save a cookies file with common YouTube cookies
COOKIES_FILE = cookies_dir / "youtube.com_cookies.txt"
if not COOKIES_FILE.exists():
    with open(COOKIES_FILE, "w") as f:
        f.write("""# Netscape HTTP Cookie File
.youtube.com	TRUE	/	TRUE	1735689600	CONSENT	YES+cb
.youtube.com	TRUE	/	TRUE	1735689600	VISITOR_INFO1_LIVE	random_string
.youtube.com	TRUE	/	TRUE	1735689600	GPS	1""")

# List of free proxy servers (you should replace these with your own proxy service)
PROXY_LIST = [
    "socks5://127.0.0.1:9050",  # Tor proxy if available
    None  # Direct connection as fallback
]

# Common yt-dlp options
def get_ydl_opts(proxy=None):
    opts = {
        'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
        'nocheckcertificate': True,
        'quiet': True,
        'no_warnings': True,
        'cookiefile': str(COOKIES_FILE),
        'http_headers': {
            'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 17_3_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.3.1 Mobile/15E148 Safari/604.1',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'DNT': '1',
            'Connection': 'keep-alive',
        },
        'extractor_args': {
            'youtube': {
                'player_client': ['ios', 'android'],  # Use mobile clients
                'skip': ['dash', 'hls']
            }
        }
    }
    
    if proxy:
        opts['proxy'] = proxy
    
    return opts

async def extract_info_with_fallback(url: str, download=False):
    last_error = None
    
    # Try with different proxies
    for proxy in PROXY_LIST:
        try:
            ydl_opts = get_ydl_opts(proxy)
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                return ydl.extract_info(url, download=download)
        except Exception as e:
            last_error = e
            continue
    
    # If all proxies failed, try with mobile format
    try:
        ydl_opts = get_ydl_opts(None)
        ydl_opts['format'] = 'best[ext=mp4]/best'  # Simpler format for mobile
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            return ydl.extract_info(url, download=download)
    except Exception as e:
        last_error = e
    
    raise last_error

@app.get("/api/health")
async def health_check():
    return {"status": "ok"}

@app.post("/api/info")
async def get_video_info(url: str):
    try:
        info = await extract_info_with_fallback(url, download=False)
        
        return {
            "success": True,
            "title": info.get('title'),
            "duration": info.get('duration'),
            "thumbnail": info.get('thumbnail'),
            "formats": [
                {
                    "format_id": f["format_id"],
                    "ext": f["ext"],
                    "resolution": f.get("resolution", "N/A"),
                    "filesize": f.get("filesize", 0),
                    "format_note": f.get("format_note", ""),
                    "url": f.get("url", "")
                }
                for f in info["formats"]
                if f.get("ext") == "mp4" and f.get("vcodec") != "none"
            ]
        }
            
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/download")
async def download_video(url: str, format_id: str = None):
    try:
        ydl_opts = get_ydl_opts(random.choice(PROXY_LIST))
        if format_id:
            ydl_opts['format'] = format_id
        
        info = await extract_info_with_fallback(url, download=False)
        title = info.get('title', 'video')
        
        # Get the download URL
        formats = info.get('formats', [])
        download_url = None
        
        if format_id:
            for f in formats:
                if f.get('format_id') == format_id:
                    download_url = f.get('url')
                    break
        else:
            # Get the best quality format URL
            for f in reversed(formats):
                if f.get('ext') == 'mp4' and f.get('vcodec') != 'none':
                    download_url = f.get('url')
                    break
        
        if not download_url:
            raise HTTPException(status_code=400, detail="No suitable format found")
        
        return {
            "success": True,
            "title": title,
            "download_url": download_url
        }
            
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e)) 