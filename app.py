"""Flask backend: serves ./public and proxies /api/* to Ollama (streaming)."""
import os

import requests
from flask import Flask, Response, jsonify, request, send_from_directory

OLLAMA = os.environ.get("OLLAMA_URL", "http://localhost:11434")
PORT = int(os.environ.get("PORT", 3000))

BASE = os.path.dirname(os.path.abspath(__file__))
# Use ./public/index.html if it exists, otherwise index.html sitting next to app.py
WEB_DIR = os.path.join(BASE, "public") if os.path.isfile(os.path.join(BASE, "public", "index.html")) else BASE

app = Flask(__name__, static_folder=None)


@app.get("/")
def index():
    if not os.path.isfile(os.path.join(WEB_DIR, "index.html")):
        return "index.html not found. Put it next to app.py or inside a public/ folder.", 404
    return send_from_directory(WEB_DIR, "index.html")


@app.get("/<path:path>")
def static_proxy(path):
    if os.path.isfile(os.path.join(WEB_DIR, path)):
        return send_from_directory(WEB_DIR, path)
    return "File not found", 404

@app.get("/icon.svg")
def icon():
    return send_from_directory(WEB_DIR, "icon.svg")

@app.route("/api/<path:path>", methods=["GET", "POST", "DELETE"])
def proxy(path):
    try:
        upstream = requests.request(
            request.method,
            f"{OLLAMA}/api/{path}",
            data=request.get_data() or None,
            headers={"Content-Type": "application/json"},
            stream=True,
            timeout=(5, None),  # fail fast if Ollama is down, no read timeout for slow models
        )
    except requests.RequestException:
        return jsonify(error=f"Cannot reach Ollama at {OLLAMA}. Is it running?"), 502

    def generate():
        try:
            for chunk in upstream.iter_content(chunk_size=None):
                if chunk:
                    yield chunk
        finally:
            upstream.close()  # runs when the browser hits Stop -> cancels generation

    return Response(
        generate(),
        status=upstream.status_code,
        content_type=upstream.headers.get("Content-Type", "application/json"),
    )


if __name__ == "__main__":
    print(f"Serving UI from: {WEB_DIR}")
    print(f"Chat UI: http://localhost:{PORT}  (Ollama: {OLLAMA})")
    app.run(host="127.0.0.1", port=PORT, threaded=True)
