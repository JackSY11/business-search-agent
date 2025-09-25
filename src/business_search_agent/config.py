#!/usr/bin/env python3
"""
Business Configuration Management

Centralized configuration for production deployment with environment-based profiles.
Supports development, staging, and production configurations.
"""

import os
from typing import Dict, List
from dataclasses import dataclass


@dataclass
class BusinessConfig:
    """
    Centralized configuration for business deployment.

    Supports environment variables for production deployment:
    - SEARCH_TIMEOUT: Request timeout in seconds
    - MAX_CONCURRENT: Maximum concurrent requests
    - RATE_LIMIT: Rate limit per engine (seconds)
    - CACHE_TTL: Cache time-to-live (seconds)
    - PARALLEL_ENABLED: Enable parallel processing
    - MAX_RESULTS: Maximum results per query
    - PRIORITY_ENGINES: Comma-separated list of preferred engines
    - QUALITY_THRESHOLD: Minimum content quality score
    - CHINESE_THRESHOLD: Minimum Chinese content ratio
    - ZHIHU_BOOST: Enable Zhihu content prioritization
    - ENABLE_METRICS: Enable business metrics tracking
    - LOG_LEVEL: Logging level (DEBUG, INFO, WARNING, ERROR)
    """

    def __init__(self, profile: str = "production"):
        """
        Initialize configuration with environment-specific profile.

        Args:
            profile: Configuration profile ('development', 'production', 'high_performance')
        """
        self.profile = profile
        self.performance = self._get_performance_config()
        self.business = self._get_business_config()
        self.monitoring = self._get_monitoring_config()
        self.engines = self._get_engine_config()

    def _get_performance_config(self) -> Dict:
        """Get performance-related configuration."""
        defaults = self._get_profile_defaults()

        return {
            "timeout": int(os.getenv("SEARCH_TIMEOUT", defaults["timeout"])),
            "max_concurrent_requests": int(os.getenv("MAX_CONCURRENT", defaults["max_concurrent"])),
            "rate_limit_per_engine": float(os.getenv("RATE_LIMIT", defaults["rate_limit"])),
            "cache_ttl": int(os.getenv("CACHE_TTL", defaults["cache_ttl"])),
            "parallel_enabled": os.getenv("PARALLEL_ENABLED", defaults["parallel_enabled"]).lower()
            == "true",
            "connection_pool_size": int(
                os.getenv("CONNECTION_POOL_SIZE", defaults.get("connection_pool_size", 20))
            ),
        }

    def _get_business_config(self) -> Dict:
        """Get business logic configuration."""
        defaults = self._get_profile_defaults()

        return {
            "max_results_per_query": int(os.getenv("MAX_RESULTS", defaults["max_results"])),
            "priority_engines": os.getenv("PRIORITY_ENGINES", defaults["priority_engines"]).split(
                ","
            ),
            "content_quality_threshold": float(
                os.getenv("QUALITY_THRESHOLD", defaults["quality_threshold"])
            ),
            "chinese_content_threshold": float(
                os.getenv("CHINESE_THRESHOLD", defaults["chinese_threshold"])
            ),
            "zhihu_boost_enabled": os.getenv("ZHIHU_BOOST", defaults["zhihu_boost"]).lower()
            == "true",
            "deduplication_enabled": os.getenv("DEDUPLICATION_ENABLED", "true").lower() == "true",
        }

    def _get_monitoring_config(self) -> Dict:
        """Get monitoring and alerting configuration."""
        return {
            "enable_metrics": os.getenv("ENABLE_METRICS", "true").lower() == "true",
            "alert_threshold": float(os.getenv("ALERT_THRESHOLD", "0.8")),
            "log_level": os.getenv("LOG_LEVEL", "INFO").upper(),
            "metrics_retention": int(os.getenv("METRICS_RETENTION", "100")),
        }

    def _get_engine_config(self) -> Dict:
        """Get search engine configuration."""
        return {
            "startpage": {
                "name": "Startpage",
                "priority": 100,
                "url_template": "https://startpage.com/sp/search?query={query}",
                "selectors": {
                    "containers": ["div.result", ".w-gl__result"],
                    "title": ["h3", "h2", ".w-gl__result-title"],
                    "url": ["a[href]", ".w-gl__result-url"],
                    "description": [".description", "p", "span", ".w-gl__description"],
                },
                "business_value": 95,
                "timeout_multiplier": 1.2,
            },
            "bing": {
                "name": "Bing",
                "priority": 90,
                "url_template": "https://bing.com/search?q={query}",
                "selectors": {
                    "containers": ["li.b_algo", ".b_algo"],
                    "title": ["h2", ".b_title", "h3"],
                    "url": ["h2 a", "a[href]", ".b_title a"],
                    "description": [".b_caption p", ".b_snippet", "p"],
                },
                "business_value": 85,
                "timeout_multiplier": 1.0,
            },
            "yandex": {
                "name": "Yandex",
                "priority": 80,
                "url_template": "https://yandex.com/search/?text={query}",
                "selectors": {
                    "containers": ["div.serp-item", ".serp-item", "li.serp-item"],
                    "title": ["h2", "h3", ".serp-item__title"],
                    "url": ["a[href]", ".serp-item__title a"],
                    "description": [".text-container", ".snippet", "div", ".serp-item__text"],
                },
                "business_value": 70,
                "timeout_multiplier": 1.1,
            },
        }

    def _get_profile_defaults(self) -> Dict:
        """Get default configuration values based on profile."""
        profiles = {
            "development": {
                "timeout": 10,
                "max_concurrent": 2,
                "rate_limit": 2.0,
                "cache_ttl": 300,  # 5 minutes
                "parallel_enabled": "true",
                "max_results": 15,
                "priority_engines": "bing,yandex",
                "quality_threshold": 50.0,
                "chinese_threshold": 0.2,
                "zhihu_boost": "false",
            },
            "production": {
                "timeout": 12,
                "max_concurrent": 6,
                "rate_limit": 1.0,
                "cache_ttl": 3600,  # 1 hour
                "parallel_enabled": "true",
                "max_results": 25,
                "priority_engines": "startpage,bing,yandex",
                "quality_threshold": 70.0,
                "chinese_threshold": 0.3,
                "zhihu_boost": "true",
            },
            "high_performance": {
                "timeout": 15,
                "max_concurrent": 10,
                "rate_limit": 0.5,
                "cache_ttl": 7200,  # 2 hours
                "parallel_enabled": "true",
                "max_results": 50,
                "priority_engines": "startpage,bing,yandex",
                "quality_threshold": 60.0,
                "chinese_threshold": 0.3,
                "zhihu_boost": "true",
            },
        }

        return profiles.get(self.profile, profiles["production"])

    def get_user_agent_pool(self) -> List[str]:
        """Get pool of user agents for rotation."""
        return [
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        ]

    def to_dict(self) -> Dict:
        """Convert configuration to dictionary."""
        return {
            "profile": self.profile,
            "performance": self.performance,
            "business": self.business,
            "monitoring": self.monitoring,
            "engines": list(self.engines.keys()),
        }

    def __repr__(self) -> str:
        return f"BusinessConfig(profile='{self.profile}', engines={len(self.engines)})"
