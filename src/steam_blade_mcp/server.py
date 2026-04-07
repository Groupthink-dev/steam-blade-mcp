"""Steam Blade MCP server — FastMCP tool registration."""

import logging
import os
import sys
from contextlib import asynccontextmanager
from typing import Literal

from fastmcp import FastMCP

from .client import SteamClient
from .formatters import (
    format_achievements,
    format_friends,
    format_game,
    format_global_stats,
    format_inventory,
    format_library,
    format_market_price,
    format_news,
    format_player_count,
    format_profile,
    format_recent,
    format_search,
)

log = logging.getLogger(__name__)

TRANSPORT = os.environ.get("STEAM_MCP_TRANSPORT", "stdio")
HTTP_HOST = os.environ.get("STEAM_MCP_HOST", "127.0.0.1")
HTTP_PORT = int(os.environ.get("STEAM_MCP_PORT", "8780"))

# Shared client instance
_client: SteamClient | None = None


def _get_client() -> SteamClient:
    global _client
    if _client is None:
        api_key = os.environ.get("STEAM_API_KEY", "")
        steam_id = os.environ.get("STEAM_ID", "")
        if not api_key:
            print("ERROR: STEAM_API_KEY environment variable is required.", file=sys.stderr)
            sys.exit(1)
        if not steam_id:
            print("ERROR: STEAM_ID environment variable is required.", file=sys.stderr)
            sys.exit(1)
        _client = SteamClient(api_key=api_key, default_steam_id=steam_id)
    return _client


@asynccontextmanager
async def lifespan(server):
    yield
    if _client is not None:
        await _client.close()


mcp = FastMCP(
    "SteamBlade",
    instructions=(
        "Steam gaming platform operations. Library stats, achievements, friends, "
        "store data, market prices. Use summary detail level (default) for token "
        "efficiency. Use steam_search to find app IDs before calling game-specific tools."
    ),
    lifespan=lifespan,
)


# --- Profile (aggregated overview) ---


@mcp.tool()
async def steam_profile(
    steam_id: str | None = None,
    detail: Literal["summary", "full"] = "summary",
) -> str:
    """Player profile with level, status, and ban info.

    Args:
        steam_id: 17-digit Steam ID. Omit to use default.
        detail: "summary" (one-line) or "full" (all fields).
    """
    client = _get_client()
    summary = await client.get_player_summary(steam_id)
    if summary is None:
        return "Player not found or profile is private."
    level = await client.get_player_level(steam_id)
    bans = await client.get_player_bans(steam_id)
    return format_profile(summary, level, bans, detail)


# --- Library ---


@mcp.tool()
async def steam_library(
    steam_id: str | None = None,
    limit: int = 25,
    offset: int = 0,
    sort: Literal["playtime", "recent", "name"] = "playtime",
    detail: Literal["summary", "full"] = "summary",
) -> str:
    """Owned games with playtime. Paginated, sorted.

    Args:
        steam_id: 17-digit Steam ID. Omit to use default.
        limit: Games per page (1-250, default 25).
        offset: Skip first N games (for pagination).
        sort: Sort by "playtime" (desc), "recent" (last played), or "name" (alpha).
        detail: "summary" (name + hours) or "full" (+ appid, 2wk, last played).
    """
    client = _get_client()
    games, total = await client.get_owned_games(steam_id, limit, offset, sort)
    return format_library(games, total, offset, detail)


# --- Recent ---


@mcp.tool()
async def steam_recent(
    steam_id: str | None = None,
    count: int = 10,
    detail: Literal["summary", "full"] = "summary",
) -> str:
    """Recently played games (last 2 weeks).

    Args:
        steam_id: 17-digit Steam ID. Omit to use default.
        count: Number of games (1-100, default 10).
        detail: "summary" (name + 2wk hours) or "full" (+ total hours, appid).
    """
    client = _get_client()
    games = await client.get_recent_games(steam_id, count)
    return format_recent(games, detail)


# --- Search ---


@mcp.tool()
async def steam_search(
    query: str,
    limit: int = 10,
) -> str:
    """Search Steam games by name. Returns app IDs for use with other tools.

    Args:
        query: Game name to search for (fuzzy matching).
        limit: Max results (1-50, default 10).
    """
    client = _get_client()
    results = await client.search_apps(query, limit)
    return format_search(results)


# --- Game Details ---


@mcp.tool()
async def steam_game(
    app_id: int,
    cc: str = "au",
    detail: Literal["summary", "full"] = "summary",
) -> str:
    """Store details for a game: price, rating, platforms, description.

    Args:
        app_id: Steam application ID. Use steam_search to find this.
        cc: Country code for regional pricing (default "au" for AUD).
        detail: "summary" (one-line) or "full" (all store info).
    """
    client = _get_client()
    app = await client.get_app_details(app_id, cc)
    if app is None:
        return f"App {app_id} not found or not available in region '{cc}'."
    return format_game(app, detail)


# --- Achievements ---


@mcp.tool()
async def steam_achievements(
    app_id: int,
    steam_id: str | None = None,
    detail: Literal["summary", "full"] = "summary",
) -> str:
    """Achievement progress for a game.

    Args:
        app_id: Steam application ID.
        steam_id: 17-digit Steam ID. Omit to use default.
        detail: "summary" (count + percentage) or "full" (every achievement).
    """
    client = _get_client()
    achievements = await client.get_achievements(app_id, steam_id)
    return format_achievements(achievements, app_id, detail)


# --- Friends ---


@mcp.tool()
async def steam_friends(
    steam_id: str | None = None,
    enrich: bool = False,
    detail: Literal["summary", "full"] = "summary",
) -> str:
    """Friends list with optional profile enrichment.

    Args:
        steam_id: 17-digit Steam ID. Omit to use default.
        enrich: Fetch profile data for each friend (costs extra API calls).
        detail: "summary" (name + since) or "full" (+ status, game, steamid).
    """
    client = _get_client()
    friends = await client.get_friends(steam_id)
    if enrich:
        enriched = await client.enrich_friends(friends)
        return format_friends(friends, enriched, detail)
    return format_friends(friends, detail=detail)


# --- News ---


@mcp.tool()
async def steam_news(
    app_id: int,
    count: int = 5,
    max_length: int = 300,
    detail: Literal["summary", "full"] = "summary",
) -> str:
    """News feed for a game.

    Args:
        app_id: Steam application ID.
        count: Number of articles (1-50, default 5).
        max_length: Max content length per article (default 300 chars).
        detail: "summary" (date + title) or "full" (+ content, author, URL).
    """
    client = _get_client()
    items = await client.get_news(app_id, count, max_length)
    return format_news(items, detail)


# --- Global Stats ---


@mcp.tool()
async def steam_stats(
    app_id: int,
    detail: Literal["summary", "full"] = "summary",
) -> str:
    """Global achievement unlock percentages for a game.

    Args:
        app_id: Steam application ID.
        detail: "summary" (top 5 easiest + hardest) or "full" (all achievements).
    """
    client = _get_client()
    achievements = await client.get_global_achievement_percentages(app_id)
    return format_global_stats(achievements, detail)


# --- Inventory ---


@mcp.tool()
async def steam_inventory(
    app_id: int,
    steam_id: str | None = None,
    detail: Literal["summary", "full"] = "summary",
) -> str:
    """Game inventory (CS2, TF2, Dota 2, etc.). Requires public inventory.

    Args:
        app_id: Steam application ID (e.g., 730 for CS2, 440 for TF2).
        steam_id: 17-digit Steam ID. Omit to use default.
        detail: "summary" (count + sample) or "full" (every item).
    """
    client = _get_client()
    items = await client.get_inventory(app_id, steam_id)
    return format_inventory(items, app_id, detail)


# --- Market Price ---


@mcp.tool()
async def steam_price(
    app_id: int,
    market_hash_name: str,
    currency: int = 21,
    detail: Literal["summary", "full"] = "summary",
) -> str:
    """Current Community Market price for an item.

    Args:
        app_id: Steam application ID (e.g., 730 for CS2).
        market_hash_name: Exact market name of the item.
        currency: Steam currency code (default 21 = AUD). 1=USD, 2=GBP, 3=EUR.
        detail: "summary" (one-line) or "full" (lowest, median, volume).
    """
    client = _get_client()
    price = await client.get_market_price(app_id, market_hash_name, currency)
    if price is None:
        return f"Price not found for '{market_hash_name}' in app {app_id}."
    return format_market_price(price, market_hash_name, detail)


# --- Player Count ---


@mcp.tool()
async def steam_players(
    app_id: int,
) -> str:
    """Current concurrent player count for a game.

    Args:
        app_id: Steam application ID.
    """
    client = _get_client()
    count = await client.get_player_count(app_id)
    return format_player_count(count, app_id)


def main():
    if TRANSPORT == "http":
        mcp.run(transport="streamable-http", host=HTTP_HOST, port=HTTP_PORT)
    else:
        mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
