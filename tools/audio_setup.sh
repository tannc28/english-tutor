#!/bin/bash
# Cài Piper TTS + tải 3 giọng tiếng Anh vào /root/piper (chạy 1 lần mỗi container mới).
set -e
pip install -q piper-tts onnxruntime
mkdir -p /root/piper
for v in en_GB/alan/medium/en_GB-alan-medium en_GB/alba/medium/en_GB-alba-medium en_US/lessac/medium/en_US-lessac-medium; do
  n=$(basename $v)
  for e in onnx onnx.json; do
    [ -s /root/piper/$n.$e ] && [ $(stat -c%s /root/piper/$n.$e) -gt 1000 ] || curl -sSL -o /root/piper/$n.$e https://huggingface.co/rhasspy/piper-voices/resolve/main/en/$v.$e
  done
done
echo "Piper ready"
