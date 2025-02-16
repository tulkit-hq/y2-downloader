from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
import yt_dlp
import os
import json
from pathlib import Path
import tempfile

# Create necessary directories
downloads_dir = Path("downloads")
downloads_dir.mkdir(exist_ok=True)

app = FastAPI(
    title="YouTube Downloader",
    docs_url=None,  # Disable docs in production
    redoc_url=None  # Disable redoc in production
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Update this with your frontend domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# Add proxy middleware configuration
app.root_path = "/api/v1"  # If you want to serve the API under /api/v1/

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/api/info")
async def get_video_info(url: str):
    try:
        ydl_opts = {
            'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
            'nocheckcertificate': True,
            'quiet': True,
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            
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
                        "format_note": f.get("format_note", "")
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
        ydl_opts = {
            'format': format_id if format_id else 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
            'nocheckcertificate': True,
            'quiet': True,
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
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

# For Vercel serverless deployment
app = app

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        proxy_headers=True,
        forwarded_allow_ips="*"
    ) 