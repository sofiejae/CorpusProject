import json
import os

from openai import OpenAI


def _find_api_key():
    """Look for the key in Streamlit secrets first, then in the OPENAI_API_KEY environment variable."""
    try:
        import streamlit as st
        return st.secrets["OPENAI_API_KEY"]
    except Exception:
        # no streamlit, no secrets.toml, or key missing -> fall back to the environment
        return os.environ.get("OPENAI_API_KEY")


class GenAIClient:
    def __init__(self, api_key=None, model="gpt-4o-mini"):
        api_key = api_key or _find_api_key()
        if not api_key:
            raise RuntimeError(
                "No OpenAI API key found. Put OPENAI_API_KEY in .streamlit/secrets.toml "
                "or set it as an environment variable."
            )
        self.client = OpenAI(api_key=api_key)
        self.model = model

    def chat(self, prompt: str, model=None, json_mode=False):
        """General chat completion. With json_mode=True the model is forced to return valid JSON."""
        kwargs = {}
        if json_mode:
            kwargs["response_format"] = {"type": "json_object"}
        response = self.client.chat.completions.create(
            model=model or self.model,
            messages=[{"role": "user", "content": prompt}],
            **kwargs,
        )
        return response.choices[0].message.content

    def extract_metadata(self, text: str) -> dict:
        """Ask the model to extract structured metadata. Returns a dict."""
        prompt = f"""
        Extract metadata from the following relinquishment report text.
        Return a JSON object with the fields: title, block, operator, date_issued.
        Use null for anything you cannot find.

        TEXT:
        {text[:3000]}
        """
        answer = self.chat(prompt, json_mode=True)
        try:
            return json.loads(answer)
        except (json.JSONDecodeError, TypeError):
            return {"raw_answer": answer}

    def summarize(self, text: str):
        """Summarize a document."""
        prompt = f"Summarize the following text in 5 bullet points:\n\n{text[:4000]}"
        return self.chat(prompt)