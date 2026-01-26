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
            
            # Add logging
            content = response.content
            print(f"📨 Received response ({len(content)} chars)")
            
            return content
            
        except Exception as e:
            print(f"❌ OpenRouter Error: {e}")
            
            # ⚠️ THIS IS THE PROBLEM - You're returning JSON string for errors
            # but the research_node tries to parse it as research data!
            error_response = json.dumps({
                "error": "AI Service unavailable",
                "message": str(e)
            })
            
            print(f"⚠️ Returning error response: {error_response}")
            return error_response  # This causes the parsing error