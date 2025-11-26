"""
Pattern Recognition Log Analysis Script

Analyzes logs/pattern_recognition.log to provide insights:
- Event distribution by type
- Performance metrics (duration, throughput)
- Error analysis
- Pattern prediction insights

Usage:
    cd app/server
    uv run python tests/manual/analyze_pattern_logs.py
"""
import json
from collections import Counter, defaultdict
from typing import Any


def parse_log_file(log_path: str) -> list[dict[str, Any]]:
    """Parse JSON log file into list of log entries."""
    entries = []

    try:
        with open(log_path) as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                if not line:
                    continue

                try:
                    entry = json.loads(line)
                    entries.append(entry)
                except json.JSONDecodeError as e:
                    print(f"Warning: Skipping malformed JSON at line {line_num}: {e}")
                    continue

    except FileNotFoundError:
        print(f"Error: Log file not found at {log_path}")
        print("Run some pattern predictions first to generate logs.")
        return []

    return entries


def analyze_event_distribution(entries: list[dict]) -> None:
    """Analyze and display event type distribution."""
    print("\n" + "=" * 80)
    print("Event Distribution")
    print("=" * 80)

    if not entries:
        print("No log entries found.")
        return

    event_types = Counter(e.get('event_type', 'unknown') for e in entries)

    print(f"\nTotal Events: {len(entries)}\n")
    print(f"{'Event Type':<40} {'Count':<10} {'%':<10}")
    print("-" * 80)

    for event_type, count in event_types.most_common():
        percentage = (count / len(entries)) * 100
        print(f"{event_type:<40} {count:<10} {percentage:>6.1f}%")


def analyze_performance(entries: list[dict]) -> None:
    """Analyze performance metrics from logs."""
    print("\n" + "=" * 80)
    print("Performance Metrics")
    print("=" * 80)

    # Extract duration data
    durations_by_operation = defaultdict(list)

    for entry in entries:
        if 'duration_ms' in entry:
            operation = entry.get('operation') or entry.get('function', 'unknown')
            duration = entry['duration_ms']
            durations_by_operation[operation].append(duration)

    if not durations_by_operation:
        print("\nNo performance data found.")
        return

    print(f"\n{'Operation':<40} {'Count':<10} {'Avg (ms)':<15} {'Min (ms)':<15} {'Max (ms)':<15}")
    print("-" * 80)

    for operation, durations in sorted(durations_by_operation.items()):
        count = len(durations)
        avg_duration = sum(durations) / count
        min_duration = min(durations)
        max_duration = max(durations)

        print(
            f"{operation:<40} {count:<10} {avg_duration:>10.2f}     "
            f"{min_duration:>10.2f}     {max_duration:>10.2f}"
        )


def analyze_errors(entries: list[dict]) -> None:
    """Analyze errors from logs."""
    print("\n" + "=" * 80)
    print("Error Analysis")
    print("=" * 80)

    error_entries = [e for e in entries if e.get('event_type', '').endswith('_error')]

    if not error_entries:
        print("\n✅ No errors found in logs.")
        return

    print(f"\nTotal Errors: {len(error_entries)}\n")

    # Group by error type
    errors_by_type = defaultdict(list)
    for entry in error_entries:
        error_type = entry.get('error_type', 'UnknownError')
        errors_by_type[error_type].append(entry)

    print(f"{'Error Type':<30} {'Count':<10} {'Operations':<40}")
    print("-" * 80)

    for error_type, error_list in sorted(errors_by_type.items()):
        operations = {e.get('operation') or e.get('function', 'unknown') for e in error_list}
        print(f"{error_type:<30} {len(error_list):<10} {', '.join(operations):<40}")

    # Show sample errors
    print("\nSample Errors (first 3):")
    print("-" * 80)

    for idx, entry in enumerate(error_entries[:3], 1):
        print(f"\n{idx}. {entry.get('error_type', 'UnknownError')}: {entry.get('error_message', 'No message')}")
        print(f"   Operation: {entry.get('operation') or entry.get('function', 'unknown')}")
        print(f"   Timestamp: {entry.get('timestamp', 'unknown')}")


def analyze_pattern_predictions(entries: list[dict]) -> None:
    """Analyze pattern prediction insights."""
    print("\n" + "=" * 80)
    print("Pattern Prediction Insights")
    print("=" * 80)

    # Find prediction events
    prediction_events = [e for e in entries if e.get('event_type') == 'predictions_generated']

    if not prediction_events:
        print("\nNo prediction events found.")
        return

    print(f"\nTotal Prediction Operations: {len(prediction_events)}")

    # Aggregate patterns
    all_patterns = []
    total_predictions = 0
    confidence_scores = []

    for event in prediction_events:
        patterns = event.get('patterns', [])
        all_patterns.extend(patterns)
        total_predictions += event.get('prediction_count', 0)

        avg_conf = event.get('avg_confidence', 0.0)
        if avg_conf > 0:
            confidence_scores.append(avg_conf)

    # Pattern frequency
    pattern_counts = Counter(all_patterns)

    print(f"Total Patterns Predicted: {total_predictions}")

    if confidence_scores:
        avg_confidence = sum(confidence_scores) / len(confidence_scores)
        print(f"Average Confidence: {avg_confidence:.2f}")

    print("\nMost Common Patterns:")
    print(f"{'Pattern':<40} {'Count':<10} {'%':<10}")
    print("-" * 80)

    for pattern, count in pattern_counts.most_common(10):
        percentage = (count / total_predictions) * 100 if total_predictions > 0 else 0
        print(f"{pattern:<40} {count:<10} {percentage:>6.1f}%")

    # Keyword matches
    keyword_events = [e for e in entries if e.get('event_type') == 'pattern_keyword_match']

    if keyword_events:
        print("\n\nKeyword Match Analysis:")
        print(f"{'Pattern Type':<30} {'Match Count':<15}")
        print("-" * 80)

        keyword_by_type = Counter(e.get('pattern_type', 'unknown') for e in keyword_events)
        for pattern_type, count in keyword_by_type.most_common():
            print(f"{pattern_type:<30} {count:<15}")


def main():
    """Run log analysis."""
    log_path = "logs/pattern_recognition.log"

    print("\n" + "=" * 80)
    print("Pattern Recognition Log Analysis")
    print("=" * 80)
    print(f"\nAnalyzing: {log_path}")

    entries = parse_log_file(log_path)

    if not entries:
        print("\nNo log entries to analyze.")
        return

    print(f"Found {len(entries)} log entries")

    # Run analyses
    analyze_event_distribution(entries)
    analyze_performance(entries)
    analyze_errors(entries)
    analyze_pattern_predictions(entries)

    print("\n" + "=" * 80)
    print("Analysis Complete")
    print("=" * 80 + "\n")


if __name__ == "__main__":
    main()
