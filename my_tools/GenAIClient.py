from openai import OpenAI
import streamlit as st

class GenAIClient:
    def __init__(self):
        # Load key from Streamlit secrets
        self.client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

    def chat(self, prompt: str, model="gpt-4o-mini"):
        """General chat completion."""
        response = self.client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}]
        )
        return response.choices[0].message.content

    def extract_metadata(self, text: str):
        """Ask the model to extract structured metadata."""
        prompt = f"""
        Extract metadata from the following relinquishment report text.
        Return JSON with fields: title, block, operator, date_issued.

        TEXT:
        {text[:3000]}
        """
        return self.chat(prompt)

    def summarize(self, text: str):
        """Summarize a document."""
        prompt = f"Summarize the following text in 5 bullet points:\n\n{text[:4000]}"
        return self.chat(prompt)
