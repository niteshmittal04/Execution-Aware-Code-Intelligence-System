import os
import json

from openai import OpenAI

from backend.config.settings import AppConfig


class ExplanationEngine:
    def __init__(self, config: AppConfig) -> None:
        self.config = config
        api_key = os.getenv(self.config.llm.api_key_env_var, "")
        self.client = OpenAI(
            base_url=self.config.llm.base_url,
            api_key=api_key,
        )

    def explain(self, function_name: str, context: dict) -> dict:
        prompt = self._build_prompt(function_name, context)
        response_text = ""
        try:
            response = self.client.chat.completions.create(
                model=self.config.llm.model,
                messages=[
                    {
                        "role": "system",
                        "content": self._system_instruction(),
                    },
                    {
                        "role": "user",
                        "content": prompt,
                    },
                ],
            )
            response_text = (response.choices[0].message.content or "").strip()
        except Exception:
            return self._fallback_response(
                f"Execution-aware explanation for '{function_name}' is currently unavailable because the LLM service could not be reached."
            )

        return self._normalize_response(response_text)

    def explain_snippet(self, code: str, language: str) -> dict:
        prompt = self._build_snippet_prompt(code, language)
        response_text = ""
        try:
            response = self.client.chat.completions.create(
                model=self.config.llm.model,
                messages=[
                    {
                        "role": "system",
                        "content": self._system_instruction(),
                    },
                    {
                        "role": "user",
                        "content": prompt,
                    },
                ],
            )
            response_text = (response.choices[0].message.content or "").strip()
        except Exception:
            return self._fallback_response(
                "Snippet explanation is currently unavailable because the LLM service could not be reached."
            )
        return self._normalize_response(response_text)

    def _build_prompt(self, function_name: str, context: dict) -> str:
        context_json = json.dumps(context, ensure_ascii=False, default=str)
        return (
            "Explain a function using execution-aware context.\n"
            f"Target function: {function_name}\n"
            "Retrieved context (JSON):\n"
            f"{context_json[: self.config.llm.max_context_chars]}"
        )

    def _build_snippet_prompt(self, code: str, language: str) -> str:
        return (
            "Explain the code snippet with execution-aware reasoning.\n"
            f"Language: {language}\n"
            "Code:\n"
            f"{code[: self.config.llm.max_context_chars]}"
        )

    def _system_instruction(self) -> str:
        return (
            "You are an execution-aware code explanation assistant. "
            "Return ONLY valid JSON with this exact schema: "
            '{"summary": string, "execution_flow": string, "dependencies": string, '
            '"variables": string, "improvements": string, "confidence_score": number}. '
            "Keep each field concise and actionable. "
            "Do not use markdown, code fences, or extra keys."
        )

    def _normalize_response(self, raw_text: str) -> dict:
        cleaned = self._strip_code_fences((raw_text or "").strip())
        parsed = self._safe_json_parse(cleaned)
        if not parsed:
            return self._fallback_response(cleaned or "No explanation content returned by model.")

        return {
            "summary": self._to_clean_text(parsed.get("summary")),
            "execution_flow": self._to_clean_text(parsed.get("execution_flow")),
            "dependencies": self._to_clean_text(parsed.get("dependencies")),
            "variables": self._to_clean_text(parsed.get("variables")),
            "improvements": self._to_clean_text(parsed.get("improvements")),
            "confidence_score": self._normalize_confidence(parsed.get("confidence_score")),
        }

    def _fallback_response(self, summary: str) -> dict:
        return {
            "summary": self._to_clean_text(summary),
            "execution_flow": "Execution flow could not be generated from the LLM response.",
            "dependencies": "Dependency details were not available in the LLM response.",
            "variables": "Variable flow details were not available in the LLM response.",
            "improvements": "Add retries, verify model availability, and re-run explanation generation.",
            "confidence_score": 0.4,
        }

    def _strip_code_fences(self, text: str) -> str:
        if text.startswith("```") and text.endswith("```"):
            lines = text.splitlines()
            if len(lines) >= 3:
                return "\n".join(lines[1:-1]).strip()
        return text

    def _safe_json_parse(self, text: str) -> dict | None:
        if not text:
            return None
        try:
            parsed = json.loads(text)
            return parsed if isinstance(parsed, dict) else None
        except Exception:
            start = text.find("{")
            end = text.rfind("}")
            if start == -1 or end == -1 or end <= start:
                return None
            try:
                parsed = json.loads(text[start : end + 1])
                return parsed if isinstance(parsed, dict) else None
            except Exception:
                return None

    def _to_clean_text(self, value: object) -> str:
        if value is None:
            return "Not available."
        if isinstance(value, list):
            lines = [str(item).strip() for item in value if str(item).strip()]
            return "\n".join(f"- {item}" for item in lines) if lines else "Not available."
        if isinstance(value, dict):
            parts = [f"{key}: {val}" for key, val in value.items()]
            return "; ".join(parts).strip() or "Not available."
        text = str(value).strip()
        return text or "Not available."

    def _normalize_confidence(self, value: object) -> float:
        try:
            score = float(value)
        except Exception:
            return 0.7
        if score < 0:
            return 0.0
        if score > 1:
            return 1.0
        return round(score, 2)
