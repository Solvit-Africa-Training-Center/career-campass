import os
import requests
from django.conf import settings

class GeminiService:
    API_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent"
    API_KEY = os.getenv("GEMINI_API_KEY")

    if not API_KEY:
        raise RuntimeError("GEMINI_API_KEY environment variable is missing or empty. Please set it before starting the application.")
    @classmethod
    def send_message(cls, prompt, context=None):
        headers = {"Content-Type": "application/json"}
        data = {
            "contents": [{"parts": [{"text": prompt}]}]
        }
        # Optionally add context
        if context:
            data["context"] = context
        
        try:
            response = requests.post(f"{cls.API_URL}?key={cls.API_KEY}", json=data, headers=headers, timeout=30)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.Timeout:
            raise Exception("Gemini API request timed out. Please try again.")
        except requests.exceptions.HTTPError as e:
            if response.status_code == 401:
                raise Exception("Invalid Gemini API key. Please check your GEMINI_API_KEY.")
            elif response.status_code == 429:
                raise Exception("Gemini API rate limit exceeded. Please try again later.")
            else:
                raise Exception(f"Gemini API error: {response.status_code}")
        except requests.exceptions.RequestException as e:
            raise Exception(f"Network error connecting to Gemini API: {str(e)}")
