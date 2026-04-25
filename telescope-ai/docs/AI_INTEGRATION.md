# AI Integration Guide

## How AI Can Interact With Your Telescope

The MCP server exposes the telescope as a set of AI-callable tools. This document explains the integration patterns.

## Pattern 1: Voice/Text Assistant

"Hey, what should I look at tonight?"

```
User → AI → get_observing_plan(max=3) → "1. M42 at 65° altitude
       for 45 min. 2. Omega Centauri at 55° for 30 min. 3. Jupiter at 40°"
```

"Point at the Orion Nebula."

```
User → AI → goto_target(target_name=M42) → "Slewing to Orion Nebula"
```

## Pattern 2: Autonomous Observation

The AI can run a full session:
1. Check weather → if clear, proceed
2. Generate plan → pick best target
3. Goto target → plate solve → confirm position
4. Take exposures → monitor progress
5. When done → move to next target
6. Park at dawn

This is implemented in the `NightScheduler` and `MountController` — the MCP server gives AI agents the tools to orchestrate this.

## Pattern 3: Satellite Tracking

When the user says "Track the ISS", the AI:

1. Calls `list_satellites(query="ISS")` to find it
2. Calls `track_satellite("ISS (ZARYA)", 300)` to start tracking
3. Reports position, speed, direction back to user

## Pattern 4: "What am I looking at?"

User takes a photo through the eyepiece, sends it to the AI:

1. AI receives image
2. AI calls `plate_solve(image_path)` to get RA/Dec
3. AI calls `classify_object(ra, dec)` to identify
4. AI responds: "You're looking at the Orion Nebula (M42), 1,344 light years away"

## Pattern 5: AI Night Scheduler

The built-in scheduler already scores targets intelligently. An LLM can add:

- Historical preferences: "This user likes planetary nebulae"
- Current events: "Comet 2026A is visible this week"
- Educational context: "Show the user something from each catalog"

## Custom AI Models

### Object Classification
You can train a custom CNN and load it:

```python
from telescope_ai import ObjectClassifier
classifier = ObjectClassifier(config)
classifier.load_model("/path/to/model.pt")
```

To train: use the Galaxy Zoo dataset (galaxy10) or SDSS image data.

### Night Planning
Extend the scheduler with reinforcement learning:
- Score targets based on past user ratings
- Learn preferred object types vs. time of night
- Optimize for science value, education, or aesthetic value

## MCP Client Integration

### Claude Code

```bash
fastmcp install claude-code mcp_server/server.py
```

Then in Claude Code:
```
/weather
> Cloudy 80%, not observable

/plan 5
> 1. M42 - Orion Nebula at 65°
> 2. Omega Centauri at 55°
```

### Claude Desktop

```bash
fastmcp install claude-desktop mcp_server/server.py
```

### Custom Python Client

```python
import subprocess, json

def call_mcp(tool: str, **kwargs):
    args = ["fastmcp", "call", "mcp_server/server.py:mcp", tool]
    for k, v in kwargs.items():
        args.extend([k.replace("_", "-"), str(v)])
    result = subprocess.run(args, capture_output=True, text=True)
    return json.loads(result.stdout)

# Example
status = call_mcp("health_check")
plan = call_mcp("get_observing_plan", max_targets=3)
```

### HTTP Client

When running with `--transport http`:

```python
import requests

resp = requests.post(
    "http://127.0.0.1:8080/mcp",
    json={
        "jsonrpc": "2.0",
        "method": "tools/call",
        "params": {"name": "health_check", "arguments": {}},
        "id": 1,
    },
)
```

## Example AI Conversation

```
User: What can I do tonight?

AI: [check_weather → clear, 15% clouds, moon at 30%]

Let me check conditions... It's clear and dark. Here's my plan:

1. 🥇 Omega Centauri (NGC 5139) — 62° altitude, globular cluster
   → Bright, southern hemisphere's best cluster
   → 30 min observation

2. 🥇 47 Tucanae (NGC 104) — 55° altitude, globular cluster  
   → Second brightest globular in the sky
   → 25 min observation

3. 🥇 Carina Nebula (NGC 3372) — 48° altitude, emission nebula
   → Massive star-forming region
   → 45 min with H-alpha filter

Shall I start with #1?

User: Yes, point at Omega Centauri.

AI: [goto_target(target_name="NGC 5139")]
Slewing to Omega Centauri...
[plate_solve → confirm pointing]
Ready! Omega Centauri centered. Take a look — 
you're seeing 10 million stars, 15,800 light years away.
Want me to start a 30-minute imaging run?
```
