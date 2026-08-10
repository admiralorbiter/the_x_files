"""Diagnose production run slowdown by analyzing latency patterns."""
import json
from pathlib import Path
from datetime import datetime

RUN = Path("results/runs/20260809_233031_study_1_production")
lines = (RUN / "responses.raw.jsonl").read_text(encoding="utf-8").strip().split("\n")
records = [json.loads(l) for l in lines]

print(f"Total completed: {len(records)}/2304 ({len(records)/2304*100:.1f}%)")

timestamps = [r["timestamp_iso"] for r in records]
first_t = datetime.fromisoformat(timestamps[0])
last_t = datetime.fromisoformat(timestamps[-1])
elapsed = (last_t - first_t).total_seconds() / 3600
print(f"First cell: {timestamps[0]}")
print(f"Last cell:  {timestamps[-1]}")
print(f"Elapsed: {elapsed:.1f} hours")
print(f"Overall throughput: {len(records)/elapsed:.1f} cells/hour")

# Model-specific analysis
for model in sorted(set(r["model_id"] for r in records)):
    m_recs = [r for r in records if r["model_id"] == model]
    m_lats = [r.get("latency_ms", 0) for r in m_recs]
    m_retries = sum(1 for r in m_recs if r.get("status") == "FORMAT_RETRY_SUCCESS")
    m_failed = sum(1 for r in m_recs if r.get("status") == "FORMAT_FAILED")
    
    avg_lat = sum(m_lats) / len(m_lats) if m_lats else 0
    max_lat = max(m_lats) if m_lats else 0
    
    # Early vs recent comparison
    early = m_lats[:50] if len(m_lats) >= 50 else m_lats
    recent = m_lats[-50:] if len(m_lats) >= 50 else m_lats
    avg_early = sum(early) / len(early) if early else 0
    avg_recent = sum(recent) / len(recent) if recent else 0
    
    # Throughput
    m_ts = [datetime.fromisoformat(r["timestamp_iso"]) for r in m_recs]
    m_elapsed_h = (m_ts[-1] - m_ts[0]).total_seconds() / 3600 if len(m_ts) >= 2 else 0
    throughput = len(m_recs) / m_elapsed_h if m_elapsed_h > 0 else 0
    
    # Recent throughput (last 100 cells)
    if len(m_ts) >= 100:
        recent_elapsed = (m_ts[-1] - m_ts[-100]).total_seconds() / 3600
        recent_throughput = 100 / recent_elapsed if recent_elapsed > 0 else 0
    else:
        recent_throughput = throughput
    
    print(f"\n{'='*60}")
    print(f"{model}:")
    print(f"  Cells done: {len(m_recs)}")
    print(f"  Avg latency (overall): {avg_lat/1000:.1f}s per cell")
    print(f"  Avg latency (first 50): {avg_early/1000:.1f}s")
    print(f"  Avg latency (last 50):  {avg_recent/1000:.1f}s")
    ratio = avg_recent / avg_early if avg_early > 0 else 1
    print(f"  Slowdown ratio (recent/early): {ratio:.2f}x")
    print(f"  Max single-cell latency: {max_lat/1000:.1f}s")
    print(f"  Overall throughput: {throughput:.1f} cells/hour")
    print(f"  Recent throughput (last 100): {recent_throughput:.1f} cells/hour")
    print(f"  Retries: {m_retries}, Failed: {m_failed}")

# Show last 20 cells with timing
print(f"\n{'='*60}")
print("LAST 20 CELLS:")
for r in records[-20:]:
    lat = r.get("latency_ms", 0)
    retry = r.get("format_retry_count", 0)
    status = r.get("status", "")
    marker = " **RETRY**" if retry > 0 else ""
    marker += " **SLOW**" if lat > 30000 else ""
    print(f"  {r['model_id']:12s} | {r['scenario_id']:15s} | {r['treatment_id']:25s} | {lat/1000:6.1f}s | {status}{marker}")

# Check for gaps between consecutive timestamps (indicating stalls)
print(f"\n{'='*60}")
print("LONGEST GAPS BETWEEN CONSECUTIVE CELLS:")
gaps = []
for i in range(1, len(records)):
    t1 = datetime.fromisoformat(timestamps[i-1])
    t2 = datetime.fromisoformat(timestamps[i])
    gap = (t2 - t1).total_seconds()
    gaps.append((gap, i, records[i]["model_id"], records[i].get("status", "")))

gaps.sort(reverse=True)
for gap_s, idx, model, status in gaps[:10]:
    print(f"  {gap_s:.0f}s gap before cell #{idx} ({model}) [{status}]")
