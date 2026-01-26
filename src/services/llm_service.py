from langchain_openai import ChatOpenAI
from src.core.config import get_settings

settings = get_settings()

class LLMService:
    def __init__(self):
        # Base Configuration for OpenRouter
        common_config = {
            "api_key": settings.OPENROUTER_API_KEY,
            "base_url": "https://openrouter.ai/api/v1",
            "default_headers": {
                "HTTP-Referer": "http://localhost:8000",
                "X-Title": "ContentAgent"
            }
        }

        self.client = ChatOpenAI(
            model="meta-llama/llama-3.3-70b-instruct:free",
            temperature=0.7,
            **common_config
        )

    async def generate_content(self, prompt: str, model="pro") -> str:
        """
        Simple generation using the reliable Llama 3.3 model.
        Ignores 'model' param since we use the same one for everything.
        """
        try:
            print(f"🤖 Calling OpenRouter Model: {self.client.model_name}")
            response = await self.client.ainvoke(prompt)
            return response.content
        except Exception as e:
            print(f"❌ OpenRouter Error: {e}")
            import json
            return json.dumps({
                "error": "AI Service unavailable",
                "linkedin_post": "Error generating content.", 
                "twitter_thread": [],
                "strategies": []
            })