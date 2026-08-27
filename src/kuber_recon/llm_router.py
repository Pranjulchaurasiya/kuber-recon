"""
TabiToken LLM Client & Router
=============================
Provides direct, authenticated routing to Claude models via TabiToken:
  - claude-opus-5
  - claude-opus-4-8
  - claude-opus-5-thinking
  - claude-opus-4-8-thinking
"""

import json
import os
import urllib.request
from typing import Optional, Dict, Any, List

TABITOKEN_BASE_URL = os.getenv("OPENAI_BASE_URL", "https://tabitoken.com/v1")
TABITOKEN_API_KEY = os.getenv("OPENAI_API_KEY", "sk-JpIAK2H3tmM2enTaGuapQ4S7aEECXIOLzRKPW1f06m7SyfzF")


def query_tabitoken(
    prompt: str,
    system_prompt: str = "",
    model: str = "claude-opus-5",
    temperature: float = 0.2,
    max_tokens: int = 4096,
) -> str:
    """
    Send a prompt to TabiToken endpoint and return the assistant response string.
    """
    messages: List[Dict[str, str]] = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": prompt})

    payload = {
        "model": model,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
    }

    url = f"{TABITOKEN_BASE_URL.rstrip('/')}/chat/completions"
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=data,
        headers={
            "Authorization": f"Bearer {TABITOKEN_API_KEY}",
            "Content-Type": "application/json",
            "User-Agent": "KuberRecon-APEX/1.0",
        },
    )

    with urllib.request.urlopen(req, timeout=60) as res:
        if res.getcode() != 200:
            raise RuntimeError(f"TabiToken API returned HTTP {res.getcode()}")
        raw = res.read().decode("utf-8")
        parsed = json.loads(raw)
        return parsed["choices"][0]["message"]["content"]


if __name__ == "__main__":
    reply = query_tabitoken("Explain in 1 short sentence why paise-exact arithmetic is critical in Indian payments.")
    print("Test Output:", reply)
