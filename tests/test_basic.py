#!/usr/bin/env python3
"""
Basic Test Suite for Business Search Agent

Tests core functionality, configuration, and utilities.
"""

import pytest
import asyncio
from unittest.mock import Mock, patch
from business_search_agent import (
    BusinessConfig,
    BusinessMetrics,
    EnhancedBusinessSearchAgent,
    BusinessSearchResult,
    business_search_sync,
    validate_search_results,
    extract_chinese_results,
    get_search_summary,
)


class TestBusinessConfig:
    """Test configuration management."""

    def test_production_config(self):
        """Test production configuration defaults."""
        config = BusinessConfig(profile="production")

        assert config.profile == "production"
        assert config.performance["timeout"] == 12
        assert config.performance["max_concurrent_requests"] == 6
        assert config.performance["parallel_enabled"] is True
        assert config.business["max_results_per_query"] == 25
        assert config.business["zhihu_boost_enabled"] is True
        assert len(config.engines) == 3

    def test_development_config(self):
        """Test development configuration."""
        config = BusinessConfig(profile="development")

        assert config.profile == "development"
        assert config.performance["max_concurrent_requests"] == 2
        assert config.business["quality_threshold"] == 50.0
        assert config.business["zhihu_boost_enabled"] is False

    def test_high_performance_config(self):
        """Test high performance configuration."""
        config = BusinessConfig(profile="high_performance")

        assert config.profile == "high_performance"
        assert config.performance["max_concurrent_requests"] == 10
        assert config.business["max_results_per_query"] == 50
        assert config.performance["rate_limit_per_engine"] == 0.5

    def test_config_to_dict(self):
        """Test configuration serialization."""
        config = BusinessConfig()
        config_dict = config.to_dict()

        assert isinstance(config_dict, dict)
        assert "profile" in config_dict
        assert "performance" in config_dict
        assert "business" in config_dict
        assert "engines" in config_dict

    def test_user_agent_pool(self):
        """Test user agent pool generation."""
        config = BusinessConfig()
        user_agents = config.get_user_agent_pool()

        assert isinstance(user_agents, list)
        assert len(user_agents) >= 4
        assert all("Mozilla" in ua for ua in user_agents)


class TestBusinessMetrics:
    """Test metrics and analytics."""

    def test_metrics_initialization(self):
        """Test metrics initialization."""
        metrics = BusinessMetrics()

        assert metrics.total_requests == 0
        assert metrics.successful_requests == 0
        assert metrics.cache_hits == 0
        assert len(metrics.metrics_history) == 0

    def test_track_search_performance(self):
        """Test performance tracking."""
        metrics = BusinessMetrics()

        # Mock results
        results = {
            "success": True,
            "total_results": 5,
            "chinese_results": 4,
            "zhihu_results": 1,
            "engines_used": ["Bing", "Yandex"],
            "results": [
                {"content_quality_score": 75.0, "business_value_score": 85.0},
                {"content_quality_score": 80.0, "business_value_score": 90.0},
            ],
        }

        tracked = metrics.track_search_performance("测试查询", results, 2.5)

        assert metrics.total_requests == 1
        assert metrics.successful_requests == 1
        assert len(metrics.metrics_history) == 1
        assert tracked["query"] == "测试查询"
        assert tracked["success"] is True
        assert tracked["execution_time_seconds"] == 2.5

    def test_performance_summary(self):
        """Test performance summary generation."""
        metrics = BusinessMetrics()

        # Add some test data
        for i in range(5):
            results = {
                "success": True,
                "total_results": 10,
                "chinese_results": 8,
                "zhihu_results": 2,
                "engines_used": ["Bing"],
                "results": [{"content_quality_score": 75.0, "business_value_score": 80.0}],
            }
            metrics.track_search_performance(f"query_{i}", results, 2.0)

        summary = metrics.get_performance_summary()

        assert summary["status"] == "healthy"
        assert summary["performance"]["success_rate"] == 1.0
        assert summary["performance"]["average_response_time"] == 2.0
        assert summary["summary"]["total_searches"] == 5

    def test_export_metrics(self):
        """Test metrics export functionality."""
        metrics = BusinessMetrics()

        # Add test data
        results = {
            "success": True,
            "total_results": 5,
            "chinese_results": 3,
            "zhihu_results": 1,
            "engines_used": ["Bing"],
            "results": [],
        }
        metrics.track_search_performance("test", results, 1.5)

        # Test JSON export
        json_export = metrics.export_metrics("json")
        assert isinstance(json_export, str)
        assert "export_timestamp" in json_export

        # Test CSV export
        csv_export = metrics.export_metrics("csv")
        assert isinstance(csv_export, str)
        assert "timestamp,query" in csv_export


class TestBusinessSearchResult:
    """Test search result data structure."""

    def test_result_creation(self):
        """Test result creation with automatic calculations."""
        result = BusinessSearchResult(
            title="上海咖啡店推荐 - 知乎",
            url="https://zhihu.com/question/123",
            description="上海最好的咖啡店有哪些？这里有详细的推荐列表...",
            source_engine="Bing",
        )

        assert result.chinese_ratio > 0.5
        assert result.chinese_content is True
        assert result.is_zhihu is True
        assert result.content_quality_score > 50.0
        assert result.business_value_score > 50.0
        assert result.extraction_timestamp != ""

    def test_chinese_ratio_calculation(self):
        """Test Chinese content ratio calculation."""
        # High Chinese content
        result1 = BusinessSearchResult(
            title="北京美食推荐",
            url="http://example.com",
            description="这是一个关于北京美食的详细介绍",
            source_engine="Test",
        )
        assert result1.chinese_ratio > 0.8

        # Low Chinese content
        result2 = BusinessSearchResult(
            title="Beijing Food Recommendations",
            url="http://example.com",
            description="This is a detailed introduction about Beijing food",
            source_engine="Test",
        )
        assert result2.chinese_ratio < 0.1

    def test_business_value_calculation(self):
        """Test business value score calculation."""
        # Zhihu content should have higher business value
        zhihu_result = BusinessSearchResult(
            title="产品经理面试技巧",
            url="https://zhihu.com/question/456",
            description="知乎上关于产品经理面试的详细分析",
            source_engine="Startpage",
        )

        regular_result = BusinessSearchResult(
            title="Product Manager Interview Tips",
            url="https://example.com/tips",
            description="Tips for product manager interviews",
            source_engine="Bing",
        )

        assert zhihu_result.business_value_score > regular_result.business_value_score


class TestUtilityFunctions:
    """Test utility functions."""

    def test_validate_search_results(self):
        """Test search results validation."""
        # Valid results
        valid_results = {
            "query": "test",
            "success": True,
            "results": [{"title": "Test"}],
            "total_results": 1,
        }
        assert validate_search_results(valid_results) is True

        # Invalid results
        invalid_results = {"query": "test"}
        assert validate_search_results(invalid_results) is False

        # Wrong type
        assert validate_search_results("not a dict") is False

    def test_extract_chinese_results(self):
        """Test Chinese content extraction."""
        results = {
            "query": "test",
            "success": True,
            "results": [
                {"chinese_content": True, "title": "中文标题"},
                {"chinese_content": False, "title": "English Title"},
                {"chinese_content": True, "title": "另一个中文标题"},
            ],
            "total_results": 3,
        }

        chinese_only = extract_chinese_results(results)
        assert len(chinese_only) == 2
        assert all(r["chinese_content"] for r in chinese_only)

    def test_get_search_summary(self):
        """Test search summary generation."""
        results = {
            "query": "test",
            "success": True,
            "results": [
                {
                    "chinese_content": True,
                    "is_zhihu": True,
                    "content_quality_score": 80.0,
                    "business_value_score": 90.0,
                },
                {
                    "chinese_content": True,
                    "is_zhihu": False,
                    "content_quality_score": 70.0,
                    "business_value_score": 75.0,
                },
            ],
            "total_results": 2,
        }

        summary = get_search_summary(results)

        assert summary["total_results"] == 2
        assert summary["chinese_results"] == 2
        assert summary["zhihu_results"] == 1
        assert summary["chinese_percentage"] == 100.0
        assert summary["zhihu_percentage"] == 50.0
        assert summary["avg_quality"] == 75.0


class TestEnhancedBusinessSearchAgent:
    """Test the main search agent."""

    @pytest.fixture
    def agent(self):
        """Create a test agent."""
        config = BusinessConfig(profile="development")
        return EnhancedBusinessSearchAgent(config)

    def test_agent_initialization(self, agent):
        """Test agent initialization."""
        assert agent.config.profile == "development"
        assert agent.metrics is not None
        assert agent.cache is not None
        assert len(agent.engines) == 3

    def test_priority_engines(self, agent):
        """Test engine priority ordering."""
        engines = agent._get_priority_engines()

        assert isinstance(engines, list)
        assert len(engines) > 0
        # Should be ordered by priority (highest first)
        priorities = [agent.engines[e]["priority"] for e in engines]
        assert priorities == sorted(priorities, reverse=True)

    def test_cache_key_generation(self, agent):
        """Test cache key generation."""
        key1 = agent._generate_cache_key("test query", 20)
        key2 = agent._generate_cache_key("test query", 20)
        key3 = agent._generate_cache_key("different query", 20)

        assert key1 == key2  # Same inputs should produce same key
        assert key1 != key3  # Different inputs should produce different keys
        assert len(key1) == 32  # MD5 hash length

    def test_deduplication(self, agent):
        """Test result deduplication."""
        results = [
            BusinessSearchResult("重复标题", "http://1.com", "描述1", "Engine1"),
            BusinessSearchResult("重复标题", "http://2.com", "描述2", "Engine2"),
            BusinessSearchResult("不同标题", "http://3.com", "描述3", "Engine1"),
        ]

        unique_results = agent._deduplicate_results(results)

        assert len(unique_results) == 2  # Should remove one duplicate
        titles = [r.title for r in unique_results]
        assert "不同标题" in titles


# Integration test (mock required for actual network calls)
@patch("business_search_agent.agent.aiohttp.ClientSession.get")
async def test_integration_mock(mock_get):
    """Test integration with mocked network calls."""
    # Mock response
    mock_response = Mock()
    mock_response.status = 200
    mock_response.text = Mock(
        return_value=asyncio.coroutine(
            lambda: '<html><div class="b_algo"><h2>Test Title</h2><p>Test description</p></div></html>'
        )()
    )

    mock_get.return_value.__aenter__.return_value = mock_response

    agent = EnhancedBusinessSearchAgent()
    try:
        # This would normally make network calls, but they're mocked
        results = await agent.search_parallel_optimized("test query", max_results=5)

        assert isinstance(results, dict)
        assert "success" in results
        assert "query" in results

    finally:
        await agent.close()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
