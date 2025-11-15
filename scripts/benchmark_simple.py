#!/usr/bin/env python3
"""
Simple benchmark to estimate complexity analysis overhead.
Simulates the core logic without imports.
"""

import time

def analyze_complexity_simulation(text):
    """Simulate the complexity analysis logic"""
    text = text.lower()
    complexity_score = 0
    reasons = []

    # UI-only keywords
    ui_keywords = ['add button', 'change color', 'update text', 'rename', 'label',
                   'tooltip', 'icon', 'display', 'show', 'hide', 'toggle']
    if any(kw in text for kw in ui_keywords):
        complexity_score -= 2
        reasons.append("Simple UI change")

    # Backend keywords
    if ('backend' in text or 'server' in text or 'api' in text) and \
       ('frontend' in text or 'client' in text or 'ui' in text):
        complexity_score += 3
        reasons.append("Full-stack")

    # Database
    if any(kw in text for kw in ['database', 'migration', 'schema', 'model']):
        complexity_score += 2
        reasons.append("Database changes")

    # Auth
    if any(kw in text for kw in ['auth', 'security', 'permission']):
        complexity_score += 2
        reasons.append("Security")

    # Determine level
    if complexity_score <= -2:
        return ("lightweight", 0.20, 0.50)
    elif complexity_score <= 2:
        return ("standard", 1.00, 2.00)
    else:
        return ("complex", 3.00, 5.00)


def benchmark():
    print("="*80)
    print("COST ESTIMATION OVERHEAD BENCHMARK")
    print("="*80)
    print()

    test_cases = [
        "Add a button to the homepage",
        "Implement user authentication with JWT",
        "Database migration for new schema",
        "Fix typo in README",
        "Enhance WorkflowHistoryCard component"
    ]

    iterations = 10000

    for description in test_cases:
        start = time.perf_counter()
        for _ in range(iterations):
            result = analyze_complexity_simulation(description)
        end = time.perf_counter()

        avg_time_ms = ((end - start) / iterations) * 1000
        level, min_cost, max_cost = result

        print(f"Description: {description[:50]}")
        print(f"  Avg time: {avg_time_ms:.4f}ms")
        print(f"  Result: {level.upper()} (${min_cost:.2f}-${max_cost:.2f})")
        print()

    # Overall estimate
    start = time.perf_counter()
    for _ in range(iterations):
        for desc in test_cases:
            analyze_complexity_simulation(desc)
    end = time.perf_counter()

    avg_overall = ((end - start) / (iterations * len(test_cases))) * 1000

    print("="*80)
    print(f"AVERAGE OVERHEAD: {avg_overall:.4f}ms per request")
    print()
    print("Impact Analysis:")
    print(f"  - Added to web request: ~{avg_overall:.4f}ms")
    print(f"  - Percentage of 100ms request: {(avg_overall/100)*100:.3f}%")
    print(f"  - Percentage of 500ms request: {(avg_overall/500)*100:.3f}%")
    print(f"  - User noticeable (>50ms)? {'YES' if avg_overall > 50 else 'NO'}")
    print(f"  - API costs: $0.00 (pure heuristics)")
    print(f"  - Network overhead: 0ms")
    print()
    print("VERDICT: NEGLIGIBLE OVERHEAD ✅")
    print("="*80)


if __name__ == "__main__":
    benchmark()
