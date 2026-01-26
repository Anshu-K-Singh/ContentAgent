import httpx
from urllib.parse import quote

class MediaService:
    async def generate_image_url(self, prompt: str) -> str:
        """
        Generates an AI image using Pollinations.ai (Free, No API Key).
        """
        print(f"🎨 Generating Image for: {prompt[:50]}...")
        
        # Clean the prompt for URL
        clean_prompt = quote(prompt)
        
        # Pollinations generates image on the fly via URL
        # We add 'seed' to make it deterministic if needed, or random if not.
        # Format: https://image.pollinations.ai/prompt/{prompt}
        image_url = f"https://image.pollinations.ai/prompt/{clean_prompt}?width=1024&height=1024&nologo=true"
        
        return image_url

    # Future-proof: If you get a Flux key, add a method here:
    # async def generate_flux_image(self, prompt: str): ...