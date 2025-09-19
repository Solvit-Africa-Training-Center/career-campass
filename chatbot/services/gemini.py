import os
import requests
from django.conf import settings

class GeminiService:
    API_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent"
    
    @classmethod
    def _get_api_key(cls):
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise RuntimeError("GEMINI_API_KEY environment variable is missing or empty. Please set it before starting the application.")
        return api_key
    @classmethod
    def send_message(cls, prompt, context=None):
        headers = {"Content-Type": "application/json"}
        data = {
            "contents": [{"parts": [{"text": prompt}]}]
        }
        # Optionally add context
        if context:
            data["context"] = context
        response = requests.post(f"{cls.API_URL}?key={cls._get_api_key()}", json=data, headers=headers)
        response.raise_for_status()
        return response.json()
