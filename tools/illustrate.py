#!/usr/bin/env python3
"""Vẽ minh hoạ CỤ THỂ (cảnh truyện, ảnh bìa, từ chỉ vật/cảnh) bằng SDXL-Turbo (mã nguồn mở, CPU bfloat16 ~7 giây/ảnh).
Từ TRỪU TƯỢNG (từ nối, idiom, cụm ngữ pháp) KHÔNG vẽ bằng công cụ này → Haiku vẽ SVG theo câu ví dụ (web/README "Minh hoạ").

Dùng:  python3 tools/illustrate.py spec.json
spec.json = [{"out": "data/img/w1/cafe.webp", "prompt": "Nam sitting in a small cafe…", "w": 512, "h": 384}, …]
- Bỏ qua ảnh đã có (xoá file để vẽ lại). Thêm "seed" để cố định kết quả.
- Phong cách chung (STYLE) giữ mọi ảnh cùng một kiểu tranh. Nhân vật cố định: xem CAST, viết {nam}, {margaret}… trong prompt.
Cài: pip install torch --index-url https://download.pytorch.org/whl/cpu && pip install diffusers transformers accelerate pillow (SDXL-Turbo ~7GB, cần ~8GB RAM)
"""
import json, os, sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STYLE = "children's picture book illustration, clean flat colors, soft lighting, simple background, no text"
CAST = {
    "nam": "a young Vietnamese man with short black hair, white shirt",
    "margaret": "a friendly old British woman with grey curly hair and a green cardigan",
    "jess": "a young woman with short red hair and an apron",
    "claire": "a woman in her forties with grey glasses and a blue blazer",
    "patel": "a middle-aged Indian man with a beard and a brown jacket",
}
def main(spec):
    import torch
    from diffusers import AutoPipelineForText2Image
    items = [x for x in json.load(open(spec)) if not os.path.exists(os.path.join(ROOT, x["out"]))]
    if not items: print("nothing to draw"); return
    torch.set_num_threads(os.cpu_count() or 4)
    pipe = AutoPipelineForText2Image.from_pretrained("stabilityai/sdxl-turbo", torch_dtype=torch.bfloat16, variant="fp16")
    for x in items:
        prompt = x["prompt"].format(**CAST) + ", " + STYLE
        g = torch.Generator().manual_seed(int(x.get("seed", 7)))
        im = pipe(prompt=prompt, negative_prompt="text, letters, watermark, ugly, deformed", num_inference_steps=x.get("steps", 2),
                  guidance_scale=0.0, width=x.get("w", 512), height=x.get("h", 384), generator=g).images[0]
        out = os.path.join(ROOT, x["out"]); os.makedirs(os.path.dirname(out), exist_ok=True)
        im.convert("RGB").save(out, "WEBP", quality=80)
        print("✓", x["out"], os.path.getsize(out)//1024, "KB")
if __name__ == "__main__":
    main(sys.argv[1])
