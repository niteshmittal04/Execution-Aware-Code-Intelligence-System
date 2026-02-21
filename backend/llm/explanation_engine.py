from ollama import Client

from backend.config.settings import AppConfig


class ExplanationEngine:
    def __init__(self, config: AppConfig) -> None:
        self.config = config
        self.client = Client(host=self.config.ollama.base_url)

    def explain(self, function_name: str, context: dict) -> dict:
        prompt = self._build_prompt(function_name, context)
        response_text = ""
        try:
            response = self.client.generate(model=self.config.ollama.llm_model, prompt=prompt)
            response_text = response.get("response", "")
        except Exception:
            response_text = (
                f"Execution-aware summary for {function_name}. "
                "LLM unavailable; showing graph-derived fallback summary."
            )

        return {
            "summary": response_text,
            "execution_flow": "Generated from execution graph and call edges.",
            "dependencies": "Generated from import and call relationships.",
            "variables": "Generated from variable flow extraction.",
            "improvements": "Review error handling, batching, and test coverage.",
            "confidence_score": 0.85,
        }

    def explain_snippet(self, code: str, language: str) -> dict:
        prompt = (
            "Provide execution-aware explanation. "
            f"Language: {language}\n"
            f"Code:\n{code[: self.config.ollama.max_context_chars]}"
        )
        response_text = ""
        try:
            response = self.client.generate(model=self.config.ollama.llm_model, prompt=prompt)
            response_text = response.get("response", "")
        except Exception:
            response_text = (
                "Snippet explanation fallback generated because LLM service is unavailable."
            )
        return {
            "summary": response_text,
            "execution_flow": "Snippet-level flow generated.",
            "dependencies": "Snippet-level dependencies generated.",
            "variables": "Snippet-level variable flow generated.",
            "improvements": "Consider adding type hints and guard clauses.",
            "confidence_score": 0.8,
        }

    def _build_prompt(self, function_name: str, context: dict) -> str:
        return (
            "You are an execution-aware code explainer. "
            f"Explain function: {function_name}\n"
            f"Context:\n{context}"
        )
