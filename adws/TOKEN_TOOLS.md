# Token Monitoring & Analysis Tools

**Zero-overhead tools for monitoring AI costs and optimizing context usage**

These tools run **outside** of Claude Code workflows and analyze execution artifacts without interfering with workflow execution or adding to context.

---

## 🚀 Quick Start

```bash
# Monitor latest workflow
uv run adws/monitor_adw_tokens.py --latest

# Monitor specific workflow
uv run adws/monitor_adw_tokens.py <adw_id>

# Real-time monitoring
uv run adws/monitor_adw_tokens.py --latest --watch

# Analyze context usage
uv run adws/analyze_context_usage.py --latest
```

---

## 📊 monitor_adw_tokens.py

Real-time token usage and cost tracking for ADW workflows.

### Features

- **Token Metrics**: Track input, cache creation, cache read, and output tokens
- **Cost Calculation**: Accurate cost estimates using Claude Sonnet 4.5 pricing
- **Cache Efficiency**: Calculate cache hit ratio and savings
- **Per-Phase Breakdown**: See token usage for each workflow phase
- **Watch Mode**: Continuous monitoring with auto-refresh

### Usage

```bash
# Monitor specific workflow
uv run adws/monitor_adw_tokens.py 19db0b8b

# Monitor latest workflow
uv run adws/monitor_adw_tokens.py --latest

# Continuous monitoring (updates every 10 seconds)
uv run adws/monitor_adw_tokens.py --latest --watch

# Detailed view (shows cache breakdown per phase)
uv run adws/monitor_adw_tokens.py --latest --detail
```

### Example Output

```
============================================================
📊 ADW Token Usage Report: 90a2412d
============================================================

📦 sdlc_planner
  Messages: 99
  Total In: 3,962,233 | Out: 47,949

📦 sdlc_implementor
  Messages: 56
  Total In: 3,465,094 | Out: 33,346

────────────────────────────────────────────────────────────
📈 TOTALS
  Total Messages: 164
  Total Input: 94,664
  Total Cache Create: 966,182
  Total Cache Read: 6,698,037
  Total Output: 82,817
  Cache Efficiency: 87.4%

💰 Estimated Cost (Sonnet 4.5)
  Input: $0.28
  Cache Create: $3.62
  Cache Read: $2.01
  Output: $1.24
  TOTAL: $7.16
  💾 Cache Savings: $18.08
============================================================
```

### How It Works

1. Reads `agents/<adw_id>/*/raw_output.jsonl` files
2. Parses token usage from Claude Code output
3. Aggregates metrics across all phases
4. Calculates costs using current pricing:
   - Input: $3 per 1M tokens
   - Cache Create: $3.75 per 1M tokens
   - Cache Read: $0.30 per 1M tokens (90% cheaper!)
   - Output: $15 per 1M tokens

### Cache Efficiency

**Cache efficiency** shows how well prompt caching is working:
- **High (>80%)**: Excellent - most context is cached
- **Medium (50-80%)**: Good - some cache benefits
- **Low (<50%)**: Poor - consider workflow optimization

**Cache savings** = What you would have paid without caching

---

## 🔍 analyze_context_usage.py

Analyze which files are loaded into context and identify optimization opportunities.

### Features

- **File Usage Analysis**: See which files are read and how often
- **Token Impact**: Understand file size contributions
- **Category Breakdown**: Classify files (source, tests, docs, config, etc.)
- **Optimization Recommendations**: Auto-detect unnecessary context
- **Lock File Detection**: Flag large lock files consuming tokens

### Usage

```bash
# Analyze latest session
uv run adws/analyze_context_usage.py --latest

# Analyze specific session
uv run adws/analyze_context_usage.py <session_id>

# Output as JSON
uv run adws/analyze_context_usage.py --latest --json

# Skip recommendations
uv run adws/analyze_context_usage.py --latest --no-recommendations
```

### Example Output

```
======================================================================
📊 Context Usage Analysis: adw_plan_iso_90a2412d
======================================================================

📈 SUMMARY
  Total file operations: 342
  Unique files read: 87
  Total reads: 198
  Total size: 1,245,678 bytes
  Estimated tokens: 311,419

📁 TOP FILES BY TOKEN COUNT
  1.  45,231 tokens | 3x reads | app/server/routes/queue_routes.py
  2.  32,145 tokens | 2x reads | app/client/src/components/AdwMonitorCard.tsx
  3.  28,492 tokens | 1x reads | bun.lock
  ...

📂 FILE CATEGORIES
  Source Code: 45 files, 245,678 tokens
  Tests: 12 files, 32,456 tokens
  Documentation: 8 files, 12,345 tokens
  Config: 15 files, 8,234 tokens
  Lock Files: 2 files, 28,492 tokens

⚠️  OPTIMIZATION RECOMMENDATIONS

  🔴 1. Lock Files (HIGH priority)
     Reason: Lock files are rarely needed and consume significant tokens
     Token Impact: 28,492 tokens
     Action: Add to .claudeignore: **/*.lock, **/bun.lock
     Affected files: 2
       - bun.lock
       - package-lock.json
```

### How It Works

1. Reads `logs/<session_id>/pre_tool_use.json`
2. Analyzes all Read, Glob, and Grep operations
3. Calculates file sizes and token estimates
4. Categorizes files by type
5. Identifies optimization opportunities

### Recommendations

The tool auto-generates recommendations for:
- **Lock files** (almost never needed)
- **Generated files** (dist/, build/, node_modules/)
- **Large log files** (>5K tokens)
- **Large data files** (>10K tokens)
- **Repeatedly read files** (read >3 times)

---

## 🎯 Use Cases

### 1. Cost Tracking

**Goal**: Understand AI costs per workflow

```bash
# Monitor a workflow as it runs
uv run adws/monitor_adw_tokens.py --latest --watch

# Check costs after completion
uv run adws/monitor_adw_tokens.py --latest --detail
```

**Use for**:
- Budget planning
- Cost attribution per issue
- ROI analysis for automation
- Identifying expensive phases

### 2. Cache Optimization

**Goal**: Improve cache efficiency

```bash
# Check cache performance
uv run adws/monitor_adw_tokens.py --latest

# If cache efficiency < 80%, analyze context
uv run adws/analyze_context_usage.py --latest
```

**Actions based on cache efficiency**:
- **<50%**: Major optimization needed - review .claudeignore
- **50-80%**: Good but improvable - check recommendations
- **>80%**: Excellent - cache working well

### 3. Context Optimization

**Goal**: Reduce unnecessary file reads

```bash
# Analyze context usage
uv run adws/analyze_context_usage.py --latest

# Review recommendations
# Add suggested patterns to .claudeignore
```

**Common optimizations**:
- Exclude lock files (bun.lock, package-lock.json)
- Exclude generated files (dist/, build/)
- Exclude large logs
- Exclude test fixtures

### 4. Performance Debugging

**Goal**: Find bottlenecks in workflows

```bash
# Compare costs across phases
uv run adws/monitor_adw_tokens.py --latest --detail

# Identify phases with unexpectedly high costs
# Check what files are being read in that phase
```

---

## 📐 Cost Benchmarks

Based on actual tac-webbuilder workflows:

| Workflow | Phases | Messages | Total Cost | Cache Savings |
|----------|--------|----------|------------|---------------|
| Full SDLC | 9 | 164 | $7.16 | $18.08 |
| Plan Only | 1 | 99 | $3.85 | $9.45 |
| Build+Test | 2 | 56 | $2.98 | $6.23 |

**Typical cache efficiency**: 85-90%

---

## 🔧 Integration with Observability System

These tools complement tac-webbuilder's observability system:

| Feature | Observability System | Token Tools |
|---------|---------------------|-------------|
| **Phase tracking** | ✅ Real-time status | ✅ Post-execution analysis |
| **Cost tracking** | ✅ Database storage | ✅ Detailed breakdown |
| **Cache metrics** | ❌ Not tracked | ✅ Efficiency & savings |
| **Context analysis** | ❌ Not available | ✅ File usage patterns |
| **Recommendations** | ✅ Workflow optimization | ✅ Context optimization |

**Best practice**: Use both systems together
- Observability system: Real-time monitoring during execution
- Token tools: Post-execution analysis and optimization

---

## 🚨 Common Issues

### "No ADW workflows found"

**Problem**: No agents directory or no workflows executed yet

**Solution**:
```bash
# Check if agents directory exists
ls agents/

# Run a test workflow first
uv run adws/adw_plan_iso.py 123
```

### "No data found for ADW"

**Problem**: Workflow hasn't generated raw_output.jsonl files yet

**Solution**:
- Wait for workflow to complete first phase
- Check `agents/<adw_id>/*/raw_output.jsonl` exists

### "Session not found"

**Problem**: logs/ directory doesn't exist or session ID incorrect

**Solution**:
```bash
# List available sessions
ls logs/

# Use --latest flag instead of specific ID
uv run adws/analyze_context_usage.py --latest
```

---

## 📚 Further Reading

- **Prompt Caching Guide**: https://docs.anthropic.com/claude/docs/prompt-caching
- **Token Optimization**: docs/features/observability-and-logging.md
- **Cost Tracking**: app/server/core/cost_tracker.py

---

## 🎓 Tips & Best Practices

### Maximize Cache Efficiency

1. **Use consistent file ordering** - Files read in same order cache better
2. **Load large files first** - Maximize cache reuse across messages
3. **Avoid re-reading files** - Use context from previous messages
4. **Exclude unnecessary files** - Update .claudeignore regularly

### Minimize Costs

1. **Monitor early and often** - Catch expensive patterns early
2. **Optimize context** - Run analyze_context_usage.py after new features
3. **Review cache efficiency** - Target >80% for production workflows
4. **Use base models** - Reserve Opus for complex tasks only

### Debug Cost Issues

1. **Compare similar workflows** - Find outliers
2. **Check per-phase costs** - Identify expensive phases
3. **Analyze context size** - Look for unexpected file reads
4. **Test with --detail** - Get granular token breakdown

---

**Last Updated**: 2025-12-02
**Ported from**: tac-7 (enhanced for tac-webbuilder)
