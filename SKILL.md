---
name: steam-blade
description: Steam gaming platform — library, achievements, friends, store, market
version: 0.1.0
permissions:
  read:
    - steam_profile
    - steam_library
    - steam_recent
    - steam_search
    - steam_game
    - steam_achievements
    - steam_friends
    - steam_news
    - steam_stats
    - steam_inventory
    - steam_price
    - steam_players
  write: []
---

# Steam Blade MCP — Skill Guide

## Token Efficiency Rules (MANDATORY)

1. **Use `steam_search` before game-specific tools** — find the app ID first, don't guess
2. **Default to `detail="summary"`** — one-line output uses 5-10x fewer tokens than full
3. **Use `steam_profile` for overview** — aggregates profile + level + bans in one call
4. **Use `steam_recent` over `steam_library`** — recent is capped; library can be huge
5. **Paginate `steam_library`** — default limit=25; never fetch all games at once
6. **Set `enrich=false` on `steam_friends`** — profile enrichment costs N extra API calls
7. **Use `steam_players` for quick checks** — cheapest possible API call (single number)

## Quick Start — 5 Most Common Operations

```
steam_profile                              → Player overview (one-line)
steam_library limit=10                     → Top 10 games by playtime
steam_recent                               → Last 2 weeks of gaming
steam_search query="Counter-Strike"        → Find app IDs
steam_game app_id=730                      → Game store info + price
```

## Tool Reference

### Profile
- **steam_profile** — Aggregated player overview: name, status, level, bans, country. Combines 3 API calls into one tool.

### Library
- **steam_library** — Owned games with playtime. Paginated (`limit`/`offset`), sortable (`playtime`/`recent`/`name`). Default: top 25 by playtime.
- **steam_recent** — Recently played games (last 2 weeks). Capped at `count` (default 10).

### Discovery
- **steam_search** — Fuzzy search all Steam apps by name. Returns app IDs. Use this before calling game-specific tools.
- **steam_game** — Full store details: price, rating, platforms, genres, description. Supports regional pricing via `cc` param.
- **steam_news** — News feed per game. Content truncated to `max_length` (default 300).
- **steam_players** — Current concurrent player count. Single number, cheapest call.

### Progress
- **steam_achievements** — Per-game achievement progress. Summary = count + percentage. Full = every achievement with status.
- **steam_stats** — Global achievement unlock percentages. Summary = top/bottom 5. Full = all achievements.

### Social
- **steam_friends** — Friends list. Set `enrich=true` for names and online status (costs API calls). Default: Steam IDs only.

### Economy
- **steam_inventory** — Game item inventory (CS2=730, TF2=440, Dota2=570). Requires public inventory. Summary = count + sample.
- **steam_price** — Community Market price for a specific item by `market_hash_name`.

## Workflow Examples

### Game Research
```
1. steam_search query="Elden Ring"            → Find app ID
2. steam_game app_id=1245620                  → Price, rating, platforms
3. steam_players app_id=1245620               → Current player count
4. steam_news app_id=1245620 count=3          → Recent news
```

### Library Analysis
```
1. steam_profile                              → Account overview
2. steam_library limit=10 sort="playtime"     → Most played games
3. steam_library limit=10 sort="recent"       → Recently played
4. steam_library limit=10 offset=10           → Page 2 of top games
```

### Achievement Hunting
```
1. steam_achievements app_id=730              → Your progress (summary)
2. steam_achievements app_id=730 detail="full" → Every achievement
3. steam_stats app_id=730                     → Global unlock rates
```

### Friend Activity
```
1. steam_friends                              → ID list (fast)
2. steam_friends enrich=true                  → Names + status (slower)
3. steam_friends enrich=true detail="full"    → Full detail (heaviest)
```

### Market Check
```
1. steam_inventory app_id=730                 → CS2 inventory overview
2. steam_price app_id=730 market_hash_name="AK-47 | Redline (Field-Tested)"
   → Current market price
```

## Common Parameters

| Parameter | Description | Example |
|-----------|-------------|---------|
| `steam_id` | 17-digit Steam ID (omit for default) | `"76561198012345678"` |
| `app_id` | Steam application ID | `730` (CS2), `440` (TF2) |
| `detail` | Output verbosity | `"summary"` (default) or `"full"` |
| `limit` | Pagination page size | `25` (default, max 250) |
| `offset` | Pagination offset | `0` (default) |
| `sort` | Library sort order | `"playtime"`, `"recent"`, `"name"` |
| `enrich` | Fetch extra profile data | `false` (default) |
| `cc` | Country code for pricing | `"au"` (default), `"us"`, `"gb"` |
| `count` | Number of items to return | `10` (default) |
| `max_length` | Max content length (news) | `300` (default) |

## Output Format

Summary mode uses compact pipe-delimited format:

```
PlayerName | Online | Playing CS2 | Level 42 | AU
Counter-Strike 2 | AUD 0.00 | MC: 83 | 1,200,000 reviews | windows/mac/linux
Elden Ring | 1,234.5h
```

Full mode uses labelled multi-line format for detailed inspection.

## Security Notes

- Read-only: no write operations exist (no purchasing, trading, or messaging)
- API key never appears in tool output (scrubbed from errors)
- Steam IDs validated: exactly 17 digits
- SSRF protection on IP-based parameters
- Rate limited: Web API 1/s, Store API 0.67/s, Community 0.33/s
- All responses cached with TTL (5min–24hr depending on data volatility)
