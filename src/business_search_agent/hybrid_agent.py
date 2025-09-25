#!/usr/bin/env python3
"""
Hybrid Chinese Web Search Agent

Combines traditional search engines with direct Chinese website extraction
for maximum reliability and comprehensive Chinese internet data extraction.
"""

import asyncio
import logging
import time
from typing import Dict, List

from .agent import EnhancedBusinessSearchAgent
from .chinese_web_extractor import ChineseWebExtractor
from .config import BusinessConfig
from .metrics import BusinessMetrics


class HybridChineseAgent:
    """
    Hybrid agent that combines multiple search strategies for Chinese content.
    
    Uses both traditional search engines and direct Chinese website extraction
    to provide the most comprehensive and reliable results for Chinese internet data.
    """

    def __init__(self, config: BusinessConfig = None):
        self.config = config or BusinessConfig(profile="chinese_optimized")
        self.metrics = BusinessMetrics()
        
        # Initialize sub-agents
        self.search_agent = EnhancedBusinessSearchAgent(self.config)
        self.chinese_extractor = None  # Will be initialized as needed
        
        self.logger = logging.getLogger(__name__)

    async def search_chinese_internet(self, query: str, max_results: int = 20) -> Dict:
        """
        Comprehensive Chinese internet search using hybrid approach.
        
        Args:
            query: Search query (Chinese or English)
            max_results: Maximum number of results to return
            
        Returns:
            Dict: Combined results from multiple sources
        """
        start_time = time.time()
        self.logger.info(f"🌐 Hybrid Chinese internet search for: '{query}'")
        
        # Strategy 1: Try traditional search engines first
        search_results = None
        try:
            self.logger.info("📡 Attempting traditional search engines...")
            search_results = await self.search_agent.search_parallel_optimized(
                query, max_results=max_results
            )
            
            if search_results.get("success") and search_results.get("total_results", 0) > 0:
                self.logger.info(f"✅ Search engines: {search_results['total_results']} results")
            else:
                self.logger.info("⚠️ Search engines returned no results")
                search_results = None
                
        except Exception as e:
            self.logger.warning(f"❌ Search engines failed: {e}")
            search_results = None
        
        # Strategy 2: Direct Chinese website extraction
        chinese_results = None
        try:
            self.logger.info("🎯 Attempting direct Chinese website extraction...")
            async with ChineseWebExtractor(self.config) as extractor:
                chinese_results = await extractor.extract_chinese_content(
                    query, max_results=max_results
                )
                
                if chinese_results.get("success") and chinese_results.get("total_results", 0) > 0:
                    self.logger.info(f"✅ Chinese sites: {chinese_results['total_results']} results")
                else:
                    self.logger.info("⚠️ Chinese sites returned no results")
                    chinese_results = None
                    
        except Exception as e:
            self.logger.warning(f"❌ Chinese extraction failed: {e}")
            chinese_results = None
        
        # Combine and process results
        final_result = self._combine_results(
            query, search_results, chinese_results, max_results
        )
        
        # Add performance metrics
        execution_time = time.time() - start_time
        final_result["performance"] = {
            "execution_time_seconds": execution_time,
            "search_engines_used": search_results is not None,
            "chinese_sites_used": chinese_results is not None,
            "hybrid_approach": True,
        }
        
        # Track metrics
        self.metrics.track_search_performance(query, final_result, execution_time)
        
        self.logger.info(
            f"🎉 Hybrid search completed in {execution_time:.2f}s: "
            f"{final_result['total_results']} total results "
            f"({final_result['chinese_results']} Chinese)"
        )
        
        return final_result

    def _combine_results(
        self, 
        query: str, 
        search_results: Dict = None, 
        chinese_results: Dict = None,
        max_results: int = 20
    ) -> Dict:
        """Combine results from different sources intelligently."""
        
        all_results = []
        engines_used = []
        
        # Add search engine results
        if search_results and search_results.get("results"):
            all_results.extend(search_results["results"])
            engines_used.extend(search_results.get("engines_used", []))
            
        # Add Chinese site results
        if chinese_results and chinese_results.get("results"):
            # Mark Chinese results as high priority
            chinese_site_results = chinese_results["results"]
            for result in chinese_site_results:
                result["from_chinese_sites"] = True
                # Boost business value for direct Chinese content
                if result.get("business_value_score", 0) < 80:
                    result["business_value_score"] = result.get("business_value_score", 0) + 15
            
            all_results.extend(chinese_site_results)
            engines_used.extend(chinese_results.get("sites_used", []))
        
        # Check if we have any results
        if not all_results:
            return {
                "query": query,
                "success": False,
                "results": [],
                "total_results": 0,
                "chinese_results": 0,
                "zhihu_results": 0,
                "engines_used": engines_used,
                "error": "No results from any source (search engines or Chinese sites)",
                "fallback_suggestions": self._generate_fallback_suggestions(query),
            }
        
        # Deduplicate by title similarity
        unique_results = self._deduplicate_hybrid_results(all_results)
        
        # Sort by combined score (business value + Chinese bonus)
        unique_results.sort(key=self._calculate_hybrid_score, reverse=True)
        
        # Limit results
        final_results = unique_results[:max_results]
        
        # Calculate statistics
        chinese_count = sum(1 for r in final_results if r.get("chinese_content", False))
        zhihu_count = sum(1 for r in final_results if r.get("is_zhihu", False))
        
        return {
            "query": query,
            "success": True,
            "results": final_results,
            "total_results": len(final_results),
            "chinese_results": chinese_count,
            "zhihu_results": zhihu_count,
            "engines_used": engines_used,
            "source_breakdown": {
                "search_engines": len(search_results.get("results", [])) if search_results else 0,
                "chinese_sites": len(chinese_results.get("results", [])) if chinese_results else 0,
            },
        }

    def _deduplicate_hybrid_results(self, results: List[Dict]) -> List[Dict]:
        """Smart deduplication for hybrid results."""
        unique_results = []
        seen_titles = set()
        seen_urls = set()
        
        for result in results:
            # Normalize title for comparison
            title_key = result.get("title", "").lower().strip()
            title_key = "".join(c for c in title_key if c.isalnum() or c.isspace())
            
            url_key = result.get("url", "").lower().strip()
            
            # Skip if too short or already seen
            if len(title_key) < 10:
                continue
                
            if title_key in seen_titles or url_key in seen_urls:
                continue
            
            seen_titles.add(title_key)
            seen_urls.add(url_key)
            unique_results.append(result)
        
        return unique_results

    def _calculate_hybrid_score(self, result: Dict) -> float:
        """Calculate hybrid scoring for result ranking."""
        base_score = result.get("business_value_score", 0)
        
        # Chinese content bonus
        if result.get("chinese_content", False):
            base_score += 10
        
        # Direct Chinese site bonus
        if result.get("from_chinese_sites", False):
            base_score += 15
        
        # Zhihu premium bonus
        if result.get("is_zhihu", False):
            base_score += 20
        
        # Quality bonus
        quality_score = result.get("content_quality_score", 0)
        if quality_score > 70:
            base_score += 10
        elif quality_score > 50:
            base_score += 5
        
        # Chinese ratio bonus
        chinese_ratio = result.get("chinese_ratio", 0)
        if chinese_ratio > 0.8:
            base_score += 15
        elif chinese_ratio > 0.5:
            base_score += 8
        
        return base_score

    def _generate_fallback_suggestions(self, query: str) -> List[str]:
        """Generate fallback suggestions when no results are found."""
        suggestions = [
            "Try using more specific Chinese keywords",
            "Check if the query contains proper Chinese characters",
            "Try shorter, more common search terms",
            "Use brand names or location names in Chinese",
        ]
        
        # Add query-specific suggestions
        if len(query) < 5:
            suggestions.append("Try using longer, more descriptive queries")
        
        if not any('\u4e00' <= c <= '\u9fff' for c in query):
            suggestions.append("Try using Chinese characters instead of English")
        
        return suggestions[:3]  # Limit to top 3 suggestions

    async def close(self):
        """Clean up resources."""
        await self.search_agent.close()

    def get_metrics(self) -> Dict:
        """Get performance metrics."""
        return self.metrics.get_performance_summary()


# Convenience functions
async def hybrid_chinese_search(query: str, max_results: int = 20) -> Dict:
    """
    Convenience function for hybrid Chinese internet search.
    
    Args:
        query: Search query (Chinese or English)
        max_results: Maximum number of results
        
    Returns:
        Dict: Comprehensive search results
        
    Example:
        >>> import asyncio
        >>> results = await hybrid_chinese_search("北京烤鸭推荐")
        >>> print(f"Found {results['total_results']} results")
    """
    agent = HybridChineseAgent()
    try:
        return await agent.search_chinese_internet(query, max_results)
    finally:
        await agent.close()


def hybrid_chinese_search_sync(query: str, max_results: int = 20) -> Dict:
    """
    Synchronous version of hybrid Chinese search.
    
    Args:
        query: Search query (Chinese or English)  
        max_results: Maximum number of results
        
    Returns:
        Dict: Comprehensive search results
        
    Example:
        >>> results = hybrid_chinese_search_sync("上海美食推荐")
        >>> print(f"Found {results['total_results']} results")
    """
    return asyncio.run(hybrid_chinese_search(query, max_results))