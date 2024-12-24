from app import app
from extensions import socketio
import os

if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))  # Используйте порт из переменной окружения
    socketio.run(app, host="0.0.0.0", port=port, debug=True)
