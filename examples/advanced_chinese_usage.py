#!/usr/bin/env python3
"""
Advanced Chinese Usage Examples for Business Search Agent

Demonstrates the enhanced Chinese internet data extraction capabilities
including hybrid search, direct Chinese website access, and comprehensive
content analysis.
"""

import asyncio
import json

from business_search_agent import (
    HybridChineseAgent,
    hybrid_chinese_search,
    hybrid_chinese_search_sync,
    extract_chinese_web_data,
    create_chinese_optimized_config,
    quick_search,
)


def example_quick_chinese_search():
    """Simplest way to search Chinese internet with auto-hybrid detection."""
    print("🔍 Quick Chinese Search (Auto-Hybrid)")
    print("-" * 50)

    # Chinese query - will automatically use hybrid approach
    results = quick_search("北京烤鸭推荐", max_results=8)

    print(f"Query: {results['query']}")
    print(f"Success: {results['success']}")
    print(f"Total Results: {results['total_results']}")
    print(f"Chinese Content: {results['chinese_results']}")
    
    if results.get('performance'):
        print(f"Hybrid Approach: {results['performance'].get('hybrid_approach', False)}")
        print(f"Execution Time: {results['performance']['execution_time_seconds']:.2f}s")

    # Show top results with Chinese analysis
    if results["results"]:
        print(f"\nTop Chinese Results:")
        for i, result in enumerate(results["results"][:3], 1):
            print(f"\n{i}. {result['title'][:60]}...")
            print(f"   Chinese Ratio: {result['chinese_ratio']:.2f}")
            print(f"   Business Value: {result['business_value_score']:.1f}/100")
            print(f"   Source: {result['source_engine']}")
            if result.get('from_chinese_sites'):
                print("   🎯 Direct Chinese Website")
    print()


async def example_hybrid_chinese_search():
    """Advanced hybrid Chinese search with full control."""
    print("🌐 Hybrid Chinese Search (Full Control)")
    print("-" * 50)

    agent = HybridChineseAgent(config=create_chinese_optimized_config())

    try:
        queries = ["上海旅游景点", "深圳科技公司", "广州美食推荐"]

        for query in queries:
            print(f"\n🔍 Searching: {query}")
            results = await agent.search_chinese_internet(query, max_results=10)

            print(f"  Success: {results['success']}")
            print(f"  Total: {results['total_results']}")
            print(f"  Chinese: {results['chinese_results']}")
            print(f"  Sources: {results.get('source_breakdown', {})}")
            
            if results.get('performance'):
                print(f"  Time: {results['performance']['execution_time_seconds']:.2f}s")
                print(f"  Search Engines: {results['performance']['search_engines_used']}")
                print(f"  Chinese Sites: {results['performance']['chinese_sites_used']}")

            # Show top result
            if results["results"]:
                top = results["results"][0]
                print(f"  Top Result: {top['title'][:40]}...")
                print(f"  Business Value: {top['business_value_score']:.1f}")

        # Show overall metrics
        metrics = agent.get_metrics()
        if metrics.get("status") != "no_data":
            print(f"\n📊 Agent Performance:")
            print(f"  Total Searches: {metrics['summary']['total_searches']}")
            print(f"  Success Rate: {metrics['performance']['success_rate']:.1%}")
            print(f"  Chinese Content Rate: {metrics['content_quality']['chinese_content_rate']:.1%}")

    finally:
        await agent.close()
    
    print()


async def example_direct_chinese_extraction():
    """Direct Chinese website data extraction."""
    print("🎯 Direct Chinese Website Extraction")
    print("-" * 50)

    queries = ["知乎 Python编程", "豆瓣 电影推荐", "百度知道 旅游攻略"]

    for query in queries:
        print(f"\n🔍 Direct extraction: {query}")
        
        try:
            results = await extract_chinese_web_data(query, max_results=5)
            
            print(f"  Success: {results['success']}")
            print(f"  Results: {results['total_results']}")
            print(f"  Sites Used: {', '.join(results.get('sites_used', []))}")
            
            if results["results"]:
                for i, result in enumerate(results["results"][:2], 1):
                    print(f"  {i}. {result['title'][:50]}...")
                    print(f"     Source: {result['source_engine']}")
                    print(f"     Business Value: {result['business_value_score']:.1f}")
                    
        except Exception as e:
            print(f"  ❌ Error: {e}")

    print()


def example_comparison_analysis():
    """Compare different search approaches."""
    print("📊 Search Approach Comparison")
    print("-" * 50)

    query = "成都美食攻略"
    approaches = []

    # Approach 1: Traditional search
    print("Testing traditional search...")
    try:
        result1 = quick_search(query, max_results=10, use_hybrid=False)
        approaches.append({
            "name": "Traditional Search",
            "success": result1["success"],
            "results": result1["total_results"],
            "chinese": result1["chinese_results"],
            "time": result1.get("performance", {}).get("execution_time_seconds", 0),
        })
    except Exception as e:
        approaches.append({"name": "Traditional Search", "error": str(e)})

    # Approach 2: Hybrid search
    print("Testing hybrid search...")
    try:
        result2 = hybrid_chinese_search_sync(query, max_results=10)
        approaches.append({
            "name": "Hybrid Chinese Search",
            "success": result2["success"],
            "results": result2["total_results"],
            "chinese": result2["chinese_results"],
            "time": result2.get("performance", {}).get("execution_time_seconds", 0),
            "search_engines": result2.get("source_breakdown", {}).get("search_engines", 0),
            "chinese_sites": result2.get("source_breakdown", {}).get("chinese_sites", 0),
        })
    except Exception as e:
        approaches.append({"name": "Hybrid Chinese Search", "error": str(e)})

    # Display comparison
    print(f"\n🎯 Query: {query}")
    print(f"{'Approach':<25} {'Success':<8} {'Results':<8} {'Chinese':<8} {'Time':<6}")
    print("-" * 60)

    for approach in approaches:
        if "error" in approach:
            print(f"{approach['name']:<25} {'ERROR':<8} {approach['error']}")
        else:
            print(f"{approach['name']:<25} "
                  f"{approach['success']:<8} "
                  f"{approach['results']:<8} "
                  f"{approach['chinese']:<8} "
                  f"{approach['time']:<6.2f}s")
            
            if "search_engines" in approach:
                print(f"  └─ Search Engines: {approach['search_engines']}, Chinese Sites: {approach['chinese_sites']}")

    print()


def example_batch_chinese_processing():
    """Batch processing for Chinese content analysis."""
    print("📦 Batch Chinese Content Processing")
    print("-" * 50)

    queries = [
        "北京旅游景点",
        "上海购物中心",
        "深圳科技园区",
        "广州美食餐厅",
        "杭州西湖游玩",
    ]

    print("Processing multiple Chinese queries...")

    results = []
    for i, query in enumerate(queries, 1):
        print(f"  {i}/5: {query}")
        result = hybrid_chinese_search_sync(query, max_results=5)
        results.append({
            "query": query,
            "success": result["success"],
            "total_results": result["total_results"],
            "chinese_results": result["chinese_results"],
            "top_business_value": max(
                (r["business_value_score"] for r in result["results"]), 
                default=0
            ),
        })

    # Summary analysis
    print(f"\n📈 Batch Processing Summary:")
    print(f"  Total Queries: {len(results)}")
    successful = [r for r in results if r["success"]]
    print(f"  Successful: {len(successful)}")
    
    if successful:
        avg_results = sum(r["total_results"] for r in successful) / len(successful)
        avg_chinese = sum(r["chinese_results"] for r in successful) / len(successful)
        avg_business_value = sum(r["top_business_value"] for r in successful) / len(successful)
        
        print(f"  Average Results per Query: {avg_results:.1f}")
        print(f"  Average Chinese Results: {avg_chinese:.1f}")
        print(f"  Average Top Business Value: {avg_business_value:.1f}")
        print(f"  Chinese Content Rate: {(avg_chinese / avg_results * 100) if avg_results > 0 else 0:.1f}%")

    print()


async def main():
    """Run all advanced Chinese usage examples."""
    print("🏢 Business Search Agent - Advanced Chinese Usage Examples")
    print("=" * 70)

    # Basic examples
    example_quick_chinese_search()
    await example_hybrid_chinese_search()
    await example_direct_chinese_extraction()
    
    # Analysis examples
    example_comparison_analysis()
    example_batch_chinese_processing()

    print("🎉 All advanced Chinese examples completed!")
    print("\n💡 Key Takeaways:")
    print("  • Hybrid approach provides better Chinese internet coverage")
    print("  • Direct Chinese sites offer premium content quality")
    print("  • Auto-detection makes it easy to use the right approach")
    print("  • Comprehensive business intelligence for Chinese market analysis")


if __name__ == "__main__":
    asyncio.run(main())