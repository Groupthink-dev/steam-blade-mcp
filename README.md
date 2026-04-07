# Steam Blade MCP

A security-first, token-efficient MCP server for the Steam gaming platform. Built for the [Sidereal](https://sidereal.cc) plugin marketplace.

## Why Another Steam MCP?

There are 9+ Steam MCP servers on GitHub. None of them are suitable for production use in a plugin marketplace:

| Problem | Existing MCPs | Steam Blade |
|---------|--------------|-------------|
| **Security** | Mixed — most lack input validation, none block SSRF, some use undocumented APIs that risk account bans | Official APIs only. Steam ID regex, SSRF protection, rate limiting, credential scrubbing |
| **Token cost** | Raw JSON dumps — a library call can return 200KB+ of unfiltered data | Compact pipe-delimited output. `detail` parameter. Pagination. 5-50x fewer tokens |
| **Marketplace ready** | None have manifests, contracts, setup metadata, or conformance declarations | Full `sidereal-plugin.yaml` with `gaming-v1` contract, setup wizard metadata, credential config |
| **Caching** | 1 of 9 implements proper caching | TTL cache with async stampede prevention on every endpoint |
| **Rate limiting** | 1 of 9 implements per-host rate limiting | Per-host async limiters: Web API 1/s, Store API 0.67/s, Community 0.33/s |

### Competitive Landscape

| Server | Tools | Security | Tokens | Maintained |
|--------|-------|----------|--------|------------|
| sharkusmanch/steam-mcp-server | 30 | Good (SSRF) | Poor (raw JSON) | Active |
| XiaWan-Play/steam-tools-mcp | 25 | Good | Good (aggregated) | Active |
| shiyuki/steam-mcp-server | 4 | Good (rate limit) | Excellent | Active (narrow) |
| **steam-blade-mcp** | **12** | **Best** | **Best** | **Active** |

Steam Blade has fewer raw tools than sharkusmanch's 30, but each tool is aggregated and token-optimised. `steam_profile` alone replaces 3 separate tools by combining profile + level + bans into a single call with compact output.

## Security Posture

**API surface — official only:**
- Steam Web API (`api.steampowered.com`) — API key, read-only, stable
- Steam Store API (`store.steampowered.com`) — no auth, read-only, stable
- Steam Community (`steamcommunity.com`) — inventory and market reads only

**Explicitly excluded:**
- Revadike/InternalSteamWebAPI undocumented endpoints (ToS violation risk, credential escalation)
- Steam CM protocol (full credential exposure)
- Any write operations (no purchasing, trading, or messaging)
- Session cookie authentication (no browser session handling)

**Controls:**
- Steam ID validation: `^[0-9]{17}$` regex on all inputs
- SSRF protection: blocks RFC 1918, loopback, link-local, multicast, documentation ranges
- API key scrubbing: keys never appear in tool output or error messages
- Per-host rate limiting: async limiters prevent Steam API throttling
- Input validation: Pydantic models with constrained types on all parameters

## Installation

### Sidereal Marketplace

```
sidereal plugin add Groupthink-dev/steam-blade-mcp
```

The install wizard will prompt for your Steam API key and Steam ID.

### Manual (uv)

```bash
# Install
uv pip install steam-blade-mcp

# Configure
export STEAM_API_KEY="your-key-from-steamcommunity.com/dev/apikey"
export STEAM_ID="76561198012345678"

# Run
steam-blade-mcp
```

### Claude Desktop

Add to `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "steam": {
      "command": "uvx",
      "args": ["steam-blade-mcp"],
      "env": {
        "STEAM_API_KEY": "your-api-key",
        "STEAM_ID": "your-steam-id"
      }
    }
  }
}
```

### Claude Code

Add to `~/.claude.json`:

```json
{
  "mcpServers": {
    "steam": {
      "command": "uvx",
      "args": ["steam-blade-mcp"],
      "env": {
        "STEAM_API_KEY": "your-api-key",
        "STEAM_ID": "your-steam-id"
      }
    }
  }
}
```

## Getting Credentials

1. **Steam API Key** — Register at [steamcommunity.com/dev/apikey](https://steamcommunity.com/dev/apikey). Requires a Steam account with at least one purchase.

2. **Steam ID** — Your 17-digit SteamID64. Find it at [steamid.io](https://steamid.io) or from your Steam profile URL.

## Tools

| Tool | Description | Default Output |
|------|-------------|---------------|
| `steam_profile` | Player overview (name, status, level, bans) | One-line summary |
| `steam_library` | Owned games with playtime (paginated, sortable) | Name + hours, top 25 |
| `steam_recent` | Recently played (last 2 weeks) | Name + 2wk hours |
| `steam_search` | Fuzzy game search by name | Name + app ID |
| `steam_game` | Store details (price, rating, platforms) | One-line with price |
| `steam_achievements` | Per-game achievement progress | Count + percentage |
| `steam_friends` | Friends list (optional enrichment) | Steam IDs + since date |
| `steam_news` | Game news feed (truncated) | Date + title |
| `steam_stats` | Global achievement unlock rates | Top/bottom 5 |
| `steam_inventory` | Game item inventory | Count + sample |
| `steam_price` | Community Market item price | Price + volume |
| `steam_players` | Current concurrent player count | Single number |

Every tool supports `detail="summary"` (default, compact) and `detail="full"` (all fields).

## Token Efficiency

Summary mode output examples:

```
PlayerName | Online | Playing CS2 | Level 42 | AU
Games 1-25 of 347
Counter-Strike 2 | 1,234.5h
Elden Ring | 892.3h
Achievements: 47/50 (94%)
Current players: 1,234,567
```

Full mode adds structured multi-line output with all available fields when you need the detail.

See [SKILL.md](SKILL.md) for the complete token efficiency guide and workflow examples.

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `STEAM_API_KEY` | Yes | Steam Web API key |
| `STEAM_ID` | Yes | Default 17-digit Steam ID |
| `STEAM_MCP_TRANSPORT` | No | `stdio` (default) or `http` |
| `STEAM_MCP_HOST` | No | HTTP host (default `127.0.0.1`) |
| `STEAM_MCP_PORT` | No | HTTP port (default `8780`) |

## Development

```bash
# Setup
make install-dev

# Run locally
make dev

# Test
make test

# Lint
make lint
```

## Sidereal Contract: `gaming-v1`

This MCP implements the `gaming-v1` domain contract:

- **Required** (4/4): `player_summary`, `library`, `game_details`, `search_games`
- **Recommended** (4/4): `recent_games`, `achievements`, `friends`, `game_news`
- **Optional** (4/5): `global_stats`, `inventory`, `market_price`, `player_count`
- **Gated**: none (entire contract is read-only)

No gated (write) operations — Steam's API does not support safe write operations without credential escalation.

## License

MIT
