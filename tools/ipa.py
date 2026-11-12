#!/usr/bin/env python3
"""Phiên âm IPA kiểu từ điển (Cambridge/Oxford) từ espeak-ng (mã nguồn mở, offline).

ipa("umbrella") → "/ʌmˈbrelə/"   ipa("flat") → "/flæt/"   ipa("flat", "us") → "/flæt/"
- Mỗi từ phiên âm riêng; từ 1 âm tiết bỏ dấu trọng âm (như từ điển).
- Dời dấu trọng âm của espeak (đặt trước nguyên âm) về đầu âm tiết theo các cụm phụ âm đầu hợp lệ của tiếng Anh.
- ɹ→r, UK 'a'→æ, ɐ→ə, ɛ→e (kiểu Cambridge), bỏ ký hiệu nối.
Dùng: python3 tools/ipa.py word… [--us]
"""
import re, subprocess, sys
V = "aeiouæɑɒɔəɜɪʊʌɛɐ"
ONSETS = {"pl","bl","kl","gl","ɡl","pr","br","tr","dr","kr","gr","ɡr","fr","θr","ʃr","fl","sl","sp","st","sk","sm","sn","sw","spl","spr","str","skr","skw","tw","dw","kw","gw","ɡw","θw","sf","pj","bj","tj","dj","kj","ɡj","mj","nj","fj","vj","hj","lj","sj"}
CONS = "pbtdkɡgfvθðszʃʒhmnŋlrjwʧʤ"

def _norm(s, acc):
    s = s.replace("ɹ", "r").replace("ɐ", "ə").replace("͡", "").replace("ː", "ː").replace("ɚ", "ər").replace("ɝ", "ɜːr")
    s = s.replace("ɾ", "t") if acc == "us" else s
    if acc == "uk":
        s = re.sub(r"a(?![ɪʊə])", "æ", s)
    s = s.replace("ɛ", "e")
    return s

def _fix_stress(w):
    out = list(w)
    for i, ch in enumerate(w):
        if ch not in "ˈˌ": continue
        j = i  # dời trái qua phụ âm sao cho cụm còn lại là onset hợp lệ
        k = i
        while k > 0 and w[k-1] in CONS: k -= 1
        cluster = w[k:i]
        best = i
        for start in range(k, i):
            c = w[start:i]
            if len(c) == 1 or c in ONSETS: best = start; break
        if best != i:
            seg = w[best:i]
            w = w[:best] + ch + seg + w[i+1:]
            return _fix_stress_rest(w, best + 1)
    return w

def _fix_stress_rest(w, frm):
    head, tail = w[:frm], w[frm:]
    return head + _fix_stress(tail)

def _syllables(w): return len(re.findall(r"(?:aɪ|aʊ|eɪ|əʊ|oʊ|ɔɪ|ɪə|eə|ʊə|[" + V + "])ː?", w))

def word_ipa(word, acc="uk"):
    v = "en-gb" if acc == "uk" else "en-us"
    raw = subprocess.run(["espeak-ng", "-q", "--ipa", "-v", v, word], capture_output=True, text=True).stdout.strip()
    raw = raw.replace("ˈ", "ˈ").replace(" ", "")
    w = _norm(raw, acc)
    w = _fix_stress(w)
    w = re.sub(r"ŋ([ˈˌ])([kɡg])", r"n\1\2", w)  # con'cur: espeak đồng hoá n→ŋ qua ranh giới âm tiết
    if _syllables(w) <= 1: w = w.replace("ˈ", "").replace("ˌ", "")
    return w

WEAK = {"a": "ə", "an": "ən", "the": "ðə", "to": "tə", "of": "əv", "and": "ənd", "for": "fə", "at": "ət", "be": "bi", "some": "səm", "from": "frəm", "was": "wəz", "can": "kən", "your": "jə", "you": "jə", "than": "ðən", "as": "əz", "that": "ðət"}
def ipa(text, acc="uk"):
    t = re.sub(r"\bsb\b", "somebody", re.sub(r"\bsth\b", "something", text))
    t = re.sub(r"\+\s*V-ing|\(.*?\)|…|\.\.\.", " ", t)
    words = re.findall(r"[A-Za-z']+", t)
    if not words: return ""
    out, i = [], 0
    while i < len(words):
        w = words[i].lower()
        if w == "used" and i + 1 < len(words) and words[i+1].lower() == "to":  # used to = /juːst tə/
            out += ["juːst", "tə"]; i += 2; continue
        out.append(WEAK[w] if len(words) > 1 and w in WEAK else word_ipa(words[i], acc)); i += 1
    if acc == "us": out = [x.replace("fə", "fər") if x == "fə" else x for x in out]
    return "/" + " ".join(out) + "/"

if __name__ == "__main__":
    a = [x for x in sys.argv[1:] if x != "--us"]; acc = "us" if "--us" in sys.argv else "uk"
    for t in a: print(t, ipa(t, acc))
