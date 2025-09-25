#!/usr/bin/env python3
"""
Business Metrics and Analytics

Real-time performance monitoring and business intelligence for the search agent.
Tracks performance metrics, success rates, content quality, and business KPIs.
"""

import time
from datetime import datetime, timezone
from typing import Dict, List, Optional
import json


class BusinessMetrics:
    """
    Business analytics and monitoring system.

    Tracks performance metrics, success rates, content quality, and provides
    real-time business intelligence for operational monitoring and optimization.
    """

    def __init__(self, retention_limit: int = 100):
        """
        Initialize metrics tracking system.

        Args:
            retention_limit: Maximum number of metrics to retain in memory
        """
        self.metrics_history: List[Dict] = []
        self.start_time = datetime.now(timezone.utc)
        self.retention_limit = retention_limit

        # Performance counters
        self.total_requests = 0
        self.successful_requests = 0
        self.cache_hits = 0
        self.total_response_time = 0.0

        # Content metrics
        self.chinese_content_found = 0
        self.zhihu_content_found = 0
        self.high_quality_results = 0

        # Engine performance
        self.engine_stats: Dict[str, Dict] = {}

    def track_search_performance(self, query: str, results: Dict, execution_time: float) -> Dict:
        """
        Track comprehensive search performance metrics.

        Args:
            query: The search query
            results: Search results dictionary
            execution_time: Time taken for the search in seconds

        Returns:
            Dict: Recorded metrics for this search
        """
        # Update counters
        self.total_requests += 1
        if results.get("success"):
            self.successful_requests += 1

        if results.get("from_cache"):
            self.cache_hits += 1

        self.total_response_time += execution_time

        # Content quality tracking
        chinese_results = results.get("chinese_results", 0)
        zhihu_results = results.get("zhihu_results", 0)

        self.chinese_content_found += chinese_results
        self.zhihu_content_found += zhihu_results

        # Count high-quality results
        high_quality = sum(
            1 for r in results.get("results", []) if r.get("content_quality_score", 0) >= 70.0
        )
        self.high_quality_results += high_quality

        # Track engine performance
        engines_used = results.get("engines_used", [])
        for engine in engines_used:
            if engine not in self.engine_stats:
                self.engine_stats[engine] = {
                    "requests": 0,
                    "successes": 0,
                    "total_results": 0,
                    "avg_response_time": 0.0,
                }

            self.engine_stats[engine]["requests"] += 1
            if results.get("success"):
                self.engine_stats[engine]["successes"] += 1

            # Estimate results per engine (simplified)
            engine_results = results.get("total_results", 0) // len(engines_used)
            self.engine_stats[engine]["total_results"] += engine_results

        # Create detailed metrics record
        metrics = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "query": query,
            "execution_time_seconds": execution_time,
            "success": results.get("success", False),
            "from_cache": results.get("from_cache", False),
            "total_results": results.get("total_results", 0),
            "engines_used": len(engines_used),
            "engines_names": engines_used,
            "chinese_results": chinese_results,
            "zhihu_results": zhihu_results,
            "high_quality_results": high_quality,
            "average_quality_score": self._calculate_avg_quality(results),
            "average_business_value": self._calculate_avg_business_value(results),
            "performance_tier": self._classify_performance(execution_time),
        }

        # Add to history with retention management
        self.metrics_history.append(metrics)
        if len(self.metrics_history) > self.retention_limit:
            self.metrics_history.pop(0)

        return metrics

    def get_performance_summary(self) -> Dict:
        """
        Get comprehensive business performance summary.

        Returns:
            Dict: Business performance metrics and KPIs
        """
        if not self.metrics_history:
            return {"status": "no_data", "message": "No search data available for analysis"}

        # Use recent data for accurate current performance
        recent_metrics = (
            self.metrics_history[-10:] if len(self.metrics_history) >= 10 else self.metrics_history
        )

        # Calculate core metrics
        total_searches = len(self.metrics_history)
        uptime_hours = (datetime.now(timezone.utc) - self.start_time).total_seconds() / 3600

        # Performance metrics
        avg_response_time = sum(m["execution_time_seconds"] for m in recent_metrics) / len(
            recent_metrics
        )
        success_rate = sum(1 for m in recent_metrics if m["success"]) / len(recent_metrics)
        cache_hit_rate = self.cache_hits / max(self.total_requests, 1)

        # Content quality metrics
        avg_results_per_query = sum(m["total_results"] for m in recent_metrics) / len(
            recent_metrics
        )
        total_results_recent = sum(m["total_results"] for m in recent_metrics)
        chinese_content_rate = sum(m["chinese_results"] for m in recent_metrics) / max(
            total_results_recent, 1
        )

        # Business value metrics
        avg_business_value = sum(m["average_business_value"] for m in recent_metrics) / len(
            recent_metrics
        )
        avg_quality_score = sum(m["average_quality_score"] for m in recent_metrics) / len(
            recent_metrics
        )

        # Performance distribution
        performance_distribution = self._get_performance_distribution(recent_metrics)

        # Engine performance summary
        engine_performance = self._get_engine_performance_summary()

        return {
            "status": "healthy" if success_rate >= 0.8 else "degraded",
            "summary": {
                "total_searches": total_searches,
                "uptime_hours": round(uptime_hours, 2),
                "requests_per_hour": round(total_searches / max(uptime_hours, 0.01), 1),
            },
            "performance": {
                "average_response_time": round(avg_response_time, 2),
                "success_rate": round(success_rate, 3),
                "cache_hit_rate": round(cache_hit_rate, 3),
                "performance_distribution": performance_distribution,
            },
            "content_quality": {
                "average_results_per_query": round(avg_results_per_query, 1),
                "chinese_content_rate": round(chinese_content_rate, 3),
                "average_business_value": round(avg_business_value, 1),
                "average_quality_score": round(avg_quality_score, 1),
            },
            "engines": engine_performance,
            "alerts": self._generate_alerts(success_rate, avg_response_time, cache_hit_rate),
        }

    def get_engine_metrics(self) -> Dict[str, Dict]:
        """Get detailed metrics for each search engine."""
        engine_metrics = {}

        for engine, stats in self.engine_stats.items():
            if stats["requests"] > 0:
                engine_metrics[engine] = {
                    "requests": stats["requests"],
                    "success_rate": stats["successes"] / stats["requests"],
                    "total_results": stats["total_results"],
                    "avg_results_per_request": stats["total_results"] / stats["requests"],
                    "reliability_score": min((stats["successes"] / stats["requests"]) * 100, 100),
                }

        return engine_metrics

    def export_metrics(self, format_type: str = "json") -> str:
        """
        Export metrics data for external analysis.

        Args:
            format_type: Export format ('json', 'csv')

        Returns:
            str: Formatted metrics data
        """
        if format_type.lower() == "json":
            return json.dumps(
                {
                    "export_timestamp": datetime.now(timezone.utc).isoformat(),
                    "summary": self.get_performance_summary(),
                    "metrics_history": self.metrics_history[-50:],  # Last 50 records
                    "engine_stats": self.engine_stats,
                },
                indent=2,
            )
        elif format_type.lower() == "csv":
            # Simple CSV export of recent metrics
            if not self.metrics_history:
                return "No data available"

            headers = [
                "timestamp",
                "query",
                "execution_time",
                "success",
                "total_results",
                "chinese_results",
            ]
            rows = [",".join(headers)]

            for metric in self.metrics_history[-50:]:
                row = [
                    metric["timestamp"],
                    f'"{metric["query"]}"',
                    str(metric["execution_time_seconds"]),
                    str(metric["success"]),
                    str(metric["total_results"]),
                    str(metric["chinese_results"]),
                ]
                rows.append(",".join(row))

            return "\n".join(rows)
        else:
            raise ValueError(f"Unsupported format: {format_type}")

    def reset_metrics(self):
        """Reset all metrics for fresh start."""
        self.metrics_history.clear()
        self.start_time = datetime.now(timezone.utc)
        self.total_requests = 0
        self.successful_requests = 0
        self.cache_hits = 0
        self.total_response_time = 0.0
        self.chinese_content_found = 0
        self.zhihu_content_found = 0
        self.high_quality_results = 0
        self.engine_stats.clear()

    def _calculate_avg_quality(self, results: Dict) -> float:
        """Calculate average content quality score."""
        if not results.get("results"):
            return 0.0
        quality_scores = [r.get("content_quality_score", 0) for r in results["results"]]
        return sum(quality_scores) / len(quality_scores) if quality_scores else 0.0

    def _calculate_avg_business_value(self, results: Dict) -> float:
        """Calculate average business value score."""
        if not results.get("results"):
            return 0.0
        business_scores = [r.get("business_value_score", 0) for r in results["results"]]
        return sum(business_scores) / len(business_scores) if business_scores else 0.0

    def _classify_performance(self, execution_time: float) -> str:
        """Classify performance tier based on execution time."""
        if execution_time < 1.0:
            return "excellent"
        elif execution_time < 3.0:
            return "good"
        elif execution_time < 6.0:
            return "acceptable"
        else:
            return "slow"

    def _get_performance_distribution(self, metrics: List[Dict]) -> Dict:
        """Get distribution of performance tiers."""
        distribution = {"excellent": 0, "good": 0, "acceptable": 0, "slow": 0}

        for metric in metrics:
            tier = metric.get("performance_tier", "unknown")
            if tier in distribution:
                distribution[tier] += 1

        total = len(metrics)
        return {tier: round(count / total, 3) for tier, count in distribution.items()}

    def _get_engine_performance_summary(self) -> Dict:
        """Get summary of engine performance."""
        if not self.engine_stats:
            return {}

        engine_summary = {}
        for engine, stats in self.engine_stats.items():
            if stats["requests"] > 0:
                success_rate = stats["successes"] / stats["requests"]
                engine_summary[engine] = {
                    "success_rate": round(success_rate, 3),
                    "total_requests": stats["requests"],
                    "reliability": (
                        "high"
                        if success_rate >= 0.9
                        else "medium" if success_rate >= 0.7 else "low"
                    ),
                }

        return engine_summary

    def _generate_alerts(
        self, success_rate: float, avg_response_time: float, cache_hit_rate: float
    ) -> List[Dict]:
        """Generate performance alerts based on thresholds."""
        alerts = []

        # Success rate alert
        if success_rate < 0.8:
            alerts.append(
                {
                    "type": "performance",
                    "severity": "high" if success_rate < 0.6 else "medium",
                    "message": f"Success rate below threshold: {success_rate:.1%}",
                    "recommendation": "Check engine connectivity and error rates",
                }
            )

        # Response time alert
        if avg_response_time > 5.0:
            alerts.append(
                {
                    "type": "performance",
                    "severity": "medium",
                    "message": f"Average response time high: {avg_response_time:.1f}s",
                    "recommendation": "Consider optimizing parallel processing or engine selection",
                }
            )

        # Cache hit rate alert
        if cache_hit_rate < 0.1 and self.total_requests > 10:
            alerts.append(
                {
                    "type": "efficiency",
                    "severity": "low",
                    "message": f"Low cache hit rate: {cache_hit_rate:.1%}",
                    "recommendation": "Review caching strategy and TTL settings",
                }
            )

        return alerts
