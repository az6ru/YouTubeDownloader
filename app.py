import os
import logging
from flask import Flask, render_template, jsonify, request
from extensions import db, socketio
import yt_dlp

logging.basicConfig(level=logging.DEBUG)

app = Flask(__name__)

app.config["SECRET_KEY"] = os.environ.get("FLASK_SECRET_KEY", "dev_key")
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL")
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
}
app.config["UPLOAD_FOLDER"] = "/tmp/downloads"
os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

db.init_app(app)
socketio.init_app(app)

with app.app_context():
    import models
    from downloader import VideoDownloader, active_downloads
    db.create_all()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/validate', methods=['POST'])
def validate_url():
    url = request.json.get('url')
    if not url:
        return jsonify({"error": "URL is required"}), 400

    try:
        with yt_dlp.YoutubeDL() as ydl:
            info = ydl.extract_info(url, download=False)
            formats = []

            # Group formats by quality
            for f in info['formats']:
                if f.get('height'):
                    if f['height'] >= 2160:
                        quality = "4K"
                    elif f['height'] >= 1440:
                        quality = "2K"
                    elif f['height'] >= 1080:
                        quality = "FullHD"
                    elif f['height'] >= 720:
                        quality = "HD"
                    else:
                        quality = "SD"

                    formats.append({
                        'format_id': f['format_id'],
                        'quality': quality,
                        'height': f['height'],
                        'ext': f['ext'],
                        'filesize': f.get('filesize', 0)
                    })

            return jsonify({
                'title': info['title'],
                'thumbnail': info['thumbnail'],
                'duration': info['duration'],
                'author': info.get('uploader', 'Unknown'),
                'upload_date': info.get('upload_date', ''),
                'description': info.get('description', ''),
                'view_count': info.get('view_count', 0),
                'formats': formats
            })
    except Exception as e:
        return jsonify({"error": str(e)}), 400

@app.route('/api/download', methods=['POST'])
def start_download():
    url = request.json.get('url')
    format_id = request.json.get('format_id')

    if not url or not format_id:
        return jsonify({"error": "URL and format are required"}), 400

    try:
        downloader = VideoDownloader(url, format_id, app.config['UPLOAD_FOLDER'])
        download_id = downloader.start()
        return jsonify({"download_id": download_id})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@socketio.on('connect')
def handle_connect():
    logging.debug('Client connected')

@socketio.on('disconnect')
def handle_disconnect():
    logging.debug('Client disconnected')

@socketio.on('get_progress')
def handle_progress(download_id):
    if download_id in active_downloads:
        download = active_downloads[download_id]
        return {
            'status': download.status,
            'progress': download.progress,
            'speed': download.speed,
            'eta': download.eta
        }
    return {'error': 'Download not found'}