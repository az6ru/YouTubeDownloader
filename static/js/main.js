document.addEventListener('DOMContentLoaded', function() {
    const socket = io();
    let currentDownloadId = null;

    const elements = {
        videoUrl: document.getElementById('videoUrl'),
        searchBtn: document.getElementById('searchBtn'),
        videoInfo: document.getElementById('videoInfo'),
        thumbnail: document.getElementById('thumbnail'),
        videoTitle: document.getElementById('videoTitle'),
        videoDuration: document.getElementById('videoDuration'),
        formatSelect: document.getElementById('formatSelect'),
        downloadBtn: document.getElementById('downloadBtn'),
        progressBar: document.getElementById('progressBar'),
        progressBarInner: document.querySelector('.progress-bar'),
        downloadStats: document.getElementById('downloadStats'),
        downloadLink: document.getElementById('downloadLink'),
        errorAlert: document.getElementById('errorAlert')
    };

    function formatDuration(seconds) {
        const hours = Math.floor(seconds / 3600);
        const minutes = Math.floor((seconds % 3600) / 60);
        const secs = seconds % 60;
        
        if (hours > 0) {
            return `${hours}:${String(minutes).padStart(2, '0')}:${String(secs).padStart(2, '0')}`;
        }
        return `${minutes}:${String(secs).padStart(2, '0')}`;
    }

    function formatFileSize(bytes) {
        const sizes = ['B', 'KB', 'MB', 'GB'];
        if (bytes === 0) return '0 B';
        const i = parseInt(Math.floor(Math.log(bytes) / Math.log(1024)));
        return Math.round(bytes / Math.pow(1024, i), 2) + ' ' + sizes[i];
    }

    function showError(message) {
        elements.errorAlert.textContent = message;
        elements.errorAlert.classList.remove('d-none');
        setTimeout(() => {
            elements.errorAlert.classList.add('d-none');
        }, 5000);
    }

    elements.searchBtn.addEventListener('click', async function() {
        const url = elements.videoUrl.value.trim();
        if (!url) {
            showError('Пожалуйста, введите URL видео');
            return;
        }

        try {
            const response = await fetch('/api/validate', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ url })
            });

            const data = await response.json();
            
            if (response.ok) {
                elements.thumbnail.src = data.thumbnail;
                elements.videoTitle.textContent = data.title;
                elements.videoDuration.textContent = formatDuration(data.duration);
                
                // Clear and populate format select
                elements.formatSelect.innerHTML = '<option selected disabled>Выберите формат</option>';
                data.formats.forEach(format => {
                    const option = document.createElement('option');
                    option.value = format.format_id;
                    option.textContent = `${format.quality} (${format.height}p) • ${formatFileSize(format.filesize)}`;
                    elements.formatSelect.appendChild(option);
                });
                
                elements.videoInfo.classList.remove('d-none');
            } else {
                showError(data.error || 'Ошибка при проверке видео');
            }
        } catch (error) {
            showError('Произошла ошибка при обработке запроса');
        }
    });

    elements.downloadBtn.addEventListener('click', async function() {
        const url = elements.videoUrl.value.trim();
        const formatId = elements.formatSelect.value;

        if (!formatId) {
            showError('Пожалуйста, выберите формат');
            return;
        }

        try {
            const response = await fetch('/api/download', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ url, format_id: formatId })
            });

            const data = await response.json();
            
            if (response.ok) {
                currentDownloadId = data.download_id;
                elements.progressBar.classList.remove('d-none');
                elements.downloadStats.textContent = 'Начало загрузки...';
            } else {
                showError(data.error || 'Ошибка при начале загрузки');
            }
        } catch (error) {
            showError('Произошла ошибка при обработке запроса');
        }
    });

    socket.on('progress_update', function(data) {
        if (data.download_id === currentDownloadId) {
            elements.progressBarInner.style.width = `${data.progress}%`;
            elements.downloadStats.textContent = 
                `Скорость: ${data.speed} • Осталось: ${data.eta}`;
        }
    });

    socket.on('download_complete', function(data) {
        if (data.download_id === currentDownloadId) {
            elements.progressBarInner.style.width = '100%';
            elements.downloadStats.textContent = 'Загрузка завершена!';
            elements.downloadLink.classList.remove('d-none');
            elements.downloadLink.querySelector('a').href = `/download/${currentDownloadId}`;
        }
    });

    socket.on('download_error', function(data) {
        if (data.download_id === currentDownloadId) {
            showError(data.error || 'Ошибка при загрузке');
            elements.progressBar.classList.add('d-none');
        }
    });
});
