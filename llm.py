import re
import time
from google import genai
from google.genai import types
from groq import Groq
import config

_gemini = (genai.Client(api_key=config.GEMINI_API_KEY,
                        http_options=types.HttpOptions(timeout=60000))
           if config.GEMINI_API_KEY else None)
# max_retries=0: the SDK must not retry silently, or hidden waiting would count as latency
_groq = Groq(api_key=config.GROQ_API_KEY, timeout=60, max_retries=0) if config.GROQ_API_KEY else None


def _call_gemini(prompt, model, json_mode):
    cfg = types.GenerateContentConfig(response_mime_type="application/json") if json_mode else None
    resp = _gemini.models.generate_content(model=model, contents=prompt, config=cfg)
    u = getattr(resp, "usage_metadata", None)
    tin = (getattr(u, "prompt_token_count", 0) or 0) if u else 0
    tout = (getattr(u, "candidates_token_count", 0) or 0) if u else 0
    return resp.text, tin, tout


def _call_groq(prompt, model, json_mode, strict_json=False, effort=None):
    if json_mode:
        prompt += "\n\nReturn ONLY valid JSON. No markdown fences, no extra text."
    messages = [{"role": "user", "content": prompt}]
    extra = {}
    if strict_json:
        extra["response_format"] = {"type": "json_object"}        # Groq guarantees valid JSON
    if effort and model.startswith("openai/gpt-oss"):
        extra["reasoning_effort"] = effort                         # low = fewer thinking tokens
    try:
        r = _groq.chat.completions.create(model=model, messages=messages, temperature=0.2, **extra)
    except Exception as e:
        if extra and "400" in str(e):                              # option not accepted: plain call
            r = _groq.chat.completions.create(model=model, messages=messages, temperature=0.2)
        else:
            raise
    text = r.choices[0].message.content or ""
    if json_mode:
        text = text.replace("```json", "").replace("```", "").strip()
    usage = getattr(r, "usage", None)
    tin = (getattr(usage, "prompt_tokens", 0) or 0) if usage else 0
    tout = (getattr(usage, "completion_tokens", 0) or 0) if usage else 0
    return text, tin, tout


def _candidates(prompt, model, json_mode, strict_json=False, effort=None):
    small = model == config.SMALL_MODEL
    for provider in config.PROVIDERS:
        if provider == "groq" and _groq:
            gm = config.GROQ_SMALL if small else config.GROQ_LARGE
            yield f"groq:{gm}", (lambda gm=gm: _call_groq(prompt, gm, json_mode, strict_json, effort))
        if provider == "gemini" and _gemini:
            for gm in dict.fromkeys([model] + config.FALLBACK_MODELS):
                yield f"gemini:{gm}", (lambda gm=gm: _call_gemini(prompt, gm, json_mode))


def _retry_after(msg):
    """Reads 'try again in 7.2s', '1m24.5s' or '640ms' from a rate-limit message.
    Returns seconds, or None if the message does not say."""
    ms = re.search(r"try again in\s+([\d.]+)\s*ms", msg)
    if ms:
        return float(ms.group(1)) / 1000
    m = re.search(r"try again in\s+(?:(\d+)h)?\s*(?:(\d+)m)?\s*(?:([\d.]+)s)?", msg)
    if not m or not any(m.groups()):
        return None
    h, mi, s = m.groups()
    return int(h or 0) * 3600 + int(mi or 0) * 60 + float(s or 0)


def _is_rate_limit(msg):
    return "429" in msg or "RESOURCE_EXHAUSTED" in msg or "rate limit" in msg.lower()


def _is_daily_limit(msg):
    return any(k in msg for k in ("per day", "TPD", "RPD"))


def generate_ex(prompt, model=config.LARGE_MODEL, json_mode=False, tries=3, max_rate_waits=10,
                strict_json=False, reasoning_effort=None):
    """Returns text + token counts. Rate limits are WAITED OUT (using the time the server
    suggests); real errors are retried a few times, then the next provider is tried."""
    waited = 0.0          # seconds spent sleeping because of rate limits or errors
    for label, call in _candidates(prompt, model, json_mode, strict_json, reasoning_effort):
        errors, rate_waits = 0, 0
        while errors < tries and rate_waits < max_rate_waits:
            try:
                text, tin, tout = call()
                return {"text": text, "input_tokens": tin, "output_tokens": tout,
                        "model": label, "waited_s": waited}
            except Exception as e:
                msg = str(e)
                if any(x in msg for x in ("401", "403", "API key", "404", "NOT_FOUND")):
                    print(f"  {label}: unusable ({msg[:80]}), skipping")
                    break
                if _is_rate_limit(msg):
                    wait = _retry_after(msg)
                    if _is_daily_limit(msg) and (wait is None or wait > 300):
                        mins = f"{wait / 60:.0f} minutes" if wait else "a while"
                        raise RuntimeError(
                            f"{label}: DAILY free limit reached. Try again in about {mins}, "
                            f"or tomorrow. Your progress is saved. ({msg[:160]})"
                        )
                    wait = min((wait if wait is not None else 10) + 1, 120)
                    rate_waits += 1
                    print(f"  {label}: rate limit, waiting {wait:.0f}s ({rate_waits}/{max_rate_waits})")
                    time.sleep(wait)
                    waited += wait
                    continue
                errors += 1
                wait = 5 * errors
                print(f"  {label}: {msg[:80]}... retry in {wait}s ({errors}/{tries})")
                time.sleep(wait)
                waited += wait
        print(f"  Giving up on {label}, trying the next option")
    raise RuntimeError("Every provider failed. Check your keys and try again in a few minutes.")


def generate(prompt, model=config.LARGE_MODEL, json_mode=False, tries=3):
    return generate_ex(prompt, model, json_mode, tries)["text"]
