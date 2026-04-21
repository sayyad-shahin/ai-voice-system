import re, time
from concurrent.futures import ThreadPoolExecutor, as_completed
from deep_translator import GoogleTranslator

_MAX_CHARS   = 4800
_MAX_WORKERS = 4
_RETRY_WAIT  = 0.5

# Languages that benefit from forced two-hop routing via English
_TWO_HOP_LANGS = {"mr", "ta", "te", "gu", "bn", "kn", "hi"}


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


def _google(text, source, target, retries=2):
    """Single translation call with retry."""
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


def _translate_one(chunk, target):
    """
    Translate one chunk to target language.

    Strategy:
      1. If target is English  → direct auto→en
      2. If target is Indian   → two-hop: auto→en → en→target
         (most reliable for Hindi/Marathi/Tamil etc.)
      3. Final safety net      → direct auto→target
    """
    # ── Step 1: to English first (universal pivot) ────────────────────
    en_text = _google(chunk, "auto", "en")

    if not en_text:
        # Could not get English — fall back to direct translation
        print(f"[Translator] English pivot failed, trying direct auto→{target}")
        result = _google(chunk, "auto", target)
        return result if result else chunk

    # ── Step 2: English is the target — we're done ────────────────────
    if target == "en":
        return en_text

    # ── Step 3: English → target language ────────────────────────────
    final = _google(en_text, "en", target)
    if final:
        return final

    # ── Step 4: Last resort — direct auto → target ────────────────────
    print(f"[Translator] en→{target} failed, trying direct auto→{target}")
    result = _google(chunk, "auto", target)
    return result if result else chunk


def translate(text, target_lang):
    """Translate text (any language) to target_lang using auto-detect."""
    if not text or not text.strip():
        return text
    text   = text.strip()
    chunks = _split(text)

    print(f"[Translator] Translating {len(chunks)} chunk(s) → {target_lang}")

    if len(chunks) == 1:
        result = _translate_one(chunks[0], target_lang)
        print(f"[Translator] Input:  '{chunks[0][:80]}'")
        print(f"[Translator] Output: '{result[:80]}'")
        return result

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