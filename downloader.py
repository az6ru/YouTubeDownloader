import os
import uuid
import threading
from datetime import datetime, timedelta
import yt_dlp
from extensions import socketio, db
from models import Download

active_downloads = {}

class VideoDownloader:
    def __init__(self, url, format_id, output_path):
        self.url = url
        self.format_id = format_id
        self.output_path = output_path
        self.download_id = str(uuid.uuid4())
        self.progress = 0
        self.speed = "0 B/s"
        self.eta = "Unknown"
        self.status = "pending"
        self._thread = None

    def progress_hook(self, d):
        if d['status'] == 'downloading':
            self.progress = (d['downloaded_bytes'] / d['total_bytes']) * 100 if 'total_bytes' in d else 0
            self.speed = d.get('speed_str', '0 B/s')
            self.eta = d.get('eta_str', 'Unknown')
            socketio.emit('progress_update', {
                'download_id': self.download_id,
                'progress': self.progress,
                'speed': self.speed,
                'eta': self.eta,
                'status': self.status
            })
        elif d['status'] == 'finished':
            self.status = 'finished'
            self.progress = 100
            socketio.emit('download_complete', {
                'download_id': self.download_id
            })

    def download(self):
        self.status = "downloading"
        output_template = os.path.join(self.output_path, f"{self.download_id}", "%(title)s.%(ext)s")

        ydl_opts = {
            'format': f'{self.format_id}+bestaudio/best',
            'outtmpl': output_template,
            'progress_hooks': [self.progress_hook],
        }

        if 'audio' in self.format_id.lower():
            ydl_opts.update({
                'format': 'bestaudio',
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '192',
                }],
            })

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(self.url)
                download = Download(
                    id=self.download_id,
                    url=self.url,
                    title=info.get('title'),
                    format_id=self.format_id,
                    status='completed',
                    completed_at=datetime.utcnow(),
                    file_path=output_template % {'title': info['title'], 'ext': 'mp4'},
                    file_size=os.path.getsize(output_template % {'title': info['title'], 'ext': 'mp4'})
                )
                db.session.add(download)
                db.session.commit()

        except Exception as e:
            self.status = "error"
            socketio.emit('download_error', {
                'download_id': self.download_id,
                'error': str(e)
            })

    def start(self):
        self._thread = threading.Thread(target=self.download)
        self._thread.start()
        active_downloads[self.download_id] = self

        # Schedule cleanup after 24 hours
        def cleanup():
            if self.download_id in active_downloads:
                del active_downloads[self.download_id]
                if os.path.exists(os.path.join(self.output_path, self.download_id)):
                    import shutil
                    shutil.rmtree(os.path.join(self.output_path, self.download_id))

        cleanup_thread = threading.Timer(86400, cleanup)  # 24 hours
        cleanup_thread.start()

        return self.download_id