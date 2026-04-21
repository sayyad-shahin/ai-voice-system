"""
translator.py — Auto-detect input language, translate to target.
Uses concurrent chunks for speed on long texts.
"""

import re, time
from concurrent.futures import ThreadPoolExecutor, as_completed
from deep_translator import GoogleTranslator

_MAX_CHARS   = 4800
_MAX_WORKERS = 4
_RETRY_WAIT  = 0.5


def _split(text):
    if len(text) <= _MAX_CHARS:
        return [text]
    parts = re.split(r'(?<=[.!?।\?\!])\s+', text)
    chunks, cur = [], ""
    for part in parts:
        if len(cur) + len(part) + 1 > _MAX_CHARS:
            if cur: chunks.append(cur.strip())
            cur = part
        else:
            cur = (cur + " " + part).strip() if cur else part
    if cur: chunks.append(cur.strip())
    return chunks or [text]


def _translate_one(chunk, target, retries=2):
    for attempt in range(retries + 1):
        try:
            result = GoogleTranslator(source="auto", target=target).translate(chunk)
            if result and result.strip():
                return result.strip()
        except Exception as e:
            print(f"[Translator] attempt {attempt+1}: {e}")
            if attempt < retries:
                time.sleep(_RETRY_WAIT * (attempt + 1))

    # Two-hop fallback via English
    if target != "en":
        try:
            en = GoogleTranslator(source="auto", target="en").translate(chunk)
            if en:
                final = GoogleTranslator(source="en", target=target).translate(en)
                if final and final.strip():
                    return final.strip()
        except Exception as e:
            print(f"[Translator] two-hop failed: {e}")

    return chunk


def translate(text, target_lang):
    if not text or not text.strip():
        return text
    text   = text.strip()
    chunks = _split(text)

    if len(chunks) == 1:
        return _translate_one(chunks[0], target_lang)

    results = {}
    with ThreadPoolExecutor(max_workers=_MAX_WORKERS) as pool:
        future_map = {
            pool.submit(_translate_one, chunk, target_lang): idx
            for idx, chunk in enumerate(chunks)
        }
        for future in as_completed(future_map):
            idx = future_map[future]
            try:
                results[idx] = future.result()
            except Exception as e:
                print(f"[Translator] chunk {idx} error: {e}")
                results[idx] = chunks[idx]

    return " ".join(results[i] for i in range(len(chunks)))