"""
translator.py — Fine-tuned translation
========================================
Key improvements for accuracy:
- source="auto" always (Google detects correctly)
- Sentence-boundary splitting preserves meaning
- Parallel chunks for speed on long text
- Two-hop fallback (via English) for rare failures
- Cleans up extra whitespace in output
"""

import re, time
from concurrent.futures import ThreadPoolExecutor, as_completed
from deep_translator import GoogleTranslator

_MAX_CHARS   = 4800
_MAX_WORKERS = 4
_RETRY_WAIT  = 0.5

# Languages that need special handling for script detection
_INDIC = {"hi","mr","ta","te","gu","bn","kn"}


def _clean(text: str) -> str:
    """Remove extra whitespace and normalize punctuation spacing."""
    text = re.sub(r' +', ' ', text)
    text = re.sub(r' ([.,!?;:])', r'\1', text)
    return text.strip()


def _split(text: str) -> list:
    if len(text) <= _MAX_CHARS:
        return [text]
    # Split on sentence boundaries
    parts = re.split(r'(?<=[.!?।\?\!।])\s+', text)
    chunks, cur = [], ""
    for part in parts:
        if len(cur) + len(part) + 1 > _MAX_CHARS:
            if cur: chunks.append(cur.strip())
            cur = part
        else:
            cur = (cur + " " + part).strip() if cur else part
    if cur: chunks.append(cur.strip())
    return chunks or [text]


def _translate_one(chunk: str, target: str, retries: int = 2) -> str:
    for attempt in range(retries + 1):
        try:
            result = GoogleTranslator(source="auto", target=target).translate(chunk)
            if result and result.strip():
                return _clean(result)
        except Exception as e:
            print(f"[Translator] attempt {attempt+1} error: {e}")
            if attempt < retries:
                time.sleep(_RETRY_WAIT * (attempt + 1))

    # Two-hop fallback via English for Indic languages
    if target in _INDIC:
        try:
            print("[Translator] Trying two-hop fallback via English…")
            en = GoogleTranslator(source="auto", target="en").translate(chunk)
            if en and en.strip():
                final = GoogleTranslator(source="en", target=target).translate(en.strip())
                if final and final.strip():
                    return _clean(final)
        except Exception as e:
            print(f"[Translator] Two-hop failed: {e}")

    # Return original text if all attempts fail
    return chunk


def translate(text: str, target_lang: str) -> str:
    """
    Translate text to target_lang.
    Auto-detects source language.
    Handles any length via parallel chunks.
    """
    if not text or not text.strip():
        return text

    text   = text.strip()
    chunks = _split(text)

    if len(chunks) == 1:
        result = _translate_one(chunks[0], target_lang)
        print(f"[Translator] '{text[:50]}' → '{result[:50]}' ({target_lang})")
        return result

    # Parallel translation for long text
    results = {}
    with ThreadPoolExecutor(max_workers=_MAX_WORKERS) as pool:
        futures = {pool.submit(_translate_one, chunk, target_lang): i
                   for i, chunk in enumerate(chunks)}
        for future in as_completed(futures):
            i = futures[future]
            try:
                results[i] = future.result()
            except Exception as e:
                print(f"[Translator] chunk {i} error: {e}")
                results[i] = chunks[i]

    return " ".join(results[i] for i in range(len(chunks)))