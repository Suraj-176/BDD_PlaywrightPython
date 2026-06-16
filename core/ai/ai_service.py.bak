import os
import re
import requests
from core.logger.logger import logger

class AIService:
    _cache = {}

    @classmethod
    def _sanitize_dom(cls, dom: str) -> str:
        # Mask credentials and sensitive info
        sanitized = re.sub(r'value=(["\']).*?\1', 'value="***MASKED***"', dom, flags=re.IGNORECASE)
        sanitized = re.sub(r'([A-Z]{5}[0-9]{4}[A-Z])', '***MASKED_PAN***', sanitized)
        sanitized = re.sub(r'\b\d{12,19}\b', '***MASKED_NUMBER***', sanitized)
        sanitized = re.sub(
            r'(password|token|secret|authorization|api[_-]?key)(["\'\s:=]+)[^"\'<>\s]+',
            r'\1\2***MASKED***',
            sanitized,
            flags=re.IGNORECASE
        )
        return sanitized

    @classmethod
    def _get_request_config(cls, provider: str, api_key: str, model: str, system_prompt: str, user_prompt: str):
        headers = {
            "Content-Type": "application/json"
        }
        url = ""
        body = {}

        provider_upper = provider.upper()

        if provider_upper == "GROQ":
            url = "https://api.groq.com/openai/v1/chat/completions"
            headers["Authorization"] = f"Bearer {api_key}"
            body = {
                "model": model,
                "max_tokens": 100,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ]
            }
        elif provider_upper == "OPENAI":
            url = "https://api.openai.com/v1/chat/completions"
            headers["Authorization"] = f"Bearer {api_key}"
            body = {
                "model": model,
                "max_tokens": 100,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ]
            }
        elif provider_upper == "AZURE_OPENAI":
            api_version = os.getenv("AZURE_OPENAI_API_VERSION", "2023-05-15")
            resource_url = os.getenv("AZURE_OPENAI_API_URL", "")
            url = f"{resource_url}/openai/deployments/{model}/chat/completions?api-version={api_version}"
            headers["api-key"] = api_key
            body = {
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ]
            }
        elif provider_upper == "GEMINI":
            url = "https://generativelanguage.googleapis.com/v1beta/openai/chat/completions"
            headers["Authorization"] = f"Bearer {api_key}"
            body = {
                "model": model,
                "max_tokens": 100,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ]
            }
        elif provider_upper == "CLAUDE":
            url = "https://api.anthropic.com/v1/messages"
            headers["x-api-key"] = api_key
            headers["anthropic-version"] = "2023-06-01"
            body = {
                "model": model,
                "max_tokens": 100,
                "system": system_prompt,
                "messages": [
                    {"role": "user", "content": user_prompt}
                ]
            }
        elif provider_upper == "OPENROUTER":
            url = "https://openrouter.ai/api/v1/chat/completions"
            headers["Authorization"] = f"Bearer {api_key}"
            headers["HTTP-Referer"] = "https://icici.com"
            body = {
                "model": model,
                "max_tokens": 100,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ]
            }
        else:
            raise ValueError(f"Unsupported AI_PROVIDER: '{provider}'")

        return url, headers, body

    @classmethod
    def get_locator(cls, dom: str, element_description: str) -> str:
        cache_key = element_description.lower().strip()
        if cache_key in cls._cache:
            logger.info(f"[AI Cache Hit] '{element_description}' → {cls._cache[cache_key]}")
            return cls._cache[cache_key]

        provider = os.getenv("AI_PROVIDER", "GEMINI").upper()
        
        # Dynamically fetch the correct API Key and Model Name depending on the selected AI_PROVIDER
        if provider == "GEMINI":
            api_key = os.getenv("GEMINI_API_KEY") or os.getenv("AI_API_KEY") or ""
            model = os.getenv("GEMINI_MODEL", "gemini-1.5-pro")
        elif provider == "GROQ":
            api_key = os.getenv("GROQ_API_KEY") or os.getenv("AI_API_KEY") or ""
            model = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
        elif provider == "OPENAI":
            api_key = os.getenv("OPENAI_API_KEY") or os.getenv("AI_API_KEY") or ""
            model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
        elif provider == "CLAUDE":
            api_key = os.getenv("CLAUDE_API_KEY") or os.getenv("AI_API_KEY") or ""
            model = os.getenv("CLAUDE_MODEL", "claude-3-5-sonnet-latest")
        elif provider == "AZURE_OPENAI":
            api_key = os.getenv("AZURE_OPENAI_API_KEY") or os.getenv("AI_API_KEY") or ""
            model = os.getenv("AZURE_OPENAI_MODEL", "")
        else:
            # Fallback to general parameters
            api_key = os.getenv("AI_API_KEY") or ""
            model = os.getenv("AI_MODEL") or ""

        if not api_key:
            raise RuntimeError(
                f"AI API key is missing for provider: {provider}.\n"
                f"Please ensure {provider}_API_KEY or AI_API_KEY is configured inside your .env file."
            )

        system_prompt = (
            "You are a Playwright locator expert.\n"
            "Return ONLY a single CSS selector string.\n"
            "No explanation. No backticks. No extra text.\n"
            "Prefer: id > name attribute > data-testid > class.\n"
            "Must be unique on the page."
        )

        sanitized_dom = cls._sanitize_dom(dom)[:5000]
        user_prompt = f"Find the best unique CSS selector for: '{element_description}'\nHTML: {sanitized_dom}"

        url, headers, body = cls._get_request_config(provider, api_key, model, system_prompt, user_prompt)

        try:
            response = requests.post(url, headers=headers, json=body, timeout=30)
            if response.status_code != 200:
                raise RuntimeError(f"HTTP Error {response.status_code}: {response.text}")

            response_json = response.json()
            locator = ""

            if provider.upper() == "CLAUDE":
                locator = response_json.get("content", [{}])[0].get("text", "").strip()
            else:
                locator = response_json.get("choices", [{}])[0].get("message", {}).get("content", "").strip()

            if not locator:
                raise RuntimeError(f"AI returned empty locator for: '{element_description}'")

            cls._cache[cache_key] = locator
            logger.info(f"[AI Locator - {provider}] '{element_description}' → {locator}")
            return locator
        except Exception as error:
            raise RuntimeError(f"[AIService - {provider} Fetch Failure]: {str(error)}")

    @classmethod
    def clear_cache(cls):
        cls._cache.clear()
pass
