#!/usr/bin/env python3
"""
Cheese Brain Performance Benchmark

Measures search, list, stats, and export performance.
Run before and after bulk imports to measure impact.
"""

import time
import tempfile
from cheese_brain import CheeseBrain

def measure(name, func, iterations=10):
    """Measure function execution time over multiple iterations."""
    times = []
    for _ in range(iterations):
        start = time.perf_counter()
        result = func()
        end = time.perf_counter()
        times.append((end - start) * 1000)  # Convert to milliseconds
    
    avg = sum(times) / len(times)
    min_time = min(times)
    max_time = max(times)
    
    return {
        'name': name,
        'avg_ms': avg,
        'min_ms': min_time,
        'max_ms': max_time,
        'iterations': iterations,
        'result_count': len(result) if isinstance(result, (list, tuple)) else None
    }

def run_benchmark():
    """Run comprehensive performance benchmark."""
    brain = CheeseBrain()
    
    print("🧀 Cheese Brain Performance Benchmark\n")
    print("=" * 70)
    
    # Get baseline stats
    stats = brain.get_stats()
    print(f"\nDatabase Stats:")
    print(f"  Total entities: {stats['total_entities']}")
    print(f"  Deleted entities: {stats['deleted_entities']}")
    print(f"  Database size: {stats['db_size_mb']} MB")
    print(f"  Categories: {len(stats['by_category'])}")
    print()
    
    results = []
    
    # Test 1: Keyword search (common word)
    print("Running keyword search tests...")
    results.append(measure(
        "Keyword search: 'backup'",
        lambda: brain.search("backup", limit=50)
    ))
    
    results.append(measure(
        "Keyword search: 'email'",
        lambda: brain.search("email", limit=50)
    ))
    
    results.append(measure(
        "Keyword search: 'config'",
        lambda: brain.search("config", limit=50)
    ))
    
    # Test 2: Category filter
    print("Running category filter tests...")
    results.append(measure(
        "List all projects",
        lambda: brain.list_entities(category="project", limit=100)
    ))
    
    results.append(measure(
        "List all tools",
        lambda: brain.list_entities(category="tool", limit=100)
    ))
    
    # Test 3: FTS search (if available)
    print("Running FTS tests...")
    try:
        results.append(measure(
            "FTS search: 'backup config'",
            lambda: brain.fts_search("backup config", limit=50)
        ))
        
        results.append(measure(
            "FTS search: 'email monitor'",
            lambda: brain.fts_search("email monitor", limit=50)
        ))
    except RuntimeError:
        print("  ⚠️  FTS not available (index not created)")
    
    # Test 4: Stats gathering
    print("Running stats tests...")
    results.append(measure(
        "Get database stats",
        lambda: brain.get_stats(),
        iterations=20
    ))
    
    # Test 5: Export performance
    print("Running export tests...")
    with tempfile.NamedTemporaryFile(suffix='.json', delete=True) as f:
        results.append(measure(
            "Export to JSON",
            lambda: brain.export_json(f.name),
            iterations=5
        ))
    
    with tempfile.NamedTemporaryFile(suffix='.parquet', delete=True) as f:
        results.append(measure(
            "Export to Parquet",
            lambda: brain.export_parquet(f.name),
            iterations=5
        ))
    
    brain.close()
    
    # Print results
    print("\n" + "=" * 70)
    print("\nBenchmark Results:\n")
    print(f"{'Operation':<40} {'Avg (ms)':<12} {'Min (ms)':<12} {'Max (ms)':<12} {'Results':<10}")
    print("-" * 90)
    
    for r in results:
        result_str = str(r['result_count']) if r['result_count'] is not None else 'N/A'
        print(f"{r['name']:<40} {r['avg_ms']:<12.3f} {r['min_ms']:<12.3f} {r['max_ms']:<12.3f} {result_str:<10}")
    
    print("\n" + "=" * 70)
    print("\n✅ Benchmark complete!")
    
    return results, stats

if __name__ == "__main__":
    run_benchmark()
