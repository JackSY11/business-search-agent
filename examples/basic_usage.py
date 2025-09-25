#!/usr/bin/env python3
"""
Basic Usage Examples for Business Search Agent

This file demonstrates the most common usage patterns for the business search agent.
"""

import asyncio
from business_search_agent import (
    quick_search,
    business_search_sync,
    business_search_async,
    EnhancedBusinessSearchAgent,
    create_production_config,
    get_search_summary,
    extract_chinese_results,
)


def example_quick_search():
    """Simplest way to perform a search."""
    print("🔍 Quick Search Example")
    print("-" * 40)

    results = quick_search("上海咖啡店推荐", max_results=10)

    print(f"Query: {results['query']}")
    print(f"Success: {results['success']}")
    print(f"Total Results: {results['total_results']}")
    print(f"Chinese Content: {results['chinese_results']}")
    print(f"Execution Time: {results.get('performance', {}).get('execution_time_seconds', 0):.2f}s")

    # Show first result
    if results["results"]:
        first_result = results["results"][0]
        print(f"\nFirst Result:")
        print(f"  Title: {first_result['title'][:60]}...")
        print(f"  Business Value: {first_result['business_value_score']:.1f}")
        print(f"  Quality: {first_result['content_quality_score']:.1f}")
    print()


def example_sync_search():
    """Synchronous search with configuration."""
    print("⚙️ Sync Search with Configuration")
    print("-" * 40)

    config = create_production_config()
    results = business_search_sync("深圳科技公司", max_results=15, config=config)

    # Get summary
    summary = get_search_summary(results)
    print(f"Search Summary:")
    print(f"  Total Results: {summary['total_results']}")
    print(f"  Chinese Content: {summary['chinese_results']}")
    print(f"  Average Quality: {summary['avg_quality']:.1f}")
    print(f"  Chinese Percentage: {summary['chinese_percentage']:.1f}%")

    # Extract only Chinese results
    chinese_results = extract_chinese_results(results)
    print(f"  Chinese-only Results: {len(chinese_results)}")
    print()


async def example_async_search():
    """Asynchronous search with full agent control."""
    print("🚀 Async Search with Full Control")
    print("-" * 40)

    config = create_production_config()
    agent = EnhancedBusinessSearchAgent(config)

    try:
        # Perform search
        results = await agent.search_parallel_optimized(query="北京美食推荐", max_results=20)

        print(f"Search Results:")
        print(f"  Query: {results['query']}")
        print(f"  Success: {results['success']}")
        print(f"  Results: {results['total_results']}")
        print(f"  Chinese: {results['chinese_results']}")
        print(f"  Zhihu: {results['zhihu_results']}")
        print(f"  Engines Used: {', '.join(results['engines_used'])}")
        print(f"  Time: {results['performance']['execution_time_seconds']:.2f}s")

        # Get business metrics
        metrics = agent.get_business_metrics()
        if metrics.get("status") != "no_data":
            print(f"\nAgent Performance:")
            print(f"  Success Rate: {metrics['performance']['success_rate']:.1%}")
            print(f"  Avg Response Time: {metrics['performance']['average_response_time']:.2f}s")

        # Show top results
        print(f"\nTop Results:")
        for i, result in enumerate(results["results"][:3], 1):
            print(f"  {i}. {result['title'][:50]}...")
            print(f"     Business Value: {result['business_value_score']:.1f}")
            print(f"     Source: {result['source_engine']}")
            if result["is_zhihu"]:
                print("     🏆 Zhihu Content")

    finally:
        await agent.close()

    print()


async def example_multiple_searches():
    """Demonstrate multiple searches with the same agent."""
    print("📊 Multiple Searches Example")
    print("-" * 40)

    agent = EnhancedBusinessSearchAgent()
    queries = ["成都旅游", "杭州美食", "广州购物"]

    try:
        for query in queries:
            results = await agent.search_parallel_optimized(query, max_results=8)
            print(
                f"{query}: {results['total_results']} results "
                f"({results['chinese_results']} Chinese)"
            )

        # Final metrics
        metrics = agent.get_business_metrics()
        if metrics.get("status") != "no_data":
            print(f"\nFinal Metrics:")
            print(f"  Total Searches: {metrics['summary']['total_searches']}")
            print(f"  Success Rate: {metrics['performance']['success_rate']:.1%}")
            print(
                f"  Chinese Content Rate: {metrics['content_quality']['chinese_content_rate']:.1%}"
            )

    finally:
        await agent.close()

    print()


def main():
    """Run all examples."""
    print("🏢 Business Search Agent - Usage Examples")
    print("=" * 50)

    # Basic examples
    example_quick_search()
    example_sync_search()

    # Async examples
    asyncio.run(example_async_search())
    asyncio.run(example_multiple_searches())

    print("✅ All examples completed successfully!")


if __name__ == "__main__":
    main()
