import json
import httpx
import asyncio
import logging
from typing import Optional, List, Dict, Any
from app.core.config import settings

logger = logging.getLogger("arams.llm")


class CloudflareLLM:
    def __init__(self, model: Optional[str] = None, format_json: bool = False):
        self.api_token = settings.CLOUDFLARE_API_TOKEN
        self.account_id = settings.CLOUDFLARE_ACCOUNT_ID
        self.model = model or settings.CLOUDFLARE_MODEL
        self.format_json = format_json

    def _base_url(self):
        return f"https://api.cloudflare.com/client/v4/accounts/{self.account_id}/ai/v1"

    async def ainvoke(self, prompt: str) -> Any:
        if not self.api_token or not self.account_id:
            raise ValueError("CLOUDFLARE_API_TOKEN and CLOUDFLARE_ACCOUNT_ID must be set")
        messages = [{"role": "user", "content": prompt}]
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_token}",
            "cf-aig-gateway-id": "default",
        }
        body = {"model": self.model, "messages": messages, "max_tokens": 32768}
        if self.format_json:
            body["response_format"] = {"type": "json_object"}

        # Try Cloudflare first
        cf_ok = False
        try:
            async with httpx.AsyncClient(timeout=300.0) as client:
                resp = await client.post(f"{self._base_url()}/chat/completions", headers=headers, json=body)
                resp.raise_for_status()
                data = resp.json()
                raw_content = data.get("choices", [{}])[0].get("message", {}).get("content") or ""
                if raw_content:
                    return LLMResponse(raw_content.strip())
                cf_ok = True  # response parsed but empty
        except httpx.TimeoutException:
            logger.warning("Cloudflare LLM timed out")
        except httpx.HTTPStatusError as e:
            body_text = e.response.text[:300] if e.response else str(e)
            logger.warning(f"Cloudflare LLM failed ({e.response.status_code}): {body_text}")

        if cf_ok:
            fail_reason = "Cloudflare returned empty content"
        else:
            fail_reason = "Cloudflare quota exhausted or unavailable"

        # Fallback: try OpenAI gateway
        e2 = None
        try:
            keys = []
            if settings.OPENAI_API_KEY:
                keys.append(settings.OPENAI_API_KEY)
            keys.extend([k.strip() for k in settings.OPENAI_API_KEYS.split(",") if k.strip()])
            if keys:
                from langchain_openai import ChatOpenAI
                oai = ChatOpenAI(
                    model=settings.OPENAI_MODEL or "gemini-2.5-flash",
                    api_key=keys[0],
                    base_url=settings.OPENAI_BASE_URL,
                    model_kwargs={"response_format": {"type": "json_object"}} if self.format_json else None
                )
                response = await oai.ainvoke(prompt)
                text = response.content if hasattr(response, 'content') else str(response)
                return LLMResponse(text.strip())
        except Exception as e2:
            logger.warning(f"OpenAI fallback failed: {e2}")

        # Final fallback: Ollama
        try:
            from langchain_ollama import ChatOllama
            ollama = ChatOllama(
                model=settings.LLM_MODEL,
                base_url=settings.OLLAMA_BASE_URL,
                format="json" if self.format_json else None
            )
            response = await ollama.ainvoke(prompt)
            text = response.content if hasattr(response, 'content') else str(response)
            return LLMResponse(text.strip())
        except Exception as e3:
            raise RuntimeError(f"All LLM backends failed. CF: {fail_reason}, OpenAI: {e2}, Ollama: {e3}")

    def invoke(self, prompt: str) -> Any:
        import asyncio
        return asyncio.run(self.ainvoke(prompt))


class RotatingOpenAILLM:
    def __init__(self, model: str, base_url: str, api_keys: List[str], format_json: bool = False):
        self.model = model
        self.base_url = base_url
        self.api_keys = api_keys
        self.format_json = format_json
        self._current = 0

    def _make_llm(self, key: str):
        from langchain_openai import ChatOpenAI
        return ChatOpenAI(
            model=self.model,
            api_key=key,
            base_url=self.base_url,
            model_kwargs={"response_format": {"type": "json_object"}} if self.format_json else None
        )

    def _is_retryable(self, e: Exception) -> bool:
        err = str(e)
        return any(x in err for x in ["401", "403", "429", "AuthenticationError", "RateLimitError", "unauthorized", "no access", "no credits"])

    async def ainvoke(self, prompt: str) -> Any:
        last_error = None
        seen = set()
        for i in range(len(self.api_keys) * 2):
            idx = (self._current + i) % len(self.api_keys)
            if idx in seen and len(seen) == len(self.api_keys):
                break
            seen.add(idx)
            key = self.api_keys[idx]
            try:
                llm = self._make_llm(key)
                result = await llm.ainvoke(prompt)
                self._current = (idx + 1) % len(self.api_keys)
                return result
            except ImportError:
                raise
            except Exception as e:
                last_error = e
                if self._is_retryable(e):
                    if "429" in str(e):
                        wait = min(10, 2 ** i)
                        logger.warning(f"Key {key[:16]}... rate limited, cooling {wait}s before next")
                        await asyncio.sleep(wait)
                    else:
                        logger.warning(f"Key {key[:16]}... failed ({e}), trying next")
                    self._current = (idx + 1) % len(self.api_keys)
                    continue
                raise
        logger.warning("all API keys exhausted, falling back to Ollama")
        from langchain_ollama import ChatOllama
        fallback = ChatOllama(
            model=settings.LLM_MODEL,
            base_url=settings.OLLAMA_BASE_URL,
            format="json" if self.format_json else None
        )
        return await fallback.ainvoke(prompt)

    def invoke(self, prompt: str) -> Any:
        import asyncio
        return asyncio.run(self.ainvoke(prompt))


class GeminiLLM:
    def __init__(self, model: Optional[str] = None, format_json: bool = False):
        self.api_key = settings.GEMINI_API_KEY
        self.model = model or settings.GEMINI_MODEL
        self.format_json = format_json

    async def ainvoke(self, prompt: str) -> Any:
        import google.generativeai as genai
        genai.configure(api_key=self.api_key)
        model = genai.GenerativeModel(
            self.model,
            generation_config={"response_mime_type": "application/json"} if self.format_json else None
        )
        last_error = None
        for attempt in range(3):
            try:
                response = await model.generate_content_async(prompt)
                return LLMResponse(response.text)
            except Exception as e:
                last_error = e
                err_str = str(e)
                if "429" in err_str or "quota" in err_str.lower() or "RATELIMIT" in err_str.upper():
                    wait = 5 * (attempt + 1)
                    logger.warning(f"Gemini rate limited, retrying in {wait}s (attempt {attempt+1}/3): {e}")
                    await asyncio.sleep(wait)
                else:
                    logger.error(f"Gemini LLM error: {e}")
                    raise
        raise last_error

    def invoke(self, prompt: str) -> Any:
        import asyncio
        return asyncio.run(self.ainvoke(prompt))


class GrokLLM:
    def __init__(self, model: Optional[str] = None, format: Optional[str] = None):
        self.api_key = settings.GROK_API_KEY
        self.base_url = settings.GROK_BASE_URL
        self.model = model or settings.GROK_MODEL
        self.format = format

    async def ainvoke(self, prompt: str) -> Any:
        if not self.api_key:
            raise ValueError("GROK_API_KEY not set")
        messages = [{"role": "user", "content": prompt}]
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }
        body = {
            "model": self.model,
            "messages": messages
        }
        async with httpx.AsyncClient(timeout=120.0) as client:
            resp = await client.post(f"{self.base_url}/chat/completions", headers=headers, json=body)
            resp.raise_for_status()
            data = resp.json()
            output_text = data.get("choices", [{}])[0].get("message", {}).get("content", "")
            return LLMResponse(output_text)

    def invoke(self, prompt: str) -> Any:
        import asyncio
        return asyncio.run(self.ainvoke(prompt))


class LLMResponse:
    def __init__(self, content: str):
        self.content = content

    def __str__(self):
        return self.content


def get_llm(model: Optional[str] = None, format_json: bool = False, prefer_fast: bool = True):
    backend = settings.LLM_BACKEND
    if backend == "gemini" and settings.GEMINI_API_KEY:
        return GeminiLLM(model=model, format_json=format_json)
    elif backend == "grok" and settings.GROK_API_KEY:
        return GrokLLM(model=model)
    elif backend == "openai":
        try:
            keys = []
            if settings.OPENAI_API_KEY:
                keys.append(settings.OPENAI_API_KEY)
            keys.extend([k.strip() for k in settings.OPENAI_API_KEYS.split(",") if k.strip()])
            if not keys:
                raise ValueError("no OpenAI API keys configured")
            model_name = model or settings.OPENAI_MODEL
            if len(keys) == 1:
                from langchain_openai import ChatOpenAI
                return ChatOpenAI(
                    model=model_name,
                    api_key=keys[0],
                    base_url=settings.OPENAI_BASE_URL,
                    model_kwargs={"response_format": {"type": "json_object"}} if format_json else None
                )
            return RotatingOpenAILLM(
                model=model_name,
                base_url=settings.OPENAI_BASE_URL,
                api_keys=keys,
                format_json=format_json,
            )
        except ImportError:
            pass
    elif backend == "cf":
        if settings.CLOUDFLARE_API_TOKEN and settings.CLOUDFLARE_ACCOUNT_ID:
            return CloudflareLLM(model=model, format_json=format_json)
    elif backend == "ollama":
        try:
            from langchain_ollama import ChatOllama
            return ChatOllama(
                model=settings.LLM_MODEL,
                base_url=settings.OLLAMA_BASE_URL,
                format="json" if format_json else None
            )
        except ImportError:
            pass
    if settings.GEMINI_API_KEY:
        return GeminiLLM(model=model, format_json=format_json)
    if settings.GROK_API_KEY:
        return GrokLLM(model=model)
    from langchain_ollama import ChatOllama
    return ChatOllama(
        model=settings.LLM_MODEL,
        base_url=settings.OLLAMA_BASE_URL,
        format="json" if format_json else None
    )
