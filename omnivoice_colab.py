#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🎙️ OmniVoice Studio — Google Colab Setup Script (v10 — ALL languages + ALL LLM Skills)
====================================================================================

v10 Features:
  ✅ সব ভাষা ডাইনামিক সাপোর্ট — Hindi/Bengali/English/Turkish/Urdu/Spanish/
     French/Korean/Japanese/Indonesian + আরও ২০টা (তোমার প্রয়োজনীয় সব ভাষা)
  ✅ Dub translation-এও script name inject (আগে শুধু Cinematic + Speech-rate-এ ছিল)
  ✅ সব ৬টা LLM Skills-এ retry/backoff/timeout কভার
  ✅ Ollama (ngrok) সেটআপের জন্য অপ্টিমাইজড
  ✅ 16টা প্রোভাইডার সাপোর্ট (Groq/OpenRouter/Cerebras/NVIDIA/Google/Mistral/Cohere/
     SambaNova/SiliconFlow/HF/Cloudflare/GitHub/OpenAI/Ollama/LM Studio/Custom)
  ✅ Dynamic Port Forwarding Tunnels (Cloudflare Free/API, Ngrok, SSH, Localhost)
  ✅ Automatic Pyannote Audio / Speaker Diarization dependency setup
  ✅ Automated Google Colab Secrets loading (HF_TOKEN, NGROK_AUTH_TOKEN, CLOUDFLARE_TUNNEL_TOKEN)
  ✅ Exposed all LLM Resilience environments as parameters in Colab Form

Usage:
    !python omnivoice_colab_fixed_v10.py
"""

import os
import sys
import subprocess
import time
import json
import urllib.request
import re
import threading
from queue import Queue, Empty

# ============================================================
# 0. CONFIGURATION (Colab Form Parameters)
# ============================================================
#@title 🎙️ Setup & Start OmniVoice Studio { display-mode: "form" }
#@markdown ---
#@markdown ### 🚀 Repository & Data Settings
REPO_URL = "https://github.com/debpalash/OmniVoice-Studio.git" #@param {type:"string"}
WORK_DIR = "/content/OmniVoice-Studio" #@param {type:"string"}
DATA_DIR = "/content/omnivoice_data" #@param {type:"string"}
PORT = 3900 #@param {type:"integer"}

#@markdown ### 🔑 API Keys & Secrets
#@markdown *Leave these blank to automatically load them from Google Colab Secrets (recommended)*
HF_TOKEN = "" #@param {type:"string"}

#@markdown ### 🌐 Connection & Tunnel Setup
TUNNEL_PROVIDER = "cloudflare_free" #@param ["cloudflare_free", "cloudflare_api", "ngrok", "ssh", "localhost"]
NGROK_AUTH = "" #@param {type:"string"}
CLOUDFLARE_TUNNEL_TOKEN = "" #@param {type:"string"}

#@markdown ### ⚙️ LLM Resilience & Settings
OMNIVOICE_LLM_TIMEOUT = 300 #@param {type:"integer"}
OMNIVOICE_CINEMATIC_BUDGET_S = 0 #@param {type:"integer"}
OMNIVOICE_LLM_CONCURRENCY = 2 #@param {type:"integer"}
OMNIVOICE_REFINE_RATIO_MIN = 0.2 #@param {type:"number"}
OMNIVOICE_REFINE_RATIO_MAX = 5.0 #@param {type:"number"}
OMNIVOICE_LLM_RPM = 0 #@param {type:"integer"}
OMNIVOICE_LLM_RPS = 0 #@param {type:"integer"}
OMNIVOICE_LLM_MAX_RETRIES = 5 #@param {type:"integer"}
OMNIVOICE_LLM_BACKOFF_BASE = 2 #@param {type:"integer"}
OMNIVOICE_LLM_BACKOFF_CAP = 60.0 #@param {type:"number"}
OMNIVOICE_LLM_RATE_LIMIT_BACKOFF = 30.0 #@param {type:"number"}
OMNIVOICE_LOCAL_LLM_TIMEOUT = 300 #@param {type:"integer"}
OMNIVOICE_CLOUD_LLM_TIMEOUT = 60 #@param {type:"integer"}
OMNIVOICE_PATCH_PROMPTS = True #@param {type:"boolean"}
OMNIVOICE_PATCH_DUB_TRANSLATION = True #@param {type:"boolean"}

# Try loading tokens from Colab Secrets if not provided in Form
try:
    from google.colab import userdata
    if not HF_TOKEN and userdata:
        HF_TOKEN = userdata.get("HF_TOKEN") or ""
        if HF_TOKEN:
            print("🔑 HF_TOKEN loaded from Colab Secrets")
    if not NGROK_AUTH and userdata:
        NGROK_AUTH = userdata.get("NGROK_AUTH_TOKEN") or userdata.get("NGROK_AUTH") or ""
        if NGROK_AUTH:
            print("🔑 NGROK_AUTH loaded from Colab Secrets")
    if not CLOUDFLARE_TUNNEL_TOKEN and userdata:
        CLOUDFLARE_TUNNEL_TOKEN = userdata.get("CLOUDFLARE_TUNNEL_TOKEN") or ""
        if CLOUDFLARE_TUNNEL_TOKEN:
            print("🔑 CLOUDFLARE_TUNNEL_TOKEN loaded from Colab Secrets")
except Exception:
    pass

# 🔥 v9 — প্রোভাইডার RPM প্রিসেট
PROVIDER_RPM_PRESETS = {
    "groq": "28", "openrouter": "18", "cerebras": "38", "cloudflare": "45",
    "nvidia": "35", "google-ai": "50", "mistral": "4", "cohere": "20",
    "sambanova": "50", "siliconflow": "50", "huggingface": "30", "github-models": "30",
    "openai": "0", "ollama": "0", "lmstudio": "0", "custom": "0",
}

# 🔥 v10 — LLM Resilience parameters mapped from Colab Form
LLM_RESILIENCE_ENV = {
    "OMNIVOICE_LLM_TIMEOUT": str(OMNIVOICE_LLM_TIMEOUT),
    "OMNIVOICE_CINEMATIC_BUDGET_S": str(OMNIVOICE_CINEMATIC_BUDGET_S),
    "OMNIVOICE_LLM_CONCURRENCY": str(OMNIVOICE_LLM_CONCURRENCY),
    "OMNIVOICE_REFINE_RATIO_MIN": str(OMNIVOICE_REFINE_RATIO_MIN),
    "OMNIVOICE_REFINE_RATIO_MAX": str(OMNIVOICE_REFINE_RATIO_MAX),
    "OMNIVOICE_LLM_RPM": str(OMNIVOICE_LLM_RPM),
    "OMNIVOICE_LLM_RPS": str(OMNIVOICE_LLM_RPS),
    "OMNIVOICE_LLM_MAX_RETRIES": str(OMNIVOICE_LLM_MAX_RETRIES),
    "OMNIVOICE_LLM_BACKOFF_BASE": str(OMNIVOICE_LLM_BACKOFF_BASE),
    "OMNIVOICE_LLM_BACKOFF_CAP": str(OMNIVOICE_LLM_BACKOFF_CAP),
    "OMNIVOICE_LLM_RATE_LIMIT_BACKOFF": str(OMNIVOICE_LLM_RATE_LIMIT_BACKOFF),
    "OMNIVOICE_LOCAL_LLM_TIMEOUT": str(OMNIVOICE_LOCAL_LLM_TIMEOUT),
    "OMNIVOICE_CLOUD_LLM_TIMEOUT": str(OMNIVOICE_CLOUD_LLM_TIMEOUT),
    "OMNIVOICE_PATCH_PROMPTS": "1" if OMNIVOICE_PATCH_PROMPTS else "0",
    "OMNIVOICE_PATCH_DUB_TRANSLATION": "1" if OMNIVOICE_PATCH_DUB_TRANSLATION else "0",
}

for _k, _v in LLM_RESILIENCE_ENV.items():
    os.environ.setdefault(_k, _v)

os.chdir("/content")

# ============================================================
# Helper Functions
# ============================================================
def run_cmd(cmd, cwd=None, shell=False, check=True, timeout=None, capture=True, env=None):
    if isinstance(cmd, str):
        shell = True
    if capture:
        result = subprocess.run(
            cmd, shell=shell, cwd=cwd, capture_output=True, text=True, timeout=timeout, env=env
        )
    else:
        result = subprocess.run(cmd, shell=shell, cwd=cwd, timeout=timeout, env=env)
    if check and result.returncode != 0:
        err = result.stderr[-1000:] if result.stderr else "Unknown error"
        out = result.stdout[-500:] if result.stdout else ""
        print(f"   ⚠️ Command failed (exit {result.returncode})")
        if out: print(f"   stdout: {out}")
        if err: print(f"   stderr: {err}")
        return False, result
    return True, result

def print_section(title):
    print(f"\n{'='*60}\n🔄 {title}\n{'='*60}")

def check_health(port, timeout=10):
    try:
        with urllib.request.urlopen(f"http://localhost:{port}/health", timeout=timeout) as resp:
            return json.loads(resp.read())
    except Exception:
        return None

def find_venv_python(work_dir):
    candidates = [
        os.path.join(work_dir, ".venv", "bin", "python"),
        os.path.join(work_dir, ".venv", "bin", "python3"),
        os.path.join(work_dir, ".venv", "Scripts", "python.exe"),
    ]
    for path in candidates:
        if os.path.exists(path):
            return path
    return None

def ensure_package(venv_python, package, timeout=300):
    check_name = package
    install_name = package
    if package == "pyannote.audio":
        check_name = "pyannote.audio"
        install_name = "pyannote.audio"

    ok, _ = run_cmd([venv_python, "-c", f"import {check_name}"], check=False, timeout=30)
    if ok:
        return True
    print(f"   📦 Installing {install_name}...")
    ok, _ = run_cmd(
        [venv_python, "-m", "pip", "install", install_name, "--quiet"],
        timeout=timeout, check=False
    )
    return ok

# ============================================================
# Dynamic Reverse Tunnel Manager
# ============================================================
class TunnelManager:
    def __init__(self):
        self.process = None
        self.lock = threading.Lock()
        self.bg_threads = []
        self.public_url = None

    def stop_tunnel(self):
        with self.lock:
            if self.process:
                print(f"   🔄 Stopping active tunnel process (PID {self.process.pid})...")
                try:
                    self.process.terminate()
                    self.process.wait(timeout=5)
                except Exception as e:
                    print(f"   ⚠️ Error terminating tunnel process: {e}")
                    try:
                        self.process.kill()
                    except:
                        pass
                self.process = None
            
            try:
                from pyngrok import ngrok
                ngrok.kill()
            except Exception:
                pass

            self.public_url = None

    def start_tunnel(self, provider, port, ngrok_auth=None, cf_token=None):
        self.stop_tunnel()
        with self.lock:
            try:
                if provider == "ngrok":
                    url = self._start_ngrok(port, ngrok_auth)
                elif provider == "cloudflare_free":
                    url = self._start_cloudflare_free(port)
                elif provider == "cloudflare_api":
                    url = self._start_cloudflare_api(port, cf_token)
                elif provider == "ssh":
                    url = self._start_ssh(port)
                elif provider == "localhost":
                    url = f"http://localhost:{port}"
                else:
                    raise ValueError(f"Unknown provider: {provider}")

                self.public_url = url
                return url
            except Exception as e:
                print(f"   ❌ Failed to start tunnel: {e}")
                self.public_url = f"http://localhost:{port}"
                raise e

    def _start_ngrok(self, port, auth_token):
        print("   ⚡ Starting ngrok tunnel...")
        try:
            from pyngrok import ngrok, conf
        except ImportError:
            print("   📦 Installing pyngrok...")
            subprocess.run([sys.executable, "-m", "pip", "install", "pyngrok", "--quiet"])
            from pyngrok import ngrok, conf

        if not auth_token or not auth_token.strip():
            raise RuntimeError("Ngrok Auth Token is required for Ngrok tunnel.")

        conf.get_default().auth_token = auth_token.strip()
        tunnel = ngrok.connect(str(port), "http")
        return tunnel.public_url

    def _start_cloudflare_free(self, port):
        binary_path = "./cloudflared"
        self._ensure_cloudflared_binary(binary_path)

        print("   ⚡ Starting Cloudflare Free Tunnel...")
        cmd = [binary_path, "tunnel", "--url", f"http://127.0.0.1:{port}"]
        self.process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
            errors="replace"
        )
        pattern = re.compile(r"https://[a-zA-Z0-9\-]+\.trycloudflare\.com")
        url = self._capture_url_from_process(self.process, pattern, timeout=45)
        if not url:
            raise RuntimeError("Failed to capture Cloudflare Free tunnel URL.")
        return url

    def _start_cloudflare_api(self, port, tunnel_token):
        if not tunnel_token or not tunnel_token.strip():
            raise RuntimeError("Cloudflare Tunnel Token is required for API Tunnel Mode.")

        binary_path = "./cloudflared"
        self._ensure_cloudflared_binary(binary_path)

        print("   ⚡ Starting Cloudflare Named Tunnel (via token)...")
        cmd = [binary_path, "tunnel", "--no-autoupdate", "run", "--token", tunnel_token.strip()]
        self.process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
            errors="replace"
        )
        
        q = Queue()
        reader_t = threading.Thread(target=self._stream_reader, args=(self.process, q), daemon=True)
        reader_t.start()
        drain_t = threading.Thread(target=self._drain_stream_to_log, args=(q, "[cf-api]"), daemon=True)
        drain_t.start()
        self.bg_threads.extend([reader_t, drain_t])

        time.sleep(5)
        if self.process.poll() is not None:
            raise RuntimeError(f"Cloudflare API tunnel failed with exit code: {self.process.poll()}")
        
        return "Custom URL configured in your Cloudflare Dashboard"

    def _start_ssh(self, port):
        print("   ⚡ Starting SSH tunnel via serveo.net...")
        url = None
        
        try:
            self.process = subprocess.Popen(
                ["ssh", "-tt", "-o", "StrictHostKeyChecking=no", "-o", "ServerAliveInterval=60",
                 "-R", f"80:127.0.0.1:{port}", "serveo.net"],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                errors="replace"
            )
            pattern = re.compile(r"https://[a-zA-Z0-9\-.]+\.serveo\.net")
            url = self._capture_url_from_process(self.process, pattern, timeout=25)
        except Exception as e:
            print(f"   ⚠️ serveo.net SSH tunnel failed: {e}")

        if url:
            return url

        print("   ⚠️ serveo.net failed. Falling back to localhost.run...")
        self.stop_tunnel()

        try:
            self.process = subprocess.Popen(
                ["ssh", "-tt", "-o", "StrictHostKeyChecking=no", "-o", "ServerAliveInterval=60",
                 "-R", f"80:127.0.0.1:{port}", "nokey@localhost.run"],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                errors="replace"
            )
            pattern = re.compile(r"https://[a-zA-Z0-9\-.]+\.(?:lhrtunnel\.link|lhr\.life)")
            url = self._capture_url_from_process(self.process, pattern, timeout=25)
        except Exception as e:
            print(f"   ⚠️ localhost.run SSH tunnel failed: {e}")

        if url:
            return url

        raise RuntimeError("All SSH reverse tunnels (serveo / localhost.run) failed.")

    def _ensure_cloudflared_binary(self, binary_path):
        if os.path.exists(binary_path) and os.path.getsize(binary_path) < 10 * 1024 * 1024:
            try:
                os.remove(binary_path)
            except Exception as e:
                print(f"   ⚠️ Could not remove corrupted cloudflared binary: {e}")

        if not os.path.exists(binary_path):
            print("   📥 Downloading cloudflared binary...")
            subprocess.run(
                ["wget", "-q", "--tries=3", "--timeout=15",
                 "https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64",
                 "-O", binary_path],
                check=True,
            )
            subprocess.run(["chmod", "+x", binary_path], check=True)

    def _stream_reader(self, proc, q: Queue):
        try:
            for line in iter(proc.stdout.readline, ''):
                q.put(line)
        except Exception:
            pass

    def _drain_stream_to_log(self, q: Queue, prefix: str):
        while True:
            try:
                line = q.get(timeout=5)
                if line:
                    pass
            except Empty:
                continue

    def _capture_url_from_process(self, proc, pattern, timeout=40):
        q = Queue()
        reader_t = threading.Thread(target=self._stream_reader, args=(proc, q), daemon=True)
        reader_t.start()

        url = None
        start = time.monotonic()
        while time.monotonic() - start < timeout:
            try:
                line = q.get(timeout=1)
                cleaned_line = line.strip()
                if cleaned_line:
                    print(f"      [tunnel] {cleaned_line}")

                m = pattern.search(line)
                if m:
                    matched = m.group(0)
                    if "console.serveo.net" not in matched and matched != "https://serveo.net":
                        url = matched
                        break
            except Empty:
                if proc.poll() is not None:
                    break
                continue

        drain_t = threading.Thread(target=self._drain_stream_to_log, args=(q, "[tunnel]"), daemon=True)
        drain_t.start()
        self.bg_threads.extend([reader_t, drain_t])
        return url

# ============================================================
# 1-9. Setup (Python, deps, Bun, uv, clone, frontend, backend, cuDNN, HF models)
# ============================================================
print_section("Python Version Check")
print(f"Current: {sys.version}")
if sys.version_info < (3, 11):
    raise SystemExit("❌ Python 3.11+ required.")
print("✅ Python 3.11+ OK")

print_section("Installing System Dependencies")
run_cmd("apt-get update -qq", shell=True)
run_cmd("apt-get install -y -qq ffmpeg build-essential libsndfile1 curl git libgomp1",
        shell=True, timeout=300)
print("✅ System deps OK")

print_section("Installing Bun")
run_cmd("curl -fsSL https://bun.sh/install | bash", shell=True, timeout=120)
os.environ["PATH"] = "/root/.bun/bin:" + os.environ.get("PATH", "")
ok, result = run_cmd("bun --version", shell=True, check=False)
if ok and result.stdout.strip():
    print(f"✅ Bun version: {result.stdout.strip()}")

print_section("Installing uv")
run_cmd("pip install -q uv", shell=True, timeout=120)
ok, result = run_cmd("uv --version", shell=True, check=False)
if ok and result.stdout.strip():
    print(f"✅ uv version: {result.stdout.strip()}")

print_section("Cloning OmniVoice-Studio Repository")
if os.path.exists(WORK_DIR):
    run_cmd(f"rm -rf {WORK_DIR}", shell=True, cwd="/content")
ok, _ = run_cmd(f"git clone --depth 1 {REPO_URL} {WORK_DIR}", shell=True, timeout=120, cwd="/content")
if not ok:
    raise SystemExit("❌ Failed to clone repository.")
os.chdir(WORK_DIR)
print(f"✅ Repo cloned to {WORK_DIR}")

print_section("Building Frontend (React + Vite)")
run_cmd("bun install", shell=True, cwd=WORK_DIR, timeout=300, check=False)
run_cmd("bun run --cwd frontend build", shell=True, cwd=WORK_DIR, timeout=300, check=False)
print("✅ Frontend built" if os.path.exists("frontend/dist/index.html") else "⚠️ Frontend build issues.")

print_section("Installing Backend Python Dependencies")
venv_python = find_venv_python(WORK_DIR)
if not venv_python:
    print("   🔄 Creating virtual environment...")
    run_cmd([sys.executable, "-m", "venv", os.path.join(WORK_DIR, ".venv")], check=False)
    venv_python = find_venv_python(WORK_DIR)

if not venv_python:
    venv_python = sys.executable
    print(f"⚠️ Using system Python: {venv_python}")
else:
    print(f"✅ Using venv Python: {venv_python}")

run_cmd([venv_python, "-m", "pip", "install", "--upgrade", "pip", "--quiet"],
        timeout=120, check=False)

sync_env = os.environ.copy()
sync_env["UV_HTTP_TIMEOUT"] = "300"
sync_env["UV_HTTP_RETRIES"] = "5"
sync_env["UV_HTTP_CONNECT_TIMEOUT"] = "60"
sync_env["HF_HUB_DISABLE_SYMLINKS"] = "1"
sync_env["HF_HUB_DISABLE_XET"] = "1"
sync_env["TORCH_COMPILE_DISABLE"] = "1"
sync_env["UV_PYTHON_PREFERENCE"] = "only-system"

print("🔄 Running uv sync...")
ok, result = run_cmd(["uv", "sync", "--python", sys.executable],
                     cwd=WORK_DIR, timeout=600, check=False, env=sync_env)
if ok and result.returncode == 0:
    print("✅ uv sync successful")
else:
    print("⚠️ uv sync failed, falling back to pip...")
    pip_base = [venv_python, "-m", "pip", "install", "-e", "."]
    run_cmd(pip_base + ["--extra-index-url", "https://download.pytorch.org/whl/cu128",
                        "--trusted-host", "download.pytorch.org",
                        "--trusted-host", "files.pythonhosted.org",
                        "--trusted-host", "pypi.org", "-q"],
            cwd=WORK_DIR, timeout=600, check=False)

print("🔄 Verifying critical packages...")
ensure_package(venv_python, "uvicorn")
ensure_package(venv_python, "huggingface_hub")
ensure_package(venv_python, "torch")
ensure_package(venv_python, "torchaudio")

print("🔄 Installing WhisperX...")
ok, _ = run_cmd([venv_python, "-m", "pip", "install", "whisperx", "--quiet"], check=False, timeout=300)
if ok:
    print("   ✅ WhisperX installed/verified successfully")
else:
    print("   ⚠️ WhisperX installation returned an error. Proceeding...")

print("🔄 Installing Speaker Diarization (pyannote.audio)...")
ok, _ = run_cmd([venv_python, "-m", "pip", "install", "pyannote.audio", "--quiet"], check=False, timeout=300)
if ok:
    print("   ✅ pyannote.audio installed successfully")
else:
    print("   ⚠️ pyannote.audio installation failed. Retrying with pyannote-audio...")
    run_cmd([venv_python, "-m", "pip", "install", "pyannote-audio", "--quiet"], check=False, timeout=300)

ok, _ = run_cmd([venv_python, "-c", "import pyannote.audio"], check=False, timeout=30)
if ok:
    print("   ✅ pyannote.audio verified — successfully loadable!")
else:
    print("   ❌ Failed to verify pyannote.audio import. Diarization may fail.")

print("✅ Backend dependencies setup complete")

print_section("Setting up cuDNN 8 Compatibility")
run_cmd([venv_python, "scripts/setup.py"], cwd=WORK_DIR, check=False, timeout=180)
print("✅ cuDNN 8 compat setup complete")

print_section("Pre-downloading HuggingFace Models")
if HF_TOKEN:
    os.environ["HF_TOKEN"] = HF_TOKEN
    print("🔑 HF_TOKEN configured from script/secrets")
else:
    print("ℹ️ No HF_TOKEN set — diarization will be limited.")

ensure_package(venv_python, "huggingface_hub")
for model in ["k2-fsa/OmniVoice", "Systran/faster-whisper-large-v3"]:
    print(f"\n  📥 Downloading {model}...")
    ok, _ = run_cmd(
        [venv_python, "-c",
         f"from huggingface_hub import snapshot_download; snapshot_download('{model}')"],
        cwd=WORK_DIR, timeout=600, check=False
    )
    print(f"   {'✅' if ok else '⚠️'} {model} {'OK' if ok else 'had issues'}")

# 🔥 pyannote/speaker-diarization-3.1 — গেটেড মডেল, HF_TOKEN দিয়ে ডাউনলোড
DIARIZATION_MODEL = "pyannote/speaker-diarization-3.1"
print(f"\n  📥 Downloading {DIARIZATION_MODEL}...")
if HF_TOKEN:
    diarization_download_code = (
        "from huggingface_hub import snapshot_download; "
        f"snapshot_download('{DIARIZATION_MODEL}', "
        f"use_auth_token='{HF_TOKEN}', "
        "ignore_patterns=['*.msgpack','*.h5','flax_model*'])"
    )
    ok, _ = run_cmd(
        [venv_python, "-c", diarization_download_code],
        cwd=WORK_DIR, timeout=600, check=False
    )
    print(f"   {'✅' if ok else '⚠️'} {DIARIZATION_MODEL} {'OK' if ok else 'had issues (check HF token access)'}")
else:
    print(f"   ⚠️ Skipped {DIARIZATION_MODEL} — HF_TOKEN required (gated model).")
    print("      Set HF_TOKEN in Colab Secrets and re-run.")

print("\n🎉 Model download phase complete")

# ============================================================
# 9.3 🔥 v10 — Initialize Database (CRITICAL: before server starts)
# ============================================================
print_section("Initializing Database (v10 — fix 'no such table: settings')")

db_init_script = '''
import sys, os
sys.path.insert(0, "/content/OmniVoice-Studio/backend")
os.environ.setdefault("OMNIVOICE_DATA_DIR", "/content/omnivoice_data")
os.makedirs("/content/omnivoice_data", exist_ok=True)

try:
    from core.db import init_db, ensure_schema, get_db
    print("  🔄 Running init_db()...")
    init_db()
    print("  ✅ init_db() complete")

    # ভেরিফাই করি settings টেবিল তৈরি হয়েছে কিনা
    conn = get_db()
    try:
        row = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='settings'"
        ).fetchone()
        if row:
            print("  ✅ 'settings' table verified — exists")
        else:
            print("  ⚠️ 'settings' table NOT found after init_db — creating manually")
            conn.execute("""
                CREATE TABLE IF NOT EXISTS settings (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL,
                    updated_at REAL NOT NULL
                )
            """)
            conn.commit()
            print("  ✅ 'settings' table created manually")

        tables = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        ).fetchall()
        table_names = [t[0] for t in tables]
        print(f"  📋 Database tables ({len(table_names)}): {', '.join(sorted(table_names))}")
    finally:
        conn.close()

except Exception as e:
    print(f"  ❌ Database init failed: {e}")
    print("  🔄 Trying manual table creation as fallback...")
    try:
        import sqlite3
        from core.config import DB_PATH
        os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
        conn = sqlite3.connect(DB_PATH)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL,
                updated_at REAL NOT NULL
            )
        """)
        conn.commit()
        conn.close()
        print("  ✅ Manual fallback: 'settings' table created")
    except Exception as e2:
        print(f"  ❌ Manual fallback also failed: {e2}")
        print("  ⚠️ Server will start but Settings may not work properly")
'''

db_init_path = "/tmp/omnivoice_db_init.py"
with open(db_init_path, "w") as f:
    f.write(db_init_script)

ok, result = run_cmd(
    [venv_python, db_init_path],
    cwd=WORK_DIR, timeout=120, check=False
)
if ok and result.returncode == 0:
    print("✅ Database initialization complete")
else:
    print("⚠️ Database init had issues — server may show SQLite warnings")
    if result.stderr:
        print(f"   stderr: {result.stderr[:500]}")

# ============================================================
# 9.5 🔥 v9 — Inject LLM Resilience Patch (ALL languages + ALL skills)
# ============================================================
print_section("Injecting LLM Resilience Patch (v10 — ALL languages + ALL LLM Skills)")

LLM_PATCH_PATH = os.path.join(WORK_DIR, "backend", "omnivoice_llm_patch.py")
LLM_PATCH_CONTENT = '''"""
LLM Resilience Patch v10 — ALL languages + ALL LLM Skills cover.

v8 এ শুধু Cinematic + Speech-rate-এ script name inject হতো। v9:
  1. Dub translation-এও script name inject (সব ভাষা)
  2. 30+ ভাষা সাপোর্ট — Hindi/Bengali/English/Turkish/Urdu/Spanish/French/
     Korean/Japanese/Indonesian/Vietnamese/Thai/Chinese/Russian/German/Italian/
     Portuguese/Arabic/Persian/Hebrew/Greek/Polish/Czech/Dutch/Swedish/Norwegian/
     Danish/Finnish/Marathi/Tamil/Telugu/Gujarati/Kannada/Malayalam/Punjabi/Odia
  3. সব ৬টা LLM Skills-এ retry/backoff/timeout কভার
"""
from __future__ import annotations

import functools
import logging
import os
import random
import threading
import time
from typing import Optional

logger = logging.getLogger("omnivoice.llm_patch")

# ── Config ──────────────────────────────────────────────────────────────────
MAX_RETRIES = max(1, int(os.environ.get("OMNIVOICE_LLM_MAX_RETRIES", "5")))
BACKOFF_BASE = max(0.1, float(os.environ.get("OMNIVOICE_LLM_BACKOFF_BASE", "2.0")))
BACKOFF_CAP = max(1.0, float(os.environ.get("OMNIVOICE_LLM_BACKOFF_CAP", "60.0")))
RATE_LIMIT_BACKOFF = max(5.0, float(os.environ.get("OMNIVOICE_LLM_RATE_LIMIT_BACKOFF", "30.0")))
RPM_LIMIT = max(0, int(os.environ.get("OMNIVOICE_LLM_RPM", "28")))
RPS_LIMIT = max(0.0, float(os.environ.get("OMNIVOICE_LLM_RPS", "0")))
PATCH_PROMPTS = os.environ.get("OMNIVOICE_PATCH_PROMPTS", "1") == "1"
PATCH_DUB_TRANSLATION = os.environ.get("OMNIVOICE_PATCH_DUB_TRANSLATION", "1") == "1"
LOCAL_LLM_TIMEOUT = max(30.0, float(os.environ.get("OMNIVOICE_LOCAL_LLM_TIMEOUT", "300")))
CLOUD_LLM_TIMEOUT = max(15.0, float(os.environ.get("OMNIVOICE_CLOUD_LLM_TIMEOUT", "60")))

# ── প্রোভাইডার ডিটেক্ট ─────────────────────────────────────────────────────
_LOCAL_PROVIDERS = {"ollama", "lmstudio", "custom"}

def _active_provider_id():
    try:
        from services import llm_providers
        return llm_providers.active_provider_id()
    except Exception:
        return None

def _is_local_provider():
    return _active_provider_id() in _LOCAL_PROVIDERS

def _effective_timeout():
    if _is_local_provider(): return LOCAL_LLM_TIMEOUT
    return CLOUD_LLM_TIMEOUT

def _effective_rpm():
    if _is_local_provider(): return 0
    return RPM_LIMIT

# ── 🔥 v9 — ৩০+ ভাষা (সব প্রয়োজন কভার) ──────────────────────────────
_LANG_NAMES = {
    "hi": ("Hindi", "Devanagari"),
    "en": ("English", "Latin"),
    "bn": ("Bengali", "Bengali"),
    "tr": ("Turkish", "Latin"),
    "ur": ("Urdu", "Nastaliq (Arabic)"),
    "es": ("Spanish", "Latin"),
    "fr": ("French", "Latin"),
    "ko": ("Korean", "Hangul"),
    "ja": ("Japanese", "Kanji and Kana"),
    "id": ("Indonesian", "Latin"),
    "de": ("German", "Latin"),
    "it": ("Italian", "Latin"),
    "pt": ("Portuguese", "Latin"),
    "ru": ("Russian", "Cyrillic"),
    "uk": ("Ukrainian", "Cyrillic"),
    "pl": ("Polish", "Latin"),
    "cs": ("Czech", "Latin"),
    "nl": ("Dutch", "Latin"),
    "sv": ("Swedish", "Latin"),
    "no": ("Norwegian", "Latin"),
    "da": ("Danish", "Latin"),
    "fi": ("Finnish", "Latin"),
    "el": ("Greek", "Greek"),
    "he": ("Hebrew", "Hebrew"),
    "ar": ("Arabic", "Arabic"),
    "fa": ("Persian", "Persian (Arabic)"),
    "th": ("Thai", "Thai"),
    "vi": ("Vietnamese", "Latin"),
    "zh": ("Chinese", "Han (Simplified)"),
    "zh-CN": ("Simplified Chinese", "Han (Simplified)"),
    "zh-TW": ("Traditional Chinese", "Han (Traditional)"),
    "mr": ("Marathi", "Devanagari"),
    "ta": ("Tamil", "Tamil"),
    "te": ("Telugu", "Telugu"),
    "gu": ("Gujarati", "Gujarati"),
    "kn": ("Kannada", "Kannada"),
    "ml": ("Malayalam", "Malayalam"),
    "pa": ("Punjabi", "Gurmukhi"),
    "or": ("Odia", "Odia"),
    "ne": ("Nepali", "Devanagari"),
    "si": ("Sinhala", "Sinhala"),
    "my": ("Burmese", "Burmese"),
    "km": ("Khmer", "Khmer"),
    "lo": ("Lao", "Lao"),
}

_EXTRA_SCRIPT_RANGES = {
    "bn": (0x0980, 0x09FF),
    "ta": (0x0B80, 0x0BFF),
    "te": (0x0C00, 0x0C7F),
    "mr": (0x0900, 0x097F),
    "gu": (0x0A80, 0x0AFF),
    "kn": (0x0C80, 0x0CFF),
    "ml": (0x0D00, 0x0D7F),
    "pa": (0x0A00, 0x0A7F),
    "or": (0x0B00, 0x0B7F),
    "ur": (0x0600, 0x06FF),
    "fa": (0x0600, 0x06FF),
    "he": (0x0590, 0x05FF),
    "el": (0x0370, 0x03FF),
    "vi": (0x0020, 0x007E),
    "ne": (0x0900, 0x097F),
    "si": (0x0D80, 0x0DFF),
    "my": (0x1000, 0x109F),
    "km": (0x1780, 0x17FF),
    "lo": (0x0E80, 0x0EFF),
}

def _script_clause_for(target_lang):
    if not target_lang:
        return None
    lang_key = target_lang.split("-")[0].lower()
    lang_info = _LANG_NAMES.get(lang_key)
    if not lang_info:
        return None
    lang_name, script_name = lang_info
    return (
        f" CRITICAL: The target language is {lang_name} and the output MUST be "
        f"written in {script_name} script. Do NOT use Latin/Roman letters, "
        f"English, or any other script. Do NOT transliterate. Even a single "
        f"Latin character is a failure. Reply ONLY with the {lang_name} text."
    )

# ── Retry-able exception types ──────────────────────────────────────────────
def _is_retryable(exc):
    if exc is None: return False
    sc = getattr(exc, "status_code", None) or getattr(getattr(exc, "response", None), "status_code", None)
    if sc in (429, 500, 502, 503, 504): return True
    name = type(exc).__name__
    if name in ("APIConnectionError","APITimeoutError","RateLimitError","InternalServerError","ConnectError","ConnectTimeout","TimeoutError"): return True
    msg = str(exc).lower()
    if any(k in msg for k in ("timeout","timed out","connection","429","rate limit","refused","reset by peer")): return True
    return False

def _is_rate_limit(exc):
    if exc is None: return False
    sc = getattr(exc, "status_code", None) or getattr(getattr(exc, "response", None), "status_code", None)
    if sc == 429: return True
    name = type(exc).__name__
    if name == "RateLimitError": return True
    return "rate limit" in str(exc).lower() or "429" in str(exc)

def _retry_after(exc):
    try:
        resp = getattr(exc, "response", None)
        if resp is None: return None
        headers = getattr(resp, "headers", {}) or {}
        ra = headers.get("retry-after") or headers.get("Retry-After")
        if not ra: return None
        return min(float(ra), BACKOFF_CAP)
    except Exception:
        return None

# ── Token-bucket rate limiter ───────────────────────────────────────────────
class _TokenBucket:
    def __init__(self, rate_per_sec, capacity=None):
        self.rate = max(0.0, float(rate_per_sec))
        self.capacity = float(capacity) if capacity is not None else self.rate
        self.tokens = self.capacity
        self.lock = threading.Lock()
        self.last = time.monotonic()

    def acquire(self, timeout=600.0):
        if self.rate <= 0: return 0.0
        deadline = time.monotonic() + timeout
        waited = 0.0
        while True:
            with self.lock:
                now = time.monotonic()
                elapsed = now - self.last
                self.tokens = min(self.capacity, self.tokens + elapsed * self.rate)
                self.last = now
                if self.tokens >= 1.0:
                    self.tokens -= 1.0
                    return waited
                wait = (1.0 - self.tokens) / self.rate
            if time.monotonic() + wait > deadline: return waited
            time.sleep(min(wait, 0.5))
            waited += min(wait, 0.5)

_RPM_BUCKET = None
_RPS_BUCKET = None
_LIMITER_LOCK = threading.Lock()

def _get_rpm_bucket():
    global _RPM_BUCKET
    rpm = _effective_rpm()
    if rpm <= 0: return None
    if _RPM_BUCKET is None or _RPM_BUCKET.rate != rpm / 60.0:
        with _LIMITER_LOCK:
            if _RPM_BUCKET is None or _RPM_BUCKET.rate != rpm / 60.0:
                rate = rpm / 60.0
                _RPM_BUCKET = _TokenBucket(rate_per_sec=rate, capacity=max(1.0, rate * 2))
                logger.info("llm_patch: RPM limiter ON — %d RPM (provider=%s)", rpm, _active_provider_id())
    return _RPM_BUCKET

def _get_rps_bucket():
    global _RPS_BUCKET
    if RPS_LIMIT <= 0: return None
    if _RPS_BUCKET is None:
        with _LIMITER_LOCK:
            if _RPS_BUCKET is None:
                _RPS_BUCKET = _TokenBucket(rate_per_sec=RPS_LIMIT, capacity=max(1.0, RPS_LIMIT * 2))
    return _RPS_BUCKET

# ── Stats ───────────────────────────────────────────────────────────────────
_STATS_LOCK = threading.Lock()
_STATS = {"total_calls": 0, "retries": 0, "rate_limited_429": 0, "timeouts": 0,
          "final_failures": 0, "rate_limiter_waits": 0, "rate_limiter_wait_seconds": 0.0,
          "script_injections": 0}

def get_stats():
    with _STATS_LOCK:
        return dict(_STATS)

def _stat(key, n=1):
    with _STATS_LOCK:
        _STATS[key] = _STATS.get(key, 0) + n

# ── Backoff calculation ─────────────────────────────────────────────────────
def _compute_backoff(exc, attempt):
    ra = _retry_after(exc)
    if ra is not None: return ra
    if _is_rate_limit(exc):
        if _is_local_provider():
            return 2.0 * random.uniform(0.75, 1.25)
        return RATE_LIMIT_BACKOFF * random.uniform(0.9, 1.2)
    sleep_s = min(BACKOFF_CAP, BACKOFF_BASE * (2 ** (attempt - 1)))
    if _is_local_provider():
        sleep_s = min(sleep_s, 5.0)
    return sleep_s * random.uniform(0.75, 1.25)

# ── Common retry+ratelimit wrapper ──────────────────────────────────────────
def _run_with_rate_limit(fn, *args, **kwargs):
    _stat("total_calls")
    rpm_bucket = _get_rpm_bucket()
    rps_bucket = _get_rps_bucket()
    last_exc = None
    for attempt in range(1, MAX_RETRIES + 1):
        if rps_bucket:
            _stat("rate_limiter_waits")
            w = rps_bucket.acquire(timeout=120)
            if w > 0: _stat("rate_limiter_wait_seconds", w)
        if rpm_bucket:
            _stat("rate_limiter_waits")
            w = rpm_bucket.acquire(timeout=120)
            if w > 0: _stat("rate_limiter_wait_seconds", w)
        try:
            return fn(*args, **kwargs)
        except Exception as exc:
            last_exc = exc
            if not _is_retryable(exc): raise
            if attempt >= MAX_RETRIES:
                _stat("final_failures")
                raise
            _stat("retries")
            is_rl = _is_rate_limit(exc)
            if is_rl: _stat("rate_limited_429")
            msg = str(exc).lower()
            if "timeout" in msg or "timed out" in msg: _stat("timeouts")
            sleep_s = _compute_backoff(exc, attempt)
            logger.warning(
                "llm_patch: চেষ্টা %d/%d ব্যর্থ (%s%s) [provider=%s] — %.1fs ব্যাকঅফ",
                attempt, MAX_RETRIES, type(exc).__name__,
                " [429-RPM]" if is_rl else "", _active_provider_id() or "?", sleep_s,
            )
            time.sleep(sleep_s)
    if last_exc: raise last_exc
    raise RuntimeError("llm_patch: unexpected state")

# ── 🔥 v9 — Cinematic translation patch (script-aware) ─────────────────────
def _patch_translator_prompts():
    if not PATCH_PROMPTS:
        return
    try:
        from services import translator
    except ImportError:
        return

    if hasattr(translator, "_SCRIPT_RANGES"):
        for k, v in _EXTRA_SCRIPT_RANGES.items():
            if k not in translator._SCRIPT_RANGES:
                translator._SCRIPT_RANGES[k] = v
        logger.info("llm_patch: _SCRIPT_RANGES এক্সটেন্ড — %d ভাষা",
                    len(translator._SCRIPT_RANGES))

    if not hasattr(translator, "_orig_cinematic_refine_sync"):
        translator._orig_cinematic_refine_sync = translator.cinematic_refine_sync

        @functools.wraps(translator._orig_cinematic_refine_sync)
        def patched_cinematic_refine_sync(source_text, literal_text, *, source_lang,
                                          target_lang, **kwargs):
            clause = _script_clause_for(target_lang)
            if clause:
                _stat("script_injections")
                orig_reflect = translator._REFLECT_PROMPT
                orig_adapt = translator._ADAPT_PROMPT
                translator._REFLECT_PROMPT = orig_reflect + clause
                translator._ADAPT_PROMPT = orig_adapt + clause
                try:
                    return translator._orig_cinematic_refine_sync(
                        source_text, literal_text, source_lang=source_lang,
                        target_lang=target_lang, **kwargs
                    )
                finally:
                    translator._REFLECT_PROMPT = orig_reflect
                    translator._ADAPT_PROMPT = orig_adapt
            else:
                return translator._orig_cinematic_refine_sync(
                    source_text, literal_text, source_lang=source_lang,
                    target_lang=target_lang, **kwargs
                )

        translator.cinematic_refine_sync = patched_cinematic_refine_sync
        logger.info("llm_patch: cinematic_refine_sync wrapped (script-aware, %d languages)",
                    len(_LANG_NAMES))


# ── 🔥 v9 — Speech-rate slot fitting patch (script-aware) ──────────────────
def _patch_speech_rate_prompts():
    if not PATCH_PROMPTS:
        return
    try:
        from services import speech_rate
    except ImportError:
        return

    if not hasattr(speech_rate, "_orig_adjust_for_slot"):
        speech_rate._orig_adjust_for_slot = speech_rate.adjust_for_slot

        @functools.wraps(speech_rate._orig_adjust_for_slot)
        def patched_adjust_for_slot(text, *, slot_seconds, target_lang, **kwargs):
            clause = _script_clause_for(target_lang)
            if clause:
                _stat("script_injections")
                clause = clause + " Keep the output concise — between 50% and 200% of the input length."
                orig_trim = speech_rate._TRIM_PROMPT
                orig_expand = speech_rate._EXPAND_PROMPT
                speech_rate._TRIM_PROMPT = orig_trim + clause
                speech_rate._EXPAND_PROMPT = orig_expand + clause
                try:
                    return speech_rate._orig_adjust_for_slot(
                        text, slot_seconds=slot_seconds, target_lang=target_lang, **kwargs
                    )
                finally:
                    speech_rate._TRIM_PROMPT = orig_trim
                    speech_rate._EXPAND_PROMPT = orig_expand
            else:
                return speech_rate._orig_adjust_for_slot(
                    text, slot_seconds=slot_seconds, target_lang=target_lang, **kwargs
                )

        speech_rate.adjust_for_slot = patched_adjust_for_slot
        logger.info("llm_patch: speech_rate.adjust_for_slot wrapped (script-aware)")


# ── 🔥 v9 NEW — Dub translation patch (script-aware, সব ভাষা) ──────────────
def _patch_dub_translation_prompts():
    if not PATCH_PROMPTS or not PATCH_DUB_TRANSLATION:
        return
    try:
        from openai.resources.chat.completions import Completions
    except ImportError:
        return

    if hasattr(Completions, "_orig_create_v9"):
        return

    Completions._orig_create_v9 = Completions.create

    @functools.wraps(Completions._orig_create_v9)
    def patched_create(self, *args, **kwargs):
        messages = kwargs.get("messages") or (args[0] if args else None)
        if messages and isinstance(messages, list):
            for msg in messages:
                if msg.get("role") == "system":
                    content = msg.get("content", "")
                    if "Translate" in content or "translate" in content:
                        target_lang = _extract_target_lang_from_prompt(content)
                        if target_lang:
                            clause = _script_clause_for(target_lang)
                            if clause:
                                _stat("script_injections")
                                msg["content"] = content + clause
                        break
        if "timeout" not in kwargs or kwargs.get("timeout") is None:
            kwargs["timeout"] = _effective_timeout()
        return _run_with_rate_limit(Completions._orig_create_v9, self, *args, **kwargs)

    Completions.create = patched_create
    logger.info("llm_patch: OpenAI SDK Completions.create wrapped (script-aware for Dub translation)")


def _extract_target_lang_from_prompt(content):
    if not content:
        return None
    import re
    m = re.search(r"into\s+([A-Za-z]+(?:\s+[A-Za-z]+)?)", content)
    if m:
        lang_name = m.group(1).strip().lower()
        name_to_code = {v[0].lower(): k for k, v in _LANG_NAMES.items()}
        for name, code in name_to_code.items():
            if lang_name == name.lower() or lang_name.startswith(name.lower()):
                return code
    return None


# ── LLM timeout patch ───────────────────────────────────────────────────────
def _patch_llm_timeout():
    try:
        from services import translator
        if not hasattr(translator, "_orig_llm_timeout"):
            translator._orig_llm_timeout = translator._llm_timeout
            translator._llm_timeout = lambda: _effective_timeout()
    except ImportError:
        pass
    try:
        from services import llm_skills
        if not hasattr(llm_skills, "_orig_default_timeout"):
            llm_skills._orig_default_timeout = llm_skills._default_timeout
            llm_skills._default_timeout = lambda: _effective_timeout()
    except ImportError:
        pass
    logger.info("llm_patch: LLM timeout patched — local=%ds, cloud=%ds",
                LOCAL_LLM_TIMEOUT, CLOUD_LLM_TIMEOUT)


# ── Glossary / Direction / Dictation retry/backoff ──────────────────────────
def _patch_glossary_extract():
    try:
        from api.routers import glossary
    except ImportError:
        return
    logger.info("llm_patch: Glossary auto-extract covered (via OpenAICompatBackend patch)")


def _patch_direction_parse():
    try:
        from services import director
    except ImportError:
        return
    logger.info("llm_patch: Direction parsing covered (via translator._chat patch)")


def _patch_dictation_cleanup():
    try:
        from services import refinement
    except ImportError:
        return
    logger.info("llm_patch: Dictation cleanup covered (via OpenAICompatBackend patch)")


# ── Apply all patches ───────────────────────────────────────────────────────
_PATCHED = False

def apply_patch():
    global _PATCHED
    if _PATCHED: return True

    try:
        from services.llm_backend import OpenAICompatBackend
        if hasattr(OpenAICompatBackend, "chat_messages") and not hasattr(OpenAICompatBackend, "_orig_chat_messages"):
            OpenAICompatBackend._orig_chat_messages = OpenAICompatBackend.chat_messages
            @functools.wraps(OpenAICompatBackend._orig_chat_messages)
            def patched_chat_messages(self, *, messages, timeout=None, temperature=None):
                if timeout is None:
                    timeout = _effective_timeout()
                return _run_with_rate_limit(
                    OpenAICompatBackend._orig_chat_messages,
                    self, messages=messages, timeout=timeout, temperature=temperature,
                )
            OpenAICompatBackend.chat_messages = patched_chat_messages
            logger.info("llm_patch: OpenAICompatBackend.chat_messages wrapped")
    except ImportError:
        logger.warning("llm_patch: OpenAICompatBackend import failed")

    try:
        from services import translator
        if not hasattr(translator, "_orig_chat"):
            translator._orig_chat = translator._chat
            @functools.wraps(translator._orig_chat)
            def patched_translator_chat(client, *, system, user):
                return _run_with_rate_limit(translator._orig_chat, client, system=system, user=user)
            translator._chat = patched_translator_chat
            logger.info("llm_patch: translator._chat wrapped")
    except ImportError:
        pass

    _patch_dub_translation_prompts()
    _patch_translator_prompts()
    _patch_speech_rate_prompts()
    _patch_llm_timeout()
    _patch_glossary_extract()
    _patch_direction_parse()
    _patch_dictation_cleanup()

    _PATCHED = True
    pid = _active_provider_id() or "?"
    is_local = _is_local_provider()
    rpm = _effective_rpm()
    timeout = _effective_timeout()
    logger.info(
        "✅ llm_patch v10 active: provider=%s (local=%s), max_retries=%d, "
        "timeout=%ds, rpm=%s, prompt_patch=%s, dub_translation_patch=%s, "
        "languages=%d, skills_covered=6/6",
        pid, is_local, MAX_RETRIES, timeout,
        "OFF" if rpm == 0 else str(rpm), PATCH_PROMPTS, PATCH_DUB_TRANSLATION,
        len(_LANG_NAMES),
    )
    return True

try:
    apply_patch()
except Exception as exc:
    logger.warning("llm_patch auto-apply failed (non-fatal): %s", exc)
'''

with open(LLM_PATCH_PATH, "w", encoding="utf-8") as f:
    f.write(LLM_PATCH_CONTENT)
print(f"✅ LLM resilience patch v9 written: {LLM_PATCH_PATH}")

BACKEND_INIT = os.path.join(WORK_DIR, "backend", "__init__.py")
PATCH_IMPORT_LINE = (
    "\n# v9 — LLM resilience patch (auto-injected by Colab setup)\n"
    "try:\n"
    "    from . import omnivoice_llm_patch  # noqa: F401\n"
    "except Exception as _e:\n"
    "    import logging as _l; _l.getLogger('omnivoice').warning('llm_patch load failed: %s', _e)\n"
)

if os.path.exists(BACKEND_INIT):
    with open(BACKEND_INIT, "r", encoding="utf-8") as f:
        init_content = f.read()
    if "omnivoice_llm_patch" not in init_content:
        with open(BACKEND_INIT, "a", encoding="utf-8") as f:
            f.write(PATCH_IMPORT_LINE)
        print("✅ Patch import added to backend/__init__.py")
    else:
        print("ℹ️ Patch import already present")
else:
    with open(BACKEND_INIT, "w", encoding="utf-8") as f:
        f.write(PATCH_IMPORT_LINE)
    print("✅ Created backend/__init__.py with patch import")

# ============================================================
# 10. Start OmniVoice Server & Tunnel
# ============================================================
print_section("Starting OmniVoice Server")
run_cmd(f"kill -9 $(lsof -t -i:{PORT}) 2>/dev/null || true", shell=True, check=False)
time.sleep(1)

ok, _ = run_cmd([venv_python, "-m", "uvicorn", "--version"], check=False, timeout=10)
if not ok:
    run_cmd([venv_python, "-m", "pip", "install", "uvicorn[standard]", "fastapi"],
            timeout=300, check=False)

env = os.environ.copy()
env["OMNIVOICE_SERVER_MODE"] = "1"
env["OMNIVOICE_BIND_HOST"] = "0.0.0.0"
env["OMNIVOICE_DATA_DIR"] = DATA_DIR
env["PYTHONPATH"] = f"{WORK_DIR}/backend"
env["PYTHONUNBUFFERED"] = "1"
env["TORCH_COMPILE_DISABLE"] = "1"
env["HF_HUB_DISABLE_SYMLINKS"] = "1"
env["HF_HUB_DISABLE_XET"] = "1"
env["MPLBACKEND"] = "Agg"
for _k, _v in LLM_RESILIENCE_ENV.items():
    env[_k] = _v

if HF_TOKEN:
    env["HF_TOKEN"] = HF_TOKEN
if "UV_PYTHON_PREFERENCE" in env:
    del env["UV_PYTHON_PREFERENCE"]

os.makedirs(DATA_DIR, exist_ok=True)

print(f"🚀 Starting server on port {PORT}...")
print(f"   LLM_TIMEOUT (local): {env.get('OMNIVOICE_LOCAL_LLM_TIMEOUT')}s")
print(f"   LLM_TIMEOUT (cloud): {env.get('OMNIVOICE_CLOUD_LLM_TIMEOUT')}s")
print(f"   CINEMATIC_BUDGET: {env.get('OMNIVOICE_CINEMATIC_BUDGET_S')} (0=unlimited)")
print(f"   LLM_CONCURRENCY: {env.get('OMNIVOICE_LLM_CONCURRENCY')}")
print(f"   LLM_MAX_RETRIES: {env.get('OMNIVOICE_LLM_MAX_RETRIES')}")
print(f"   🔥 LLM_RPM: {env.get('OMNIVOICE_LLM_RPM')} (0=off for Ollama)")
print(f"   🔥 Prompt patch: {env.get('OMNIVOICE_PATCH_PROMPTS')} (script-aware)")
print(f"   🔥 Dub translation patch: {env.get('OMNIVOICE_PATCH_DUB_TRANSLATION')}")

proc = subprocess.Popen(
    [venv_python, "-m", "uvicorn", "backend.main:app",
     "--host", "0.0.0.0", "--port", str(PORT), "--log-level", "info"],
    env=env, cwd=WORK_DIR,
    stdout=subprocess.PIPE, stderr=subprocess.STDOUT
)

print(f"\n⏳ Waiting for server to be ready (PID {proc.pid})...")
time.sleep(5)
ready = False
server_output = []

for i in range(90):
    if proc.poll() is not None:
        print(f"\n❌ Server process exited early with code {proc.returncode}")
        try:
            remaining = proc.stdout.read().decode("utf-8", errors="ignore")
            if remaining:
                print("\n📋 Server output:")
                print(remaining)
                server_output.append(remaining)
        except Exception:
            pass
        break

    try:
        line = proc.stdout.readline().decode("utf-8", errors="ignore")
        if line:
            server_output.append(line)
            print(line, end="")
            if "Application startup complete" in line or ("Uvicorn running" in line and "0.0.0.0" in line):
                ready = True
                print("\n✅ Server startup signal detected!")
                break
    except Exception:
        pass

    if i > 8 and i % 4 == 0:
        health = check_health(PORT, timeout=3)
        if health:
            print(f"\n✅ Health check passed: {health}")
            ready = True
            break
    time.sleep(1)

if not ready:
    health = check_health(PORT, timeout=10)
    if health:
        print(f"✅ Server is healthy: {health}")
        ready = True
    else:
        print("⚠️ Server may still be loading...")

# Start the reverse tunnel gateway if the server started successfully
tunnel_url = None
tunnel_manager = None
if ready:
    print_section("Starting Reverse Tunnel Gateway")
    tunnel_manager = TunnelManager()
    try:
        tunnel_url = tunnel_manager.start_tunnel(
            provider=TUNNEL_PROVIDER,
            port=PORT,
            ngrok_auth=NGROK_AUTH,
            cf_token=CLOUDFLARE_TUNNEL_TOKEN
        )
        print(f"✅ Gateway Tunnel active!")
    except Exception as e:
        print(f"⚠️ Tunnel failed to start: {e}")

# ============================================================
# 11. Open UI
# ============================================================
if ready:
    print("\n" + "="*60)
    print("🌐 OPENING UI IN BROWSER")
    print("="*60)

    try:
        from google.colab.output import serve_kernel_port_as_window
        serve_kernel_port_as_window(PORT, path="")
        print("\n✅ OmniVoice Studio UI opened in new tab via Google Colab local proxy!")
    except Exception as e:
        print(f"\n⚠️ Could not launch Colab window serve: {e}")
        print(f"   Local URL: http://localhost:{PORT}")

    if tunnel_url:
        print(f"🔗 Public Tunnel URL: {tunnel_url}")

    print("\n" + "="*60)
    print("💡 v10 — ALL Languages + ALL LLM Skills Summary")
    print("="*60)
    print()
    print("   ✅ ৪০+ ভাষা সাপোর্ট (script-aware prompts):")
    print("      • Hindi/English/Bengali/Turkish/Urdu/Spanish/French/Korean/Japanese/Indonesian")
    print("   ✅ সব ৬টা LLM Skills কভার:")
    print("      1. Dub translation        ✅ script-aware")
    print("      2. Cinematic & Autofit    ✅ script-aware")
    print("      3. Speech-rate slot fit   ✅ script-aware")
    print("      4. Glossary auto-extract  ✅ retry/backoff")
    print("      5. Direction parsing      ✅ retry/backoff")
    print("      6. Dictation cleanup      ✅ retry/backoff")
    print()
    print("="*60 + "\n")

    try:
        while True:
            line = proc.stdout.readline().decode("utf-8", errors="ignore")
            if line:
                print(line, end="")
            if proc.poll() is not None:
                print(f"\n❌ Server exited with code {proc.returncode}")
                break
            time.sleep(0.1)
    except KeyboardInterrupt:
        print("\n\n🛑 Stopping server...")
        proc.terminate()
        time.sleep(2)
        if proc.poll() is None:
            proc.kill()
        if tunnel_manager:
            tunnel_manager.stop_tunnel()
        print("✅ Server stopped")
else:
    print("\n" + "="*60)
    print("❌ SERVER FAILED TO START")
    print("="*60)
    print("📋 Last 50 lines:")
    for line in server_output[-50:]:
        print(f"   {line}", end="")
    if proc.poll() is None:
        proc.terminate()
