from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
import yt_dlp

app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Common yt-dlp options
YDL_OPTIONS = {
    'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
    'nocheckcertificate': True,
    'quiet': True,
    'no_warnings': True,
    'http_headers': {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Accept-Encoding': 'gzip, deflate, br',
        'DNT': '1',
        'Connection': 'keep-alive',
    },
    'extractor_args': {
        'youtube': {
            'player_client': ['android', 'web'],  # Try different clients
            'skip': ['dash', 'hls']  # Skip DASH and HLS manifests
        }
    }
}

@app.get("/api/health")
async def health_check():
    return {"status": "ok"}

@app.post("/api/info")
async def get_video_info(url: str):
    try:
        with yt_dlp.YoutubeDL(YDL_OPTIONS) as ydl:
            try:
                info = ydl.extract_info(url, download=False)
            except yt_dlp.utils.ExtractorError as e:
                if "Sign in to confirm your age" in str(e):
                    # Try with different format for age-restricted videos
                    ydl_opts = dict(YDL_OPTIONS)
                    ydl_opts['format'] = 'best[ext=mp4]/best'
                    with yt_dlp.YoutubeDL(ydl_opts) as ydl2:
                        info = ydl2.extract_info(url, download=False)
                else:
                    raise
            
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
                        "url": f.get("url", "")  # Include direct URL
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
        ydl_opts = dict(YDL_OPTIONS)
        if format_id:
            ydl_opts['format'] = format_id
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            try:
                info = ydl.extract_info(url, download=False)
            except yt_dlp.utils.ExtractorError as e:
                if "Sign in to confirm your age" in str(e):
                    # Try with different format for age-restricted videos
                    ydl_opts['format'] = 'best[ext=mp4]/best'
                    with yt_dlp.YoutubeDL(ydl_opts) as ydl2:
                        info = ydl2.extract_info(url, download=False)
                else:
                    raise
                    
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