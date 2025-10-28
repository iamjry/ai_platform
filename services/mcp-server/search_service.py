"""
Enhanced Web Search Service with Multi-Provider Support
Integrates with RAG for vectorized search results
"""

import logging
import os
from typing import List, Dict, Optional, Any
from datetime import datetime
import asyncio

logger = logging.getLogger(__name__)


class SearchService:
    """Unified search service supporting multiple search providers"""

    def __init__(self):
        self.providers = []
        self._initialize_providers()

    def _initialize_providers(self):
        """Initialize available search providers based on configuration"""
        # Always add DuckDuckGo (free, no API key needed)
        self.providers.append("duckduckgo")
        logger.info("✓ DuckDuckGo search provider enabled (free)")

        # Add Google Custom Search if configured
        if os.getenv("GOOGLE_SEARCH_API_KEY") and os.getenv("GOOGLE_SEARCH_ENGINE_ID"):
            self.providers.append("google")
            logger.info("✓ Google Custom Search provider enabled")

        # Add Tavily if configured
        if os.getenv("TAVILY_API_KEY"):
            self.providers.append("tavily")
            logger.info("✓ Tavily Search provider enabled")

        # Add SerpAPI if configured
        if os.getenv("SERPAPI_API_KEY"):
            self.providers.append("serpapi")
            logger.info("✓ SerpAPI search provider enabled")

        if not self.providers:
            logger.warning("⚠ No search providers configured, using fallback mode")

    async def search_duckduckgo(self, query: str, max_results: int = 5) -> List[Dict[str, Any]]:
        """Search using DuckDuckGo (free, no API key)"""
        try:
            from duckduckgo_search import DDGS

            results = []
            with DDGS() as ddgs:
                search_results = list(ddgs.text(query, max_results=max_results))

                for idx, result in enumerate(search_results):
                    results.append({
                        "title": result.get("title", ""),
                        "url": result.get("href", ""),
                        "snippet": result.get("body", ""),
                        "source": "DuckDuckGo",
                        "rank": idx + 1
                    })

            logger.info(f"DuckDuckGo search returned {len(results)} results for: {query}")
            return results

        except Exception as e:
            logger.error(f"DuckDuckGo search error: {e}")
            return []

    async def search_google(self, query: str, max_results: int = 5) -> List[Dict[str, Any]]:
        """Search using Google Custom Search API"""
        try:
            from googleapiclient.discovery import build

            api_key = os.getenv("GOOGLE_SEARCH_API_KEY")
            search_engine_id = os.getenv("GOOGLE_SEARCH_ENGINE_ID")

            if not api_key or not search_engine_id:
                logger.warning("Google Search API credentials not configured")
                return []

            service = build("customsearch", "v1", developerKey=api_key)

            # Google Custom Search API returns max 10 results per request
            result = service.cse().list(
                q=query,
                cx=search_engine_id,
                num=min(max_results, 10)
            ).execute()

            results = []
            for idx, item in enumerate(result.get("items", [])):
                results.append({
                    "title": item.get("title", ""),
                    "url": item.get("link", ""),
                    "snippet": item.get("snippet", ""),
                    "source": "Google",
                    "rank": idx + 1
                })

            logger.info(f"Google search returned {len(results)} results for: {query}")
            return results

        except Exception as e:
            logger.error(f"Google search error: {e}")
            return []

    async def search_tavily(self, query: str, max_results: int = 5) -> List[Dict[str, Any]]:
        """Search using Tavily API (optimized for AI/LLM applications)"""
        try:
            from tavily import TavilyClient

            api_key = os.getenv("TAVILY_API_KEY")
            if not api_key:
                logger.warning("Tavily API key not configured")
                return []

            client = TavilyClient(api_key=api_key)

            # Tavily search with optimized parameters for AI
            response = client.search(
                query=query,
                max_results=max_results,
                search_depth="advanced",  # More thorough search
                include_answer=True,  # Include AI-generated answer
                include_raw_content=False  # Don't need full HTML
            )

            results = []

            # Add Tavily's AI-generated answer as first result if available
            if response.get("answer"):
                results.append({
                    "title": f"AI Summary: {query}",
                    "url": "",
                    "snippet": response["answer"],
                    "source": "Tavily AI",
                    "rank": 0,
                    "is_ai_summary": True
                })

            # Add search results
            for idx, item in enumerate(response.get("results", [])):
                results.append({
                    "title": item.get("title", ""),
                    "url": item.get("url", ""),
                    "snippet": item.get("content", ""),
                    "source": "Tavily",
                    "rank": idx + 1,
                    "score": item.get("score", 0.0)
                })

            logger.info(f"Tavily search returned {len(results)} results for: {query}")
            return results

        except Exception as e:
            logger.error(f"Tavily search error: {e}")
            return []

    async def search_serpapi(self, query: str, max_results: int = 5) -> List[Dict[str, Any]]:
        """Search using SerpAPI (Google Search aggregator)"""
        try:
            import serpapi

            api_key = os.getenv("SERPAPI_API_KEY")
            if not api_key:
                logger.warning("SerpAPI key not configured")
                return []

            client = serpapi.Client(api_key=api_key)

            response = client.search({
                "engine": "google",
                "q": query,
                "num": max_results
            })

            results = []

            # Extract organic search results
            organic_results = response.get("organic_results", [])
            for idx, item in enumerate(organic_results[:max_results]):
                results.append({
                    "title": item.get("title", ""),
                    "url": item.get("link", ""),
                    "snippet": item.get("snippet", ""),
                    "source": "Google (SerpAPI)",
                    "rank": idx + 1,
                    "position": item.get("position", idx + 1)
                })

            logger.info(f"SerpAPI search returned {len(results)} results for: {query}")
            return results

        except Exception as e:
            logger.error(f"SerpAPI search error: {e}")
            return []

    async def search(
        self,
        query: str,
        max_results: int = 5,
        providers: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Perform web search across multiple providers

        Args:
            query: Search query
            max_results: Maximum results per provider
            providers: List of providers to use (default: all available)

        Returns:
            Dict with combined results from all providers
        """
        if providers is None:
            providers = self.providers

        if not providers:
            logger.warning("No search providers available")
            return {
                "query": query,
                "results": [],
                "providers_used": [],
                "total_results": 0
            }

        # Run searches in parallel
        tasks = []
        for provider in providers:
            if provider == "duckduckgo":
                tasks.append(self.search_duckduckgo(query, max_results))
            elif provider == "google":
                tasks.append(self.search_google(query, max_results))
            elif provider == "tavily":
                tasks.append(self.search_tavily(query, max_results))
            elif provider == "serpapi":
                tasks.append(self.search_serpapi(query, max_results))

        # Wait for all searches to complete
        all_results = await asyncio.gather(*tasks, return_exceptions=True)

        # Combine results
        combined_results = []
        for provider_results in all_results:
            if isinstance(provider_results, list):
                combined_results.extend(provider_results)

        # Sort by rank and remove duplicates by URL
        seen_urls = set()
        unique_results = []
        for result in combined_results:
            url = result.get("url", "")
            if url and url not in seen_urls:
                seen_urls.add(url)
                unique_results.append(result)
            elif not url:  # Include results without URLs (e.g., AI summaries)
                unique_results.append(result)

        return {
            "query": query,
            "results": unique_results[:max_results * len(providers)],
            "providers_used": providers,
            "total_results": len(unique_results),
            "timestamp": datetime.now().isoformat()
        }

    def get_available_providers(self) -> List[str]:
        """Get list of configured and available providers"""
        return self.providers


# Global instance
search_service = SearchService()
