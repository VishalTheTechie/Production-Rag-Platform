import time
from google import genai
from google.genai import types
from groq import Groq
import config

_gemini = (genai.Client(api_key=config.GEMINI_API_KEY,
                        http_options=types.HttpOptions(timeout=60000))
           if config.GEMINI_API_KEY else None)
_groq = Groq(api_key=config.GROQ_API_KEY, timeout=60) if config.GROQ_API_KEY else None


def _call_gemini(prompt, model, json_mode):
    cfg = types.GenerateContentConfig(response_mime_type="application/json") if json_mode else None
    return _gemini.models.generate_content(model=model, contents=prompt, config=cfg).text


def _call_groq(prompt, model, json_mode):
    if json_mode:
        prompt += "\n\nReturn ONLY valid JSON. No markdown fences, no extra text."
    r = _groq.chat.completions.create(
        model=model, messages=[{"role": "user", "content": prompt}], temperature=0.2
    )
    text = r.choices[0].message.content
    if json_mode:
        text = text.replace("```json", "").replace("```", "").strip()
    return text


def _candidates(prompt, model, json_mode):
    small = model == config.SMALL_MODEL
    for provider in config.PROVIDERS:
        if provider == "groq" and _groq:
            gm = config.GROQ_SMALL if small else config.GROQ_LARGE
            yield f"groq:{gm}", (lambda gm=gm: _call_groq(prompt, gm, json_mode))
        if provider == "gemini" and _gemini:
            for gm in dict.fromkeys([model] + config.FALLBACK_MODELS):
                yield f"gemini:{gm}", (lambda gm=gm: _call_gemini(prompt, gm, json_mode))


def generate(prompt, model=config.LARGE_MODEL, json_mode=False, tries=3):
    for label, call in _candidates(prompt, model, json_mode):
        for attempt in range(tries):
            try:
                return call()
            except Exception as e:
                msg = str(e)
                if any(x in msg for x in ("401", "403", "API key", "404", "NOT_FOUND")):
                    print(f"  {label}: unusable ({msg[:80]}), skipping")
                    break
                wait = 5 * (attempt + 1)
                print(f"  {label}: {msg[:80]}... retry in {wait}s ({attempt + 1}/{tries})")
                time.sleep(wait)
        print(f"  Giving up on {label}, trying the next option")
    raise RuntimeError("Every provider failed. Check your keys and try again in a few minutes.")