import requests, json
from typing import List, Dict, Any, Optional
from django.conf import settings

class OpenRouterClient:
    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        model: Optional[str] = None,
        referer: Optional[str] = None,
        app_title: Optional[str] = None,
        timeout: int = 40,
    ):
        cfg = settings.OPENROUTER
        self.api_key = api_key or cfg.get("API_KEY")
        self.base_url = (base_url or cfg.get("BASE_URL")).rstrip("/")
        self.model = model or cfg.get("MODEL")
        self.timeout = timeout
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            # These 2 are recommended by OpenRouter (helps your app appear in their dashboard):
            "HTTP-Referer": referer or cfg.get("REFERER"),
            "X-Title": app_title or cfg.get("APP_TITLE"),
        }
        if not self.api_key:
            raise ValueError("OPENROUTER_API_KEY is missing.")

    def chat(self, messages: List[Dict[str, str]], temperature: float = 0.2, max_tokens: int = 800) -> str:
        """
        messages = [{"role":"system","content":"..."}, {"role":"user","content":"..."}]
        returns the assistant string.
        """
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        url = f"{self.base_url}/chat/completions"
        resp = requests.post(url, headers=self.headers, data=json.dumps(payload), timeout=self.timeout)
        resp.raise_for_status()
        data = resp.json()
        # OpenRouter returns OpenAI-compatible structure
        return data["choices"][0]["message"]["content"]

# A helper that calls the LLM with a strict JSON schema
def llm_json(client: OpenRouterClient, system: str, user: str, schema_hint: str) -> Dict[str, Any]:
    messages = [
        {"role": "system", "content": system},
        {"role": "user", "content": f"{user}\n\nReturn ONLY valid JSON matching this schema:\n{schema_hint}"},
    ]
    raw = client.chat(messages)
    # make a best-effort parse (model should return JSON only)
    start = raw.find("{")
    end = raw.rfind("}")
    if start != -1 and end != -1 and end > start:
        raw = raw[start:end+1]
    return json.loads(raw)
