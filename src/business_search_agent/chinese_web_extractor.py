#!/usr/bin/env python3
"""
Advanced Chinese Web Content Extractor

Direct website content extraction optimized for Chinese internet.
Provides fallback methods when search engines are unavailable.
"""

import asyncio
import json
import logging
import re
import urllib.parse
from typing import Dict, List, Optional
from urllib.parse import quote

import aiohttp
from bs4 import BeautifulSoup
from fake_useragent import UserAgent

from .agent import BusinessSearchResult
from .config import BusinessConfig


class ChineseWebExtractor:
    """
    Direct Chinese website content extractor.
    
    Provides reliable data extraction from Chinese websites when search engines
    are unavailable or blocked. Supports major Chinese platforms and content sites.
    """

    def __init__(self, config: BusinessConfig = None):
        self.config = config or BusinessConfig(profile="chinese_optimized")
        self.ua = UserAgent()
        
        # Chinese website endpoints for direct access
        self.chinese_sites = {
            "zhihu": {
                "name": "知乎",
                "search_url": "https://www.zhihu.com/api/v4/search_v3?t=general&q={query}&correction=1&offset=0&limit=10",
                "headers": {
                    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
                    "Accept": "application/json, text/plain, */*",
                    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
                    "Referer": "https://www.zhihu.com/",
                },
                "priority": 95,
            },
            "douban": {
                "name": "豆瓣",
                "search_url": "https://www.douban.com/search?q={query}&cat=1002",
                "headers": {
                    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
                    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
                },
                "priority": 85,
                "selectors": {
                    "containers": [".result-list .result", ".search-result .result"],
                    "title": [".title a", "h3 a", ".title"],
                    "url": [".title a", "h3 a"],
                    "description": [".abstract", ".desc", "p"],
                },
            },
            "baidu_zhidao": {
                "name": "百度知道",
                "search_url": "https://zhidao.baidu.com/search?word={query}&ie=utf-8",
                "headers": {
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                    "Accept-Language": "zh-CN,zh;q=0.9",
                },
                "priority": 80,
                "selectors": {
                    "containers": [".list-inner .dl", ".result-list .result-item"],
                    "title": [".dt a", ".title a"],
                    "url": [".dt a", ".title a"],
                    "description": [".dd", ".summary"],
                },
            },
        }

        # Setup session for Chinese websites
        self.session = None
        
        self.logger = logging.getLogger(__name__)

    async def __aenter__(self):
        """Async context manager entry."""
        timeout = aiohttp.ClientTimeout(total=self.config.performance["timeout"])
        connector = aiohttp.TCPConnector(
            limit=self.config.performance["max_concurrent_requests"],
            limit_per_host=self.config.performance["max_concurrent_requests"] // 2,
            ssl=False  # For compatibility with various Chinese sites
        )
        
        self.session = aiohttp.ClientSession(
            timeout=timeout,
            connector=connector,
            trust_env=True
        )
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self.session:
            await self.session.close()

    async def extract_chinese_content(self, query: str, max_results: int = 20) -> Dict:
        """
        Extract content directly from Chinese websites.
        
        Args:
            query: Search query in Chinese
            max_results: Maximum number of results to return
            
        Returns:
            Dict: Structured results from Chinese websites
        """
        self.logger.info(f"🎯 Direct Chinese content extraction for: '{query}'")
        
        all_results = []
        
        # Try each Chinese site
        for site_id, site_config in self.chinese_sites.items():
            try:
                results = await self._extract_from_site(site_id, site_config, query)
                if results:
                    all_results.extend(results)
                    self.logger.info(f"✅ {site_config['name']}: {len(results)} results")
                else:
                    self.logger.info(f"⚠️ {site_config['name']}: No results")
                    
            except Exception as e:
                self.logger.warning(f"❌ {site_config['name']} failed: {e}")
                continue
            
            # Rate limiting
            await asyncio.sleep(1.5)
        
        # Process and rank results
        processed_results = self._process_chinese_results(query, all_results, max_results)
        
        return {
            "query": query,
            "success": len(processed_results) > 0,
            "results": processed_results,
            "total_results": len(processed_results),
            "chinese_results": len(processed_results),  # All are Chinese
            "source": "direct_chinese_extraction",
            "sites_used": list(self.chinese_sites.keys()),
        }

    async def _extract_from_site(self, site_id: str, site_config: Dict, query: str) -> List[BusinessSearchResult]:
        """Extract results from a specific Chinese website."""
        
        if site_id == "zhihu":
            return await self._extract_zhihu_api(site_config, query)
        else:
            return await self._extract_html_site(site_config, query)

    async def _extract_zhihu_api(self, site_config: Dict, query: str) -> List[BusinessSearchResult]:
        """Extract from Zhihu using their API."""
        url = site_config["search_url"].format(query=quote(query))
        headers = site_config["headers"]
        
        try:
            async with self.session.get(url, headers=headers) as response:
                if response.status != 200:
                    return []
                
                data = await response.json()
                results = []
                
                for item in data.get("data", [])[:10]:  # Limit results
                    if item.get("type") in ["search_result", "answer", "article"]:
                        obj = item.get("object", {})
                        
                        title = obj.get("title", "") or obj.get("question", {}).get("title", "")
                        url_path = obj.get("url", "")
                        description = obj.get("excerpt", "") or obj.get("content", "")[:200]
                        
                        if title and len(title) > 5:
                            result = BusinessSearchResult(
                                title=title,
                                url=f"https://www.zhihu.com{url_path}" if url_path.startswith("/") else url_path,
                                description=description,
                                source_engine="知乎API",
                            )
                            results.append(result)
                
                return results
                
        except Exception as e:
            self.logger.debug(f"Zhihu API error: {e}")
            return []

    async def _extract_html_site(self, site_config: Dict, query: str) -> List[BusinessSearchResult]:
        """Extract from HTML-based Chinese website."""
        url = site_config["search_url"].format(query=quote(query))
        headers = site_config["headers"]
        
        try:
            async with self.session.get(url, headers=headers) as response:
                if response.status != 200:
                    return []
                
                html_content = await response.text(encoding='utf-8')
                soup = BeautifulSoup(html_content, 'html.parser')
                
                results = []
                selectors = site_config.get("selectors", {})
                
                # Find containers
                containers = []
                for container_selector in selectors.get("containers", []):
                    containers = soup.select(container_selector)
                    if containers:
                        break
                
                for container in containers[:10]:  # Limit results
                    try:
                        title = self._extract_text_by_selectors(container, selectors.get("title", []))
                        url_elem = self._extract_element_by_selectors(container, selectors.get("url", []))
                        description = self._extract_text_by_selectors(container, selectors.get("description", []))
                        
                        url_path = ""
                        if url_elem and url_elem.get("href"):
                            href = url_elem["href"]
                            if href.startswith("http"):
                                url_path = href
                            elif href.startswith("/"):
                                parsed_url = urllib.parse.urlparse(site_config["search_url"])
                                domain = parsed_url.netloc
                                url_path = f"https://{domain}{href}"
                        
                        if title and len(title) > 5:
                            result = BusinessSearchResult(
                                title=title,
                                url=url_path,
                                description=description or "",
                                source_engine=site_config["name"],
                            )
                            results.append(result)
                            
                    except Exception as e:
                        continue
                
                return results
                
        except Exception as e:
            self.logger.debug(f"HTML site extraction error: {e}")
            return []

    def _extract_text_by_selectors(self, container, selectors: List[str]) -> str:
        """Extract text using multiple selector fallbacks."""
        for selector in selectors:
            elem = container.select_one(selector)
            if elem:
                text = elem.get_text(strip=True)
                if text and len(text) > 3:
                    return text
        return ""

    def _extract_element_by_selectors(self, container, selectors: List[str]):
        """Extract element using multiple selector fallbacks."""
        for selector in selectors:
            elem = container.select_one(selector)
            if elem:
                return elem
        return None

    def _process_chinese_results(self, query: str, results: List[BusinessSearchResult], max_results: int) -> List[Dict]:
        """Process and rank Chinese results."""
        
        # Deduplicate by title
        unique_results = {}
        for result in results:
            title_key = re.sub(r'[^\w\s]', '', result.title.lower().strip())
            if len(title_key) > 10 and title_key not in unique_results:
                unique_results[title_key] = result
        
        # Convert to list and sort by business value
        final_results = list(unique_results.values())
        final_results.sort(key=lambda x: x.business_value_score, reverse=True)
        
        # Convert to dict format and limit results
        return [
            {
                "title": r.title,
                "url": r.url,
                "description": r.description,
                "source_engine": r.source_engine,
                "chinese_content": r.chinese_content,
                "chinese_ratio": r.chinese_ratio,
                "business_value_score": r.business_value_score,
                "content_quality_score": r.content_quality_score,
                "is_zhihu": r.is_zhihu,
                "relevance_score": r.relevance_score,
            }
            for r in final_results[:max_results]
        ]


# Convenience function for direct use
async def extract_chinese_web_data(query: str, max_results: int = 20) -> Dict:
    """
    Convenience function for direct Chinese web content extraction.
    
    Args:
        query: Search query in Chinese
        max_results: Maximum number of results
        
    Returns:
        Dict: Extracted Chinese web content
        
    Example:
        >>> import asyncio
        >>> results = await extract_chinese_web_data("北京美食推荐")
        >>> print(f"Found {results['total_results']} Chinese results")
    """
    async with ChineseWebExtractor() as extractor:
        return await extractor.extract_chinese_content(query, max_results)