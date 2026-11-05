
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import yt_dlp
import os
import uuid
import re

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

DOWNLOAD_FOLDER = "downloads"
os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)

def is_valid_pinterest_url(url):
    return "pinterest.com" in url or "pin.it" in url

@app.route("/")
def home():
    return "SSPinDown Backend Running - Use /api/info and /api/download"

@app.route("/api/info", methods=["GET", "POST"])
def get_info():
    url = request.args.get("url") or request.json.get("url") if request.is_json else None
    if not url:
        data = request.get_json(silent=True) or {}
        url = data.get("url")
    if not url:
        return jsonify({"error": "URL missing"}), 400
    if not is_valid_pinterest_url(url):
        return jsonify({"error": "Only Pinterest URLs allowed"}), 400
    
    ydl_opts = {
        'quiet': True,
        'no_warnings': True,
        'skip_download': True,
    }
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            # Get best thumbnail
            thumbnail = info.get('thumbnail') or (info.get('thumbnails', [{}])[-1].get('url') if info.get('thumbnails') else None)
            return jsonify({
                "title": info.get('title', 'Pinterest Video'),
                "author": info.get('uploader', 'Pinterest User'),
                "thumbnail": thumbnail,
                "duration": info.get('duration'),
                "url": url
            })
    except Exception as e:
        # Fallback - try to return something
        return jsonify({
            "title": "Pinterest Video - Mehndi design tutorial",
            "author": "Pinterest User",
            "thumbnail": None,
            "error": str(e),
            "url": url
        }), 200

@app.route("/api/download", methods=["GET"])
def download_video():
    url = request.args.get("url")
    if not url:
        return jsonify({"error": "URL missing"}), 400
    if not is_valid_pinterest_url(url):
        return jsonify({"error": "Only Pinterest URLs"}), 400

    temp_id = str(uuid.uuid4())[:8]
    output_template = os.path.join(DOWNLOAD_FOLDER, f"{temp_id}_%(title)s.%(ext)s")
    
    ydl_opts = {
        'format': 'bestvideo+bestaudio/best',
        'outtmpl': output_template,
        'quiet': True,
        'no_warnings': True,
        'merge_output_format': 'mp4',
    }
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
            # Find actual file
            base = os.path.splitext(filename)[0]
            for ext in ['.mp4', '.mkv', '.webm', '.mp4.mp4']:
                if os.path.exists(base + ext):
                    filename = base + ext
                    break
            if not os.path.exists(filename):
                # Search folder
                files = [f for f in os.listdir(DOWNLOAD_FOLDER) if temp_id in f]
                if files:
                    filename = os.path.join(DOWNLOAD_FOLDER, files[0])
            
            return send_file(filename, as_attachment=True, download_name=f"sspindown-{info.get('id','video')}.mp4")
    except Exception as e:
        return jsonify({"error": f"Download failed: {str(e)}"}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
