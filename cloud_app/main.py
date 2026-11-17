import os
import re
from datetime import datetime, timezone
from fastapi import FastAPI, Header, HTTPException
import instaloader

app = FastAPI(title="Instagram Public Posts Analyzer")

@app.get("/health")
def health():
    return {"status": "ok"}

@app.get("/posts/{username}")
def posts(username: str, limit: int = 20, x_access_token: str | None = Header(default=None)):
    secret = os.getenv("ACCESS_TOKEN")
    if not secret or x_access_token != secret:
        raise HTTPException(status_code=401, detail="Invalid access token")
    if not re.fullmatch(r"[A-Za-z0-9._]{1,30}", username):
        raise HTTPException(status_code=400, detail="Invalid username")
    if not 1 <= limit <= 100:
        raise HTTPException(status_code=400, detail="Limit must be 1-100")
    try:
        loader = instaloader.Instaloader(download_pictures=False, download_videos=False,
                                        download_video_thumbnails=False, save_metadata=False,
                                        compress_json=False, quiet=True)
        profile = instaloader.Profile.from_username(loader.context, username)
        result = []
        for post in profile.get_posts():
            if len(result) >= limit:
                break
            result.append({"date_utc": post.date_utc.isoformat(), "shortcode": post.shortcode,
                           "url": "https://www.instagram.com/p/" + post.shortcode + "/",
                           "caption": (post.caption or "")[:4000], "likes": post.likes,
                           "comments": post.comments, "is_video": post.is_video})
        return {"username": username, "retrieved": len(result), "posts": result,
                "note": "Only accessible public posts. Instagram may block cloud IPs."}
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Instagram access failed: {type(exc).__name__}")
