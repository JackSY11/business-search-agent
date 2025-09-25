#!/usr/bin/env python3
"""
Utility Functions

Convenience functions and utilities for the business search agent.
Provides simple interfaces for common operations.
"""

import asyncio
from typing import Dict, List, Optional
from .agent import EnhancedBusinessSearchAgent
from .config import BusinessConfig


async def business_search_async(query: str, max_results: int = 20, config: Optional[BusinessConfig] = None) -> Dict:
    """
    Async convenience function for business search.
    
    Args:
        query: Search query (Chinese or English)
        max_results: Maximum number of results to return
        config: Optional configuration object
        
    Returns:
        dict: Search results with business intelligence
        
    Example:
        >>> import asyncio
        >>> from business_search_agent import business_search_async
        >>> results = await business_search_async("上海咖啡店推荐")
        >>> print(f"Found {results['total_results']} results")
    """
    agent = EnhancedBusinessSearchAgent(config)
    try:
        return await agent.search_parallel_optimized(query, max_results)
    finally:
        await agent.close()


def business_search_sync(query: str, max_results: int = 20, config: Optional[BusinessConfig] = None) -> Dict:
    """
    Synchronous convenience function for business search.
    
    Args:
        query: Search query (Chinese or English)
        max_results: Maximum number of results to return
        config: Optional configuration object
        
    Returns:
        dict: Search results with business intelligence
        
    Example:
        >>> from business_search_agent import business_search_sync
        >>> results = business_search_sync("北京美食推荐")
        >>> print(f"Found {results['total_results']} results")
    """
    return asyncio.run(business_search_async(query, max_results, config))


def create_production_config() -> BusinessConfig:
    """
    Create a production-ready configuration.
    
    Returns:
        BusinessConfig: Optimized for production use
        
    Example:
        >>> from business_search_agent import create_production_config, business_search_sync
        >>> config = create_production_config()
        >>> results = business_search_sync("深圳科技公司", config=config)
    """
    return BusinessConfig(profile="production")


def create_development_config() -> BusinessConfig:
    """
    Create a development configuration.
    
    Returns:
        BusinessConfig: Optimized for development use
        
    Example:
        >>> from business_search_agent import create_development_config
        >>> config = create_development_config()
    """
    return BusinessConfig(profile="development")


def create_high_performance_config() -> BusinessConfig:
    """
    Create a high-performance configuration.
    
    Returns:
        BusinessConfig: Optimized for maximum performance
        
    Example:
        >>> from business_search_agent import create_high_performance_config
        >>> config = create_high_performance_config()
    """
    return BusinessConfig(profile="high_performance")


def validate_search_results(results: Dict) -> bool:
    """
    Validate search results structure.
    
    Args:
        results: Search results dictionary
        
    Returns:
        bool: True if results are valid
        
    Example:
        >>> from business_search_agent import business_search_sync, validate_search_results
        >>> results = business_search_sync("测试查询")
        >>> is_valid = validate_search_results(results)
    """
    required_keys = ['query', 'success', 'results', 'total_results']
    
    if not isinstance(results, dict):
        return False
    
    for key in required_keys:
        if key not in results:
            return False
    
    if not isinstance(results['results'], list):
        return False
    
    return True


def extract_chinese_results(results: Dict) -> List[Dict]:
    """
    Extract only results with Chinese content.
    
    Args:
        results: Search results dictionary
        
    Returns:
        List[Dict]: Filtered results with Chinese content
        
    Example:
        >>> from business_search_agent import business_search_sync, extract_chinese_results
        >>> results = business_search_sync("上海旅游")
        >>> chinese_results = extract_chinese_results(results)
    """
    if not validate_search_results(results):
        return []
    
    return [r for r in results['results'] if r.get('chinese_content', False)]


def extract_high_quality_results(results: Dict, min_score: float = 70.0) -> List[Dict]:
    """
    Extract results above a quality threshold.
    
    Args:
        results: Search results dictionary
        min_score: Minimum quality score threshold
        
    Returns:
        List[Dict]: High-quality results
        
    Example:
        >>> from business_search_agent import business_search_sync, extract_high_quality_results
        >>> results = business_search_sync("北京餐厅推荐")
        >>> quality_results = extract_high_quality_results(results, min_score=80.0)
    """
    if not validate_search_results(results):
        return []
    
    return [r for r in results['results'] 
            if r.get('content_quality_score', 0) >= min_score]


def get_search_summary(results: Dict) -> Dict:
    """
    Get a summary of search results.
    
    Args:
        results: Search results dictionary
        
    Returns:
        Dict: Summary statistics
        
    Example:
        >>> from business_search_agent import business_search_sync, get_search_summary
        >>> results = business_search_sync("成都美食")
        >>> summary = get_search_summary(results)
        >>> print(f"Average quality: {summary['avg_quality']:.1f}")
    """
    if not validate_search_results(results):
        return {}
    
    if not results['results']:
        return {
            'total_results': 0,
            'chinese_results': 0,
            'zhihu_results': 0,
            'avg_quality': 0.0,
            'avg_business_value': 0.0
        }
    
    chinese_count = sum(1 for r in results['results'] if r.get('chinese_content', False))
    zhihu_count = sum(1 for r in results['results'] if r.get('is_zhihu', False))
    
    quality_scores = [r.get('content_quality_score', 0) for r in results['results']]
    business_scores = [r.get('business_value_score', 0) for r in results['results']]
    
    return {
        'total_results': len(results['results']),
        'chinese_results': chinese_count,
        'zhihu_results': zhihu_count,
        'avg_quality': sum(quality_scores) / len(quality_scores),
        'avg_business_value': sum(business_scores) / len(business_scores),
        'chinese_percentage': (chinese_count / len(results['results'])) * 100,
        'zhihu_percentage': (zhihu_count / len(results['results'])) * 100
    }


class SearchBatch:
    """
    Utility class for batch processing multiple search queries.
    
    Example:
        >>> from business_search_agent import SearchBatch
        >>> batch = SearchBatch()
        >>> await batch.add_query("上海咖啡")
        >>> await batch.add_query("北京美食")
        >>> results = await batch.execute()
    """
    
    def __init__(self, config: Optional[BusinessConfig] = None):
        self.config = config or BusinessConfig()
        self.queries: List[str] = []
        self.max_results_per_query = 20
    
    def add_query(self, query: str) -> 'SearchBatch':
        """Add a query to the batch."""
        self.queries.append(query)
        return self
    
    def set_max_results(self, max_results: int) -> 'SearchBatch':
        """Set maximum results per query."""
        self.max_results_per_query = max_results
        return self
    
    async def execute(self) -> List[Dict]:
        """Execute all queries in the batch."""
        if not self.queries:
            return []
        
        agent = EnhancedBusinessSearchAgent(self.config)
        
        try:
            tasks = []
            for query in self.queries:
                task = agent.search_parallel_optimized(query, self.max_results_per_query)
                tasks.append(task)
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Filter out exceptions
            valid_results = []
            for result in results:
                if not isinstance(result, Exception):
                    valid_results.append(result)
            
            return valid_results
        
        finally:
            await agent.close()
    
    def execute_sync(self) -> List[Dict]:
        """Execute all queries synchronously."""
        return asyncio.run(self.execute())