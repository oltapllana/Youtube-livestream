"""Quick test script — generates instances for all 12 YouTube channels and runs the algorithm."""

import httpx
import json

BASE = "http://localhost:8000"

print("=" * 60)
print("TV Scheduling — Instance Generation + Algorithm")
print("=" * 60)

# 1. Generate schedule (all 12 channels, 8 AM – 11 PM, no YT probing)
payload = {
    "opening_time": 480,       # 8:00 AM
    "closing_time": 1380,      # 11:00 PM
    "min_duration": 30,
    "channels_count": 12,
    "switch_penalty": 10,
    "termination_penalty": 20,
    "max_consecutive_genre": 2,
    "time_preferences": [
        {"start": 480, "end": 600, "preferred_genre": "science", "bonus": 20},
        {"start": 720, "end": 900, "preferred_genre": "technology", "bonus": 15},
    ],
}

print("\n[1] Sending scheduling request (probe=false, fast mode)...")
r = httpx.post(f"{BASE}/api/schedule/sync?probe=false", json=payload, timeout=300)
result = r.json()

print(f"    Status      : {result.get('status')}")
print(f"    Total progs : {result.get('total_programs')}")
print(f"    Channels    : {result.get('channels_used')}")
print(f"    Exec time   : {result.get('execution_time')}s")

print("\n[2] Scheduled programs with YouTube URLs:\n")
for p in result.get("scheduled_programs", []):
    sh, sm = divmod(p["start"], 60)
    eh, em = divmod(p["end"], 60)
    print(f"    {sh:02d}:{sm:02d} → {eh:02d}:{em:02d}  |  Ch {p['channel_id']:2d}  |  {p['program_id']}")
    print(f"      ↳ {p.get('url', 'N/A')}")

# 2. Save full result to a file
out_file = "schedule_result.json"
with open(out_file, "w") as f:
    json.dump(result, f, indent=2)
print(f"\n[3] Full result saved to {out_file}")

print("\n" + "=" * 60)
print("Done!")
