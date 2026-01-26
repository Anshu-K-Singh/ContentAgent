import httpx
from src.models.agent.schemas import ResearchData
from src.core.config import get_settings

settings = get_settings()

class ResearchService:
    async def search_web(self, query: str) -> ResearchData:
        """
        1. Search Google via Serper
        2. Take top 2 links
        3. Read full webpage text for each
        """
        print(f"🕵️ Searching web for: {query}")

        try:
            async with httpx.AsyncClient(timeout=30) as client:
                # Google Search 
                search_res = await client.post(
                    "https://google.serper.dev/search",
                    headers={
                        "X-API-KEY": settings.SERPER_API_KEY,
                        "Content-Type": "application/json"
                    },
                    json={
                        "q": query,
                        "num": 5
                    }
                )
                search_res.raise_for_status()
                search_data = search_res.json()

                organic = search_data.get("organic", [])
                top_links = [
                    r["link"] for r in organic[:2] if r.get("link")
                ]

                if not top_links:
                    return ResearchData(
                        summary="No sources found",
                        sources=[],
                        key_points=[]
                    )

                #  Read webpages 
                page_texts = []

                for link in top_links:
                    page_res = await client.post(
                        "https://google.serper.dev/webpage",
                        headers={
                            "X-API-KEY": settings.SERPER_API_KEY,
                            "Content-Type": "application/json"
                        },
                        json={"url": link}
                    )

                    page_res.raise_for_status()
                    page_data = page_res.json()

                    text = page_data.get("text", "")
                    if text:
                        page_texts.append(
                            f"\n\n===== SOURCE: {link} =====\n\n{text}"
                        )

                combined_text = "\n".join(page_texts)

                return ResearchData(
                    summary=combined_text[:4000],  # keep token-safe
                    sources=top_links,
                    key_points=[
                        "Extracted full article text from top 2 sources",
                        "Used Serper webpage API (clean text)"
                    ]
                )

        except Exception as e:
            print(f"❌ Research failed: {e}")
            return ResearchData(
                summary="Research failed",
                sources=[],
                key_points=[]
            )
