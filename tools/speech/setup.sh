#!/usr/bin/env bash
# Cài bộ chấm phát âm khi cần (không cài sẵn mỗi phiên vì nặng ~3 GB kể cả model).
# Dùng: bash tools/speech/setup.sh   → tạo venv ở ~/.speechenv
set -e
command -v espeak-ng >/dev/null || { sudo apt-get update -q >/dev/null; sudo apt-get install -y -q espeak-ng >/dev/null; }
command -v ffmpeg >/dev/null || sudo apt-get install -y -q ffmpeg >/dev/null
V="$HOME/.speechenv"
[ -x "$V/bin/python" ] || python3 -m venv "$V"
"$V/bin/pip" install -q --upgrade pip
"$V/bin/pip" install -q faster-whisper praat-parselmouth soundfile phonemizer transformers
"$V/bin/pip" install -q torch --index-url https://download.pytorch.org/whl/cpu
echo "OK – chạy: $V/bin/python tools/speech/assess.py <audio> \"<câu mẫu>\""
