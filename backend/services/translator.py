import re, time
from concurrent.futures import ThreadPoolExecutor, as_completed
from deep_translator import GoogleTranslator

_MAX_CHARS   = 4800
_MAX_WORKERS = 4
_RETRY_WAIT  = 0.5


def _clean(text: str) -> str:
    text = re.sub(r' +', ' ', text)
    text = re.sub(r' ([.,!?;:।])', r'\1', text)
    return text.strip()


def _split(text: str) -> list:
    if len(text) <= _MAX_CHARS:
        return [text]
    parts = re.split(r'(?<=[.!?।])\s+', text)
    chunks, cur = [], ""
    for part in parts:
        if len(cur) + len(part) + 1 > _MAX_CHARS:
            if cur: chunks.append(cur.strip())
            cur = part
        else:
            cur = (cur + " " + part).strip() if cur else part
    if cur: chunks.append(cur.strip())
    return chunks or [text]


def _google(source: str, target: str, text: str, retries: int = 2):
    """Single Google Translate call with retry."""
    for attempt in range(retries + 1):
        try:
            result = GoogleTranslator(source=source, target=target).translate(text)
            if result and result.strip():
                return result.strip()
        except Exception as e:
            print(f"[Translator] {source}→{target} attempt {attempt+1}: {e}")
            if attempt < retries:
                time.sleep(_RETRY_WAIT * (attempt + 1))
    return None


def _translate_one(chunk: str, target: str) -> str:
    """
    Translate one chunk using English as universal pivot.

    Pipeline:
      1. any input  →  English    (auto-detect source)
      2. English    →  target     (skip if target is English)

    Fallback (if pivot fails):
      Direct auto → target (best effort)
    """
    print(f"[Translator] chunk: '{chunk[:50]}' → target: {target}")

    # ── Step 1: get English version ──────────────────────
    en_text = _google("auto", "en", chunk)

    if not en_text:
        # English pivot failed entirely — try direct translation
        print(f"[Translator] English pivot failed, trying direct auto→{target}")
        result = _google("auto", target, chunk)
        return _clean(result) if result else chunk

    print(f"[Translator] English: '{en_text[:60]}'")

    # ── Step 2: English is the target — done ─────────────
    if target == "en":
        return _clean(en_text)

    # ── Step 3: English → target ─────────────────────────
    final = _google("en", target, en_text)
    if final:
        print(f"[Translator] Final ({target}): '{final[:60]}'")
        return _clean(final)

    # ── Step 4: direct fallback ───────────────────────────
    print(f"[Translator] en→{target} failed, trying direct auto→{target}")
    result = _google("auto", target, chunk)
    return _clean(result) if result else chunk


def translate(text: str, target_lang: str) -> str:
    """
    Translate text (any language) to target_lang.
    Uses English as a pivot for reliability.
    Handles any length via parallel chunk processing.
    """
    if not text or not text.strip():
        return text

    text   = text.strip()
    chunks = _split(text)
    print(f"[Translator] {len(chunks)} chunk(s) → {target_lang}")

    if len(chunks) == 1:
        return _translate_one(chunks[0], target_lang)

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