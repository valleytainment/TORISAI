"""
TORIS AI - Web Tools Implementation
Implements secure web search and browsing capabilities
"""
from typing import Dict, Any, List, Optional
import logging
import httpx
import asyncio
from bs4 import BeautifulSoup
import re
import json
from pydantic import BaseModel, Field

from torisai.core.tool_protocol import registry, ToolDefinition

logger = logging.getLogger("torisai.tools.web")

class SearchResult(BaseModel):
    """Model for search results"""
    title: str
    url: str
    snippet: str

async def web_search(query: str, num_results: int = 5) -> List[SearchResult]:
    """
    Search the web for information
    
    Args:
        query: Search query
        num_results: Number of results to return
        
    Returns:
        List of search results
    """
    try:
        logger.info(f"Searching web for: {query}")
        
        # Use a search API (this is a placeholder - in production would use a real search API)
        # For security and reliability, we'd use a proper search API with authentication
        async with httpx.AsyncClient() as client:
            response = await client.get(
                "https://api.duckduckgo.com/",
                params={
                    "q": query,
                    "format": "json",
                    "no_html": "1",
                    "no_redirect": "1"
                },
                timeout=10.0
            )
            
            if response.status_code != 200:
                logger.error(f"Search API error: {response.status_code}")
                return []
            
            try:
                data = response.json()
                results = []
                
                # Process results
                for result in data.get("Results", [])[:num_results]:
                    results.append(
                        SearchResult(
                            title=result.get("Title", ""),
                            url=result.get("FirstURL", ""),
                            snippet=result.get("Text", "")
                        )
                    )
                
                return results
            except Exception as e:
                logger.error(f"Error parsing search results: {str(e)}")
                return []
    
    except Exception as e:
        logger.error(f"Error in web search: {str(e)}")
        return []

async def fetch_webpage(url: str) -> str:
    """
    Fetch and parse a webpage
    
    Args:
        url: URL to fetch
        
    Returns:
        Parsed webpage content
    """
    try:
        logger.info(f"Fetching webpage: {url}")
        
        async with httpx.AsyncClient() as client:
            response = await client.get(
                url,
                headers={
                    "User-Agent": "TORISAI/1.0 (Local AI Assistant)"
                },
                follow_redirects=True,
                timeout=15.0
            )
            
            if response.status_code != 200:
                logger.error(f"Webpage fetch error: {response.status_code}")
                return f"Error: Could not fetch webpage (status code {response.status_code})"
            
            # Parse HTML
            soup = BeautifulSoup(response.text, "html.parser")
            
            # Remove scripts, styles, and other non-content elements
            for element in soup(["script", "style", "meta", "noscript", "svg"]):
                element.decompose()
            
            # Extract text
            text = soup.get_text(separator="\n", strip=True)
            
            # Clean up text
            text = re.sub(r"\n+", "\n", text)
            text = re.sub(r"\s+", " ", text)
            
            # Truncate if too long
            if len(text) > 10000:
                text = text[:10000] + "...\n[Content truncated due to length]"
            
            return text
    
    except Exception as e:
        logger.error(f"Error fetching webpage: {str(e)}")
        return f"Error: {str(e)}"

# Register tools with the registry
registry.register(
    ToolDefinition(
        name="web_search",
        description="Search the web for information",
        parameters={
            "query": {
                "type": "string",
                "description": "Search query"
            },
            "num_results": {
                "type": "integer",
                "description": "Number of results to return",
                "default": 5
            }
        },
        function=web_search,
        requires_confirmation=False
    )
)

registry.register(
    ToolDefinition(
        name="fetch_webpage",
        description="Fetch and parse a webpage",
        parameters={
            "url": {
                "type": "string",
                "description": "URL to fetch"
            }
        },
        function=fetch_webpage,
        requires_confirmation=False
    )
)
