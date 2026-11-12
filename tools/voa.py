#!/usr/bin/env python3
"""Lấy bài nghe từ VOA Learning English (PUBLIC DOMAIN – nội dung của chính phủ Mỹ; ảnh AP/Reuters thì không, nên KHÔNG lấy ảnh).
VOA Learning English ngừng cập nhật từ 3/2025 nhưng kho bài cũ còn nguyên – chọn bài chủ đề phổ thông, không thời sự.

  python3 tools/voa.py list <zone> [<zone>…]   # liệt kê bài: 955 Health & Lifestyle · 986 Arts · 1579 Science · 3521 As It Is · 1581 American Stories · 987 Words and Their Stories · 5535 Ask a Teacher
  python3 tools/voa.py get <url> <id>          # tải MP3 (64kbps) → data/audio/voa/<id>.mp3 + lời & từ vựng → data/sources/voa/<id>.json
Sau đó gia sư soạn bài nghe data/lessons/<id>.json (Learn từ vựng → nghe 3 vòng → câu hỏi) – xem web/README "Bài nghe VOA".
"""
import html, json, os, re, subprocess, sys, urllib.request
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BASE = "https://learningenglish.voanews.com"
UA = {"User-Agent": "Mozilla/5.0 (english-tutor; personal study)"}

def fetch(url):
    with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=40) as r:
        return r.read().decode("utf-8", "ignore")

def clean(s):
    t = html.unescape(re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", s))).strip()
    t = re.sub(r"\s+([.,;:!?’”)])", r"\1", t); t = re.sub(r"([“(])\s+", r"\1", t)
    return t

def list_zone(z):
    h = fetch(f"{BASE}/z/{z}")
    out = []
    for m in re.finditer(r'href="(/a/[^"]+\.html)"[^>]*>\s*(?:<[^>]+>\s*)*([^<]{12,140})<', h):
        u, t = m.group(1), clean(m.group(2))
        if u not in [x[0] for x in out] and not re.match(r"^\w+ \d{1,2}, 20\d\d$", t): out.append((u, t))
    return out

def get(url, lid):
    url = url if url.startswith("http") else BASE + url
    h = fetch(url)
    title = clean((re.findall(r"<title>(.*?)</title>", h) or [""])[0])
    date = (re.findall(r'"datePublished":"([^"]+)"', h) or [""])[0][:10]
    mp3s = [u for u in dict.fromkeys(re.findall(r'https://voa-audio[^"\'\s]+?\.mp3', h)) if not u.endswith("_hq.mp3")]
    level = (re.findall(r"(Level \d)", h) or [""])[-1]
    if re.search(r"Associated Press|Reuters|\bAFP\b|Agence France", h):
        print(f"SKIP {lid}: bài có nguồn AP/Reuters/AFP – không chắc là public domain"); return None
    parts = re.split(r"<h2[^>]*>\s*Words in This Story\s*</h2>", h, flags=re.I)
    h_story, h_words = parts[0], (parts[1] if len(parts) > 1 else "")
    words = []
    for raw in re.findall(r"<p[^>]*>(.*?)</p>", h_words, re.S)[:3]:
        for piece in re.split(r"<br\s*/?>", raw):
            m = re.match(r"\s*<strong>(.*?)</strong>\s*(?:<em>)?\s*[–—-]\s*([a-z]+\.)?\s*(?:</em>)?(.*)", piece, re.S)
            if m: words.append({"w": clean(m.group(1)), "pos": (m.group(2) or "").strip("."), "def": clean(m.group(3))})
    h = h_story
    paras = []
    for raw in re.findall(r"<p[^>]*>(.*?)</p>", h, re.S):   # 1 đoạn có thể chứa nhiều dòng <br> (danh sách từ)
        for piece in re.split(r"<br\s*/?>", raw):
            p = clean(piece)
            if len(p) > 2: paras.append(p)
    paras = [p for p in paras if len(p) > 25 or re.search(r"Words in This Story", p, re.I)]
    story = [p for p in paras if not re.match(r"^_+$", p) and "No media source" not in p and not re.search(r"\b(video|Click here|Learning English Facebook)\b", p)]
    rest = []
    for p in story:  # trang không có tiêu đề "Words in This Story": dòng dạng "bud –n. …" là từ vựng
        m = re.match(r"^([\w'’ ,()-]{2,50}?)\s*[–—-]\s*(n|v|adj|adv|phrase|idiom|prep|conj)\.\s*(.+)$", p)
        if m: words.append({"w": m.group(1).strip(), "pos": m.group(2), "def": m.group(3).strip()})
        else: rest.append(p)
    story = rest
    # bỏ dòng ký tên/biên tập ở cuối
    story = [p for p in story if not re.search(r"(adapted (it|this story) for|wrote this story|was the editor|for Learning English|Copyright|Comments section|Learning English Facebook)", p, re.I)]
    text = "\n\n".join(story)
    os.makedirs(os.path.join(ROOT, "data", "audio", "voa"), exist_ok=True); os.makedirs(os.path.join(ROOT, "data", "sources", "voa"), exist_ok=True)
    mp3 = os.path.join(ROOT, "data", "audio", "voa", f"{lid}.mp3")
    if mp3s and not os.path.exists(mp3):
        with urllib.request.urlopen(urllib.request.Request(mp3s[0], headers=UA), timeout=120) as r, open(mp3, "wb") as f: f.write(r.read())
    dur = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", mp3], capture_output=True, text=True).stdout or 0) if os.path.exists(mp3) else 0
    n = len(text.split())
    meta = {"id": lid, "title": title, "url": url, "date": date, "level": level, "audio": f"data/audio/voa/{lid}.mp3", "minutes": round(dur / 60, 1), "words": n,
            "wpm": round(n / (dur / 60)) if dur else None, "license": "VOA Learning English – public domain (U.S. government work)", "text": text, "vocab": words}
    json.dump(meta, open(os.path.join(ROOT, "data", "sources", "voa", f"{lid}.json"), "w"), ensure_ascii=False, indent=1)
    print(f"{lid}: {title} · {level} · {meta['minutes']} min · {n} words · {meta['wpm']} wpm · {len(words)} vocab")
    return meta

if __name__ == "__main__":
    a = sys.argv[1:]
    if a[:1] == ["list"]:
        for z in a[1:]:
            for u, t in list_zone(z): print(z, u, "|", t)
    elif a[:1] == ["get"]: get(a[1], a[2])
    else: print(__doc__)
