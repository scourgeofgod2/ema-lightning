"""Local web UI for EMA Lightning. Run: python web/server.py"""
import base64
import io
import json
import os
import sys
import time
import traceback
import wave
from collections import deque
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from ema_lightning import EMA

ROOT = Path(__file__).parent
LOGS = deque(maxlen=300)
tts = EMA()


def log(line):
    stamp = time.strftime("%H:%M:%S")
    entry = f"{stamp}  {line}"
    LOGS.append(entry)
    print(entry, flush=True)


def wav_bytes(audio, sample_rate):
    pcm = (audio.clip(-1, 1) * 32767).astype("<i2")
    buf = io.BytesIO()
    with wave.open(buf, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(sample_rate)
        w.writeframes(pcm.tobytes())
    return buf.getvalue()


class Handler(BaseHTTPRequestHandler):
    def _send(self, code, body, content_type):
        data = body if isinstance(body, bytes) else body.encode()
        self.send_response(code)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        try:
            self.wfile.write(data)
        except (BrokenPipeError, ConnectionResetError):
            log(f"istemci bağlantıyı kesti ({self.path})")

    def do_GET(self):
        path = self.path.split("?")[0]
        if path == "/health":
            self._send(200, "ok", "text/plain")
            return
        if path == "/api/logs":
            self._send(200, json.dumps(list(LOGS)), "application/json")
            return
        if path != "/":
            self._send(404, "not found", "text/plain")
            return
        self._send(200, (ROOT / "index.html").read_bytes(), "text/html; charset=utf-8")

    def do_POST(self):
        if self.path != "/api/say":
            self._send(404, "not found", "text/plain")
            return
        try:
            req = json.loads(self.rfile.read(int(self.headers.get("Content-Length", 0))) or b"{}")
            text = str(req.get("text", "")).strip()
            if not text:
                raise ValueError("Metin boş olamaz.")
            if len(text) > 2000:
                raise ValueError("Metin en fazla 2000 karakter olabilir.")
            speed = float(req.get("speed", 1.0))
            seed = req.get("seed")
            seed = int(seed) if seed not in (None, "") else None
            speech = tts.say(text, speed=speed, seed=seed)
        except (ValueError, TypeError, json.JSONDecodeError) as e:
            log(f"HATA /api/say: {e}")
            self._send(400, json.dumps({"error": str(e)}), "application/json")
            return
        except Exception:
            log("HATA /api/say:\n" + traceback.format_exc().rstrip())
            self._send(500, json.dumps({"error": "Sunucu hatası, ayrıntı loglarda."}), "application/json")
            return
        log(f"/api/say {len(text)} karakter, {speech.duration:.2f} sn, seed {speech.seed}")
        payload = {
            "wav": base64.b64encode(wav_bytes(speech.audio, speech.sample_rate)).decode(),
            "duration": round(speech.duration, 3),
            "sample_rate": speech.sample_rate,
            "seed": speech.seed,
            "words": [{"text": w.text, "start": round(w.start, 3), "end": round(w.end, 3)} for w in speech.words],
        }
        self._send(200, json.dumps(payload), "application/json")

    def log_message(self, fmt, *args):
        log(f"{self.address_string()} {fmt % args}")


if __name__ == "__main__":
    port = int(os.environ.get("PORT", "8000"))
    log(f"EMA Lightning UI: http://0.0.0.0:{port}")
    log(f"python {sys.version.split()[0]}, EMA_WEIGHTS={os.environ.get('EMA_WEIGHTS', '-')}")
    ThreadingHTTPServer(("0.0.0.0", port), Handler).serve_forever()
