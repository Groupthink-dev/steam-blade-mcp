"""Token-efficient output formatters.

Two modes:
- summary (default): compact pipe-delimited output, minimal tokens
- full: complete details for when the user needs everything
"""

from datetime import UTC, datetime

from .types import (
    Achievement,
    AppDetails,
    Friend,
    GlobalAchievement,
    InventoryItem,
    MarketPrice,
    NewsItem,
    OwnedGame,
    PlayerBans,
    PlayerSummary,
    RecentGame,
)

PERSONA_STATES = {
    0: "Offline",
    1: "Online",
    2: "Busy",
    3: "Away",
    4: "Snooze",
    5: "Looking to trade",
    6: "Looking to play",
}


def _hours(minutes: int) -> str:
    """Format minutes as hours with 1 decimal."""
    h = minutes / 60
    if h >= 10:
        return f"{h:.0f}h"
    return f"{h:.1f}h"


def _date(timestamp: int) -> str:
    """Format a Unix timestamp as YYYY-MM-DD."""
    if not timestamp:
        return ""
    return datetime.fromtimestamp(timestamp, tz=UTC).strftime("%Y-%m-%d")


def _price_str(cents: int | None, currency: str) -> str:
    """Format price in cents to human-readable."""
    if cents is None:
        return "N/A"
    return f"{currency} {cents / 100:.2f}"


# --- Profile ---


def format_profile(
    summary: PlayerSummary,
    level: int | None,
    bans: PlayerBans | None,
    detail: str = "summary",
) -> str:
    state = PERSONA_STATES.get(summary.persona_state, "Unknown")
    playing = f" | Playing: {summary.game_extra_info}" if summary.game_extra_info else ""
    level_str = f" | Level {level}" if level is not None else ""

    if detail == "summary":
        ban_str = ""
        if bans and (bans.vac_banned or bans.number_of_game_bans > 0):
            ban_str = f" | BANS: VAC={bans.number_of_vac_bans} Game={bans.number_of_game_bans}"
        country = f" | {summary.loc_country}" if summary.loc_country else ""
        return f"{summary.persona_name} | {state}{playing}{level_str}{country}{ban_str}"

    # Full detail
    lines = [
        f"Name: {summary.persona_name}",
        f"Steam ID: {summary.steam_id}",
        f"Status: {state}{playing}",
        f"Profile: {summary.profile_url}",
    ]
    if level is not None:
        lines.append(f"Level: {level}")
    if summary.loc_country:
        lines.append(f"Country: {summary.loc_country}")
    if summary.time_created:
        lines.append(f"Created: {_date(summary.time_created)}")
    if summary.last_logoff:
        lines.append(f"Last logoff: {_date(summary.last_logoff)}")
    if bans:
        lines.append(f"VAC bans: {bans.number_of_vac_bans}")
        lines.append(f"Game bans: {bans.number_of_game_bans}")
        lines.append(f"Community banned: {bans.community_banned}")
        lines.append(f"Economy ban: {bans.economy_ban}")
    return "\n".join(lines)


# --- Library ---


def format_library(
    games: list[OwnedGame], total: int, offset: int, detail: str = "summary"
) -> str:
    if not games:
        return "No games found."

    header = f"Games {offset + 1}-{offset + len(games)} of {total}"

    if detail == "summary":
        lines = [header]
        for g in games:
            played = _hours(g.playtime_forever) if g.playtime_forever else "unplayed"
            lines.append(f"{g.name} | {played}")
        return "\n".join(lines)

    lines = [header]
    for g in games:
        played = _hours(g.playtime_forever) if g.playtime_forever else "unplayed"
        recent = f" | 2wk: {_hours(g.playtime_2weeks)}" if g.playtime_2weeks else ""
        last = f" | last: {_date(g.rtime_last_played)}" if g.rtime_last_played else ""
        lines.append(f"{g.name} | {played}{recent}{last} | appid={g.app_id}")
    return "\n".join(lines)


# --- Recent Games ---


def format_recent(games: list[RecentGame], detail: str = "summary") -> str:
    if not games:
        return "No recently played games."

    if detail == "summary":
        lines = [f"Recently played ({len(games)} games):"]
        for g in games:
            lines.append(f"{g.name} | 2wk: {_hours(g.playtime_2weeks)}")
        return "\n".join(lines)

    lines = [f"Recently played ({len(games)} games):"]
    for g in games:
        total = _hours(g.playtime_forever)
        lines.append(
            f"{g.name} | 2wk: {_hours(g.playtime_2weeks)} | total: {total} | appid={g.app_id}"
        )
    return "\n".join(lines)


# --- Achievements ---


def format_achievements(
    achievements: list[Achievement], app_id: int, detail: str = "summary"
) -> str:
    if not achievements:
        return f"No achievements for app {app_id}."

    unlocked = [a for a in achievements if a.achieved]
    total = len(achievements)
    pct = (len(unlocked) / total * 100) if total else 0

    if detail == "summary":
        return f"Achievements: {len(unlocked)}/{total} ({pct:.0f}%)"

    lines = [f"Achievements: {len(unlocked)}/{total} ({pct:.0f}%)"]
    lines.append("")
    # Show unlocked first, then locked
    for a in sorted(achievements, key=lambda x: (-x.achieved, x.api_name)):
        status = "+" if a.achieved else "-"
        name = a.name or a.api_name
        date_str = f" | {_date(a.unlock_time)}" if a.unlock_time else ""
        desc = f" — {a.description}" if a.description else ""
        lines.append(f"  {status} {name}{desc}{date_str}")
    return "\n".join(lines)


# --- Global Stats ---


def format_global_stats(
    achievements: list[GlobalAchievement], detail: str = "summary"
) -> str:
    if not achievements:
        return "No global achievement data."

    sorted_achs = sorted(achievements, key=lambda a: a.percent, reverse=True)

    if detail == "summary":
        # Top 5 easiest + bottom 5 hardest
        lines = ["Global achievements:"]
        lines.append("Easiest:")
        for a in sorted_achs[:5]:
            lines.append(f"  {a.name} | {a.percent:.1f}%")
        lines.append("Hardest:")
        for a in sorted_achs[-5:]:
            lines.append(f"  {a.name} | {a.percent:.1f}%")
        return "\n".join(lines)

    lines = [f"Global achievements ({len(achievements)} total):"]
    for a in sorted_achs:
        lines.append(f"  {a.name} | {a.percent:.1f}%")
    return "\n".join(lines)


# --- Friends ---


def format_friends(
    friends: list[Friend],
    enriched: list[tuple[Friend, PlayerSummary | None]] | None = None,
    detail: str = "summary",
) -> str:
    count = len(friends)
    if not friends:
        return "No friends found (profile may be private)."

    if enriched:
        if detail == "summary":
            lines = [f"Friends ({count}):"]
            for friend, profile in enriched:
                name = profile.persona_name if profile else friend.steam_id
                since = _date(friend.friend_since)
                lines.append(f"{name} | since {since}")
            return "\n".join(lines)

        lines = [f"Friends ({count}):"]
        for friend, profile in enriched:
            name = profile.persona_name if profile else friend.steam_id
            state = PERSONA_STATES.get(profile.persona_state, "?") if profile else "?"
            since = _date(friend.friend_since)
            playing = f" | {profile.game_extra_info}" if profile and profile.game_extra_info else ""
            lines.append(f"{name} | {state}{playing} | since {since} | {friend.steam_id}")
        return "\n".join(lines)

    # No enrichment
    lines = [f"Friends ({count}):"]
    for f in friends:
        since = _date(f.friend_since)
        lines.append(f"{f.steam_id} | since {since}")
    return "\n".join(lines)


# --- Game Details ---


def format_game(app: AppDetails, detail: str = "summary") -> str:
    if detail == "summary":
        price = "Free" if app.is_free else _price_str(app.price_final, app.price_currency)
        discount = f" (-{app.discount_percent}%)" if app.discount_percent else ""
        meta = f" | MC: {app.metacritic_score}" if app.metacritic_score else ""
        recs = f" | {app.recommendations:,} reviews" if app.recommendations else ""
        platforms_str = "/".join(
            p for p, v in app.platforms.items() if v
        ) if app.platforms else ""
        return f"{app.name} | {price}{discount}{meta}{recs} | {platforms_str}"

    lines = [
        f"Name: {app.name}",
        f"Type: {app.type}",
        f"App ID: {app.steam_appid}",
    ]
    if app.is_free:
        lines.append("Price: Free")
    else:
        lines.append(f"Price: {_price_str(app.price_final, app.price_currency)}")
        if app.discount_percent:
            lines.append(
                f"Discount: {app.discount_percent}%"
                f" (was {_price_str(app.price_initial, app.price_currency)})"
            )
    if app.metacritic_score:
        lines.append(f"Metacritic: {app.metacritic_score}")
    if app.recommendations:
        lines.append(f"Reviews: {app.recommendations:,}")
    lines.append(f"Release: {app.release_date}")
    if app.developers:
        lines.append(f"Developer: {', '.join(app.developers)}")
    if app.publishers:
        lines.append(f"Publisher: {', '.join(app.publishers)}")
    if app.genres:
        lines.append(f"Genres: {', '.join(app.genres)}")
    if app.categories:
        lines.append(f"Categories: {', '.join(app.categories)}")
    if app.platforms:
        lines.append(f"Platforms: {', '.join(p for p, v in app.platforms.items() if v)}")
    if app.short_description:
        lines.append(f"\n{app.short_description}")
    return "\n".join(lines)


# --- News ---


def format_news(items: list[NewsItem], detail: str = "summary") -> str:
    if not items:
        return "No news items."

    if detail == "summary":
        lines = [f"News ({len(items)} items):"]
        for n in items:
            date = _date(n.date)
            lines.append(f"{date} | {n.title}")
        return "\n".join(lines)

    lines = [f"News ({len(items)} items):"]
    for n in items:
        date = _date(n.date)
        lines.append(f"\n--- {n.title} ---")
        lines.append(f"Date: {date} | By: {n.author} | Feed: {n.feed_label}")
        if n.contents:
            lines.append(n.contents)
        if n.url:
            lines.append(f"URL: {n.url}")
    return "\n".join(lines)


# --- Search ---


def format_search(results: list, detail: str = "summary") -> str:
    if not results:
        return "No matches found."

    lines = [f"Search results ({len(results)} matches):"]
    for app in results:
        lines.append(f"{app.name} | appid={app.app_id}")
    return "\n".join(lines)


# --- Inventory ---


def format_inventory(
    items: list[InventoryItem], app_id: int, detail: str = "summary"
) -> str:
    if not items:
        return f"No inventory items for app {app_id} (inventory may be private)."

    if detail == "summary":
        tradable = sum(1 for i in items if i.tradable)
        marketable = sum(1 for i in items if i.marketable)
        # Show count + 5 rarest (by type diversity)
        lines = [
            f"Inventory: {len(items)} items | {tradable} tradable | {marketable} marketable"
        ]
        # Group by type and show a sample
        seen_types: set[str] = set()
        sample = []
        for item in items:
            if item.type not in seen_types and len(sample) < 5:
                sample.append(item)
                seen_types.add(item.type)
        if sample:
            lines.append("Sample:")
            for item in sample:
                lines.append(f"  {item.name} | {item.type}")
        return "\n".join(lines)

    lines = [f"Inventory: {len(items)} items"]
    for item in items:
        trade = "T" if item.tradable else "-"
        market = "M" if item.marketable else "-"
        lines.append(f"  {item.name} | {item.type} | [{trade}{market}]")
    return "\n".join(lines)


# --- Market Price ---


def format_market_price(
    price: MarketPrice, market_hash_name: str, detail: str = "summary"
) -> str:
    if detail == "summary":
        return f"{market_hash_name} | {price.lowest_price} | vol: {price.volume}"

    return (
        f"Item: {market_hash_name}\n"
        f"Lowest: {price.lowest_price}\n"
        f"Median: {price.median_price}\n"
        f"Volume: {price.volume}"
    )


# --- Player Count ---


def format_player_count(count: int | None, app_id: int) -> str:
    if count is None:
        return f"Player count unavailable for app {app_id}."
    return f"Current players: {count:,}"
