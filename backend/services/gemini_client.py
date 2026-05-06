"""
LLM client powered by Groq (drop-in replacement for the original Gemini client).
Keeps the same GeminiClient class name so no callers need to change.
- Retry with exponential backoff (max 4 retries, 1.5s base)
- SHA-256 hashing of prompt and response
- Writes audit log to llm_audit_log table
"""
import hashlib
import json
import time
import uuid
import os
import logging
from typing import Optional

from groq import Groq, RateLimitError, APIStatusError
from sqlalchemy.orm import Session

from db.database import SessionLocal
from db.models import LLMAuditLog

logger = logging.getLogger(__name__)

# Map old Gemini model names to Groq models
MODEL_MAP = {
    "gemini-2.0-flash": "llama-3.3-70b-versatile",
    "gemini-2.5-pro": "llama-3.3-70b-versatile",
}


class GeminiError(Exception):
    """Typed exception for LLM client errors."""
    def __init__(self, error_code: str, retryable: bool, message: str):
        self.error_code = error_code
        self.retryable = retryable
        self.message = message
        super().__init__(message)


class GeminiClient:
    """
    Wrapper around Groq API (maintains GeminiClient interface for compatibility).
    - Retry with exponential backoff (max 4 retries, 1.5s base)
    - SHA-256 hashing of prompt and response
    - Writes audit log to llm_audit_log table
    """

    def __init__(self, model: str = "gemini-2.0-flash", service_name: str = "unknown"):
        self.model_name = model
        self.groq_model = MODEL_MAP.get(model, "llama-3.3-70b-versatile")
        self.service_name = service_name
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            raise GeminiError("CONFIG_ERROR", False, "GROQ_API_KEY not set")
        self._client = Groq(api_key=api_key)

    def generate(self, prompt: str, json_mode: bool = True) -> str:
        """
        Generate content from the LLM with retry and audit logging.

        Args:
            prompt: The prompt string to send
            json_mode: If True, request JSON response format

        Returns:
            The generated text response
        """
        prompt_hash = hashlib.sha256(prompt.encode("utf-8")).hexdigest()
        max_retries = 6  # Increased to 6 to handle TPM rate limits better
        base_delay = 5.0  # Increased base delay for TPM limits
        current_model = self.groq_model

        for attempt in range(max_retries + 1):
            start_time = time.time()
            try:
                messages = [{"role": "user", "content": prompt}]

                kwargs = {
                    "model": current_model,
                    "messages": messages,
                    "temperature": 0.1,
                    "max_tokens": 8192,
                }

                if json_mode:
                    kwargs["response_format"] = {"type": "json_object"}
                    # Prepend system message to ensure JSON output
                    messages.insert(0, {
                        "role": "system",
                        "content": "You are a helpful assistant. Always respond with valid JSON.",
                    })

                response = self._client.chat.completions.create(**kwargs)

                response_text = response.choices[0].message.content
                latency_ms = (time.time() - start_time) * 1000
                response_hash = hashlib.sha256(response_text.encode("utf-8")).hexdigest()

                # Extract token counts
                input_tokens = getattr(response.usage, "prompt_tokens", None) if response.usage else None
                output_tokens = getattr(response.usage, "completion_tokens", None) if response.usage else None

                # Write audit log
                self._write_audit_log(
                    model=current_model,
                    prompt_hash=prompt_hash,
                    response_hash=response_hash,
                    input_tokens=input_tokens,
                    output_tokens=output_tokens,
                    latency_ms=latency_ms,
                )

                return response_text

            except RateLimitError as e:
                if attempt < max_retries:
                    delay = base_delay * (1.5 ** attempt) # E.g., 5, 7.5, 11.2, 16.8, 25.3, 37.9
                    logger.warning(
                        f"Groq RateLimitError on attempt {attempt + 1}, "
                        f"retrying in {delay:.1f}s with model {current_model}"
                    )
                    time.sleep(delay)
                else:
                    raise GeminiError(
                        error_code="RATE_LIMIT",
                        retryable=True,
                        message=f"Groq API rate limited after {max_retries} retries: {str(e)}"
                    )

            except APIStatusError as e:
                if e.status_code in (413, 503, 502, 500) and attempt < max_retries:
                    delay = base_delay * (1.5 ** attempt)
                    logger.warning(
                        f"Groq API error {e.status_code} on attempt {attempt + 1}, "
                        f"retrying in {delay:.1f}s"
                    )
                    time.sleep(delay)
                else:
                    raise GeminiError(
                        error_code="SERVICE_UNAVAILABLE",
                        retryable=True,
                        message=f"Groq API error after retries: {str(e)}"
                    )

            except Exception as e:
                raise GeminiError(
                    error_code="GENERATION_ERROR",
                    retryable=False,
                    message=f"Groq generation failed: {str(e)}"
                )

        raise GeminiError("MAX_RETRIES", True, "Exhausted all retry attempts")

    def _write_audit_log(
        self,
        model: str,
        prompt_hash: str,
        response_hash: str,
        input_tokens: Optional[int],
        output_tokens: Optional[int],
        latency_ms: float,
    ):
        """Write one row to llm_audit_log (insert-only)."""
        try:
            db: Session = SessionLocal()
            log_entry = LLMAuditLog(
                id=str(uuid.uuid4()),
                service=self.service_name,
                model=model,
                prompt_hash_sha256=prompt_hash,
                response_hash_sha256=response_hash,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                latency_ms=latency_ms,
            )
            db.add(log_entry)
            db.commit()
            db.close()
        except Exception as e:
            logger.error(f"Failed to write LLM audit log: {e}")
