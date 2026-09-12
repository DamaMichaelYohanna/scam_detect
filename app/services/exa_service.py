import logging
from typing import List, Optional
from exa_py import Exa
from app.config import settings

logger = logging.getLogger(__name__)


class ExaContextResult:
    def __init__(self, page_contents: str = "", web_search_intelligence: str = ""):
        self.page_contents = page_contents
        self.web_search_intelligence = web_search_intelligence

    def to_combined_context(self) -> str:
        parts = []
        if self.page_contents:
            parts.append(f"### [LIVE PAGE CONTENTS FETCHED BY EXA]:\n{self.page_contents}")
        if self.web_search_intelligence:
            parts.append(f"### [EXA WEB SEARCH INTELLIGENCE & REPUTATION]:\n{self.web_search_intelligence}")
        return "\n\n".join(parts) if parts else "No live web content could be retrieved."


class ExaService:
    def __init__(self):
        self._client: Optional[Exa] = None

    def _get_client(self) -> Optional[Exa]:
        if not settings.EXA_API_KEY:
            logger.warning("EXA_API_KEY not configured. Skipping live web extraction.")
            return None
        if self._client is None:
            self._client = Exa(api_key=settings.EXA_API_KEY)
        return self._client

    async def extract_context(
        self,
        urls: List[str],
        message_text: str,
        matched_keywords: List[str]
    ) -> ExaContextResult:
        client = self._get_client()
        if not client:
            return ExaContextResult()

        page_contents_list: List[str] = []
        intelligence_list: List[str] = []

        # 1. Fetch live page contents for detected URLs
        formatted_urls = []
        for url in urls[:3]:  # Limit to top 3 URLs to avoid rate limits
            if not url.startswith(("http://", "https://")):
                url = f"https://{url}"
            formatted_urls.append(url)

        if formatted_urls:
            try:
                # Use Exa get_contents to read live webpage content
                contents_response = client.get_contents(
                    urls=formatted_urls,
                    text={"max_characters": 2500}
                )
                for res in contents_response.results:
                    title = getattr(res, "title", "Untitled")
                    url = getattr(res, "url", "")
                    text = getattr(res, "text", "")
                    if text:
                        page_contents_list.append(f"Page Title: {title}\nURL: {url}\nContent Snippet:\n{text[:1500]}")
            except Exception as e:
                logger.error(f"Error fetching live contents with Exa: {e}")

        # 2. Search web for scam reports & domain reputation
        search_query = ""
        if formatted_urls:
            domain = formatted_urls[0].replace("https://", "").replace("http://", "").split("/")[0]
            search_query = f"{domain} scam OR phishing OR fake OR legit"
        elif matched_keywords or len(message_text) > 10:
            snippet = " ".join(message_text.split()[:10])
            search_query = f"{snippet} scam OR fake OR warning"

        if search_query:
            try:
                search_response = client.search_and_contents(
                    search_query,
                    type="auto",
                    num_results=2,
                    text={"max_characters": 1000}
                )
                for res in search_response.results:
                    title = getattr(res, "title", "")
                    url = getattr(res, "url", "")
                    text = getattr(res, "text", "")
                    if text:
                        intelligence_list.append(f"Source: {title} ({url})\nFindings: {text[:800]}")
            except Exception as e:
                logger.error(f"Error searching scam intelligence with Exa: {e}")

        return ExaContextResult(
            page_contents="\n---\n".join(page_contents_list),
            web_search_intelligence="\n---\n".join(intelligence_list),
        )


exa_service = ExaService()
