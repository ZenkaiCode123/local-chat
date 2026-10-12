<div align="center">

# Local Chat

**A fast, private web interface for your local [Ollama](https://ollama.com) models.**
Runs on your own hardware. No accounts, no telemetry, no build step.

</div>

---

## Features

**Chat**
- Streaming replies, token by token, with live tokens-per-second
- Multiple conversations, each with its own settings and context, saved in your browser
- Stop, copy and regenerate any reply
- Export a chat as Markdown (`.md`) or a full JSON backup (settings and history included)

**Models**
- Browse installed models with parameter size, quantization, disk usage and capabilities (vision, tools, thinking)
- Switch models in one click
- Pull new models from the Ollama library with a live progress bar
- Delete models you no longer need to free disk space

**Attachments and vision**
- Attach images (`.png`, `.jpg`, `.webp`) for multimodal models such as `llama3.2-vision` or `moondream`
- Attach code and text files (`.py`, `.js`, `.json`, `.csv`, `.md`, `.txt`) with formatted previews
- Drag and drop, or paste from the clipboard with <kbd>Ctrl</kbd> + <kbd>V</kbd>

**Tuning**
- System prompt, temperature, top P, top K, repeat penalty, context window (`num_ctx`) and max reply tokens
- Set per chat or as your global default
- Live context meter that warns you before the window fills up

**Interface**
- Light and dark themes
- Responsive layout with a slide-out sidebar on phones
- Syntax-highlighted code blocks with one-click copy

---

## Quick start

### 1. Install Ollama and pull a model

```bash
ollama pull llama3.2
```

### 2. Get the project

```bash
git clone https://github.com/your-username/local-chat.git
cd local-chat
```

### 3. Run it

The same command works on Windows, macOS, Linux and WSL. It creates a virtual environment on the first run, installs dependencies, starts Ollama if needed, and opens your browser:

```bash
python launch.py          # on some systems: python3 launch.py
```

Then open **http://localhost:3000** if it doesn't open by itself.

<details>
<summary>Prefer to set it up by hand?</summary>

```bash
# Linux / macOS / WSL
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python app.py
```

```powershell
# Windows (PowerShell)
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python app.py
```

> Use `python -m pip` rather than plain `pip`. It installs into the active venv and avoids the "externally-managed-environment" error on Debian and Ubuntu.

</details>

### Stopping the app

Press <kbd>Ctrl</kbd> + <kbd>C</kbd> in the terminal, or close the terminal window. Closing the browser tab does **not** stop the server; you can reopen the page at any time.

---

## Desktop shortcut (optional)

Everything works without this. It only saves you from opening a terminal. Run once from the project folder:

```bash
python install_shortcut.py
```

| Your system | What you get |
| --- | --- |
| **Windows** | `Local Chat` on your Desktop and in the Start menu |
| **macOS** | `Local Chat.app` in `~/Applications` (drag it to the Dock) |
| **Linux** | `Local Chat` in your app menu, plus the Desktop if you have one |
| **WSL** | A Windows Desktop and Start menu shortcut that runs the app inside WSL |

Clicking the shortcut opens a terminal window and launches the app. Close the window (or press <kbd>Ctrl</kbd> + <kbd>C</kbd>) to stop it.

- If you move the project folder, run `python install_shortcut.py` again.
- GNOME: right-click the Desktop icon and choose **Allow Launching** the first time.
- Windows may show a SmartScreen prompt for scripts you downloaded: **More info > Run anyway**.

---

## Configuration

Set these environment variables before starting the server.

| Variable     | Default                  | Description                      |
| ------------ | ------------------------ | -------------------------------- |
| `OLLAMA_URL` | `http://localhost:11434` | Address of the Ollama API        |
| `PORT`       | `3000`                   | Port for the web interface       |

```bash
# Custom port and a remote Ollama machine (Linux / macOS)
OLLAMA_URL="http://192.168.1.50:11434" PORT=8080 python app.py
```

```powershell
# Windows (PowerShell)
$env:OLLAMA_URL="http://192.168.1.50:11434"; $env:PORT=8080; python app.py
```

### Using it from your phone or another computer

By default the server only listens on `127.0.0.1` (your own machine). To reach it from other devices on your Wi-Fi, change the `host` in `app.py` to `"0.0.0.0"`, then open `http://<your-computer-ip>:3000` on the other device.

> **Security note:** there is no login. Anyone on your network can then use your models, so only do this on a network you trust.

---

## Troubleshooting

| Problem | Fix |
| --- | --- |
| "Cannot reach Ollama" | Start it with `ollama serve`, or check `OLLAMA_URL` |
| Model list is empty | You haven't pulled a model yet: `ollama pull llama3.2` |
| `externally-managed-environment` error | Use a venv and `python -m pip install -r requirements.txt` |
| Page shows 404 or "index.html not found" | Make sure `public/index.html` sits next to `app.py` |
| "Address already in use" | Another copy is running, or change the port: `PORT=8080 python app.py` |
| `python` not found | Try `python3`, or on Windows `py -3`. Install Python from python.org and tick **Add to PATH** |
| `venv` creation fails on Debian / Ubuntu / WSL | `sudo apt install python3-venv` |
| Replies get cut off or forget earlier messages | Raise the context window in Settings, or start a new chat |
| Shortcut not on the Desktop | Linux: check your app menu, many desktops don't show Desktop icons. WSL: it's on the *Windows* Desktop, not inside Linux |

---

## Your data

- Chats and settings live in your browser's `localStorage`, on this device only. Clearing site data, switching browsers or using a private window will not show them.
- Use **Export** to back up important conversations.
- Prompts and replies stay between your browser, this server and your Ollama instance.

---

## Project structure

```
local-chat/
├── app.py                # Flask server: serves the UI, streams /api/* to Ollama
├── public/
│   └── index.html        # Single-page UI (vanilla HTML/CSS/JS, no build step)
├── launch.py             # Cross-platform launcher (venv, dependencies, Ollama, browser)
├── install_shortcut.py   # Optional: Desktop / Start menu / app shortcut with icon
├── assets/               # App icons (.svg, .ico, .icns, .png)
├── requirements.txt      # flask, requests
└── README.md
```

## How it works

- **Frontend:** a single static page in plain HTML, CSS and JavaScript. No bundler, no Node.js.
- **Backend:** a small Flask app that serves the page and forwards `/api/*` requests to Ollama, streaming responses straight through. When you press Stop, the connection to Ollama is closed and generation ends.
- **Storage:** your browser's `localStorage`. The server stores nothing.

---

## Contributing

Issues and pull requests are welcome.

1. Fork the repository
2. Create a branch: `git checkout -b feature/my-change`
3. Commit and push your changes
4. Open a pull request

## License

Distributed under the MIT License. See `LICENSE` for details.
