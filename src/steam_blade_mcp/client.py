"""Async Steam API client with rate limiting and caching."""

import logging
from difflib import SequenceMatcher

import httpx

from .cache import TTLCache
from .rate_limiter import RateLimiter
from .types import (
    Achievement,
    AppDetails,
    AppListEntry,
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
from .validation import validate_app_id, validate_count, validate_steam_id

log = logging.getLogger(__name__)

WEB_API = "https://api.steampowered.com"
STORE_API = "https://store.steampowered.com"
COMMUNITY = "https://steamcommunity.com"

# Cache TTLs (seconds)
TTL_PROFILE = 300  # 5 min
TTL_LIBRARY = 3600  # 1 hr
TTL_RECENT = 1800  # 30 min
TTL_ACHIEVEMENTS = 3600  # 1 hr
TTL_FRIENDS = 3600  # 1 hr
TTL_APP_DETAILS = 86400  # 24 hr (store data rarely changes)
TTL_APP_LIST = 21600  # 6 hr
TTL_NEWS = 1800  # 30 min
TTL_GLOBAL_STATS = 3600  # 1 hr
TTL_BANS = 3600  # 1 hr
TTL_INVENTORY = 1800  # 30 min
TTL_MARKET = 600  # 10 min
TTL_PLAYER_COUNT = 300  # 5 min


class SteamAPIError(Exception):
    """Raised when a Steam API call fails."""

    def __init__(self, message: str, status_code: int | None = None):
        self.status_code = status_code
        # Scrub API key from error messages
        clean = message.replace("key=", "key=***")
        super().__init__(clean)


class SteamClient:
    """Async Steam API client.

    Uses only official Steam Web API and Store API — no undocumented
    internal endpoints, no credential escalation.
    """

    def __init__(self, api_key: str, default_steam_id: str):
        self.api_key = api_key
        self.default_steam_id = validate_steam_id(default_steam_id)
        self.cache = TTLCache()
        self.rate_limiter = RateLimiter()
        self._http = httpx.AsyncClient(timeout=15.0, follow_redirects=True)
        self._app_list: list[AppListEntry] | None = None

    async def close(self) -> None:
        await self._http.aclose()

    async def _get(self, url: str, params: dict | None = None) -> dict:
        """Make a rate-limited GET request."""
        await self.rate_limiter.acquire(url)
        try:
            resp = await self._http.get(url, params=params)
        except httpx.HTTPError as e:
            raise SteamAPIError(f"HTTP error: {e}") from e

        if resp.status_code == 429:
            raise SteamAPIError("Rate limited by Steam API. Try again later.", 429)
        if resp.status_code == 403:
            raise SteamAPIError("API key invalid or access denied.", 403)
        if resp.status_code != 200:
            raise SteamAPIError(
                f"Steam API returned {resp.status_code}", resp.status_code
            )

        try:
            return resp.json()
        except Exception:
            raise SteamAPIError("Invalid JSON in Steam API response") from None

    def _resolve_steam_id(self, steam_id: str | None) -> str:
        sid = steam_id or self.default_steam_id
        return validate_steam_id(sid)

    # --- Player Profile ---

    async def get_player_summary(
        self, steam_id: str | None = None
    ) -> PlayerSummary | None:
        sid = self._resolve_steam_id(steam_id)
        cache_key = f"summary:{sid}"

        async def fetch():
            data = await self._get(
                f"{WEB_API}/ISteamUser/GetPlayerSummaries/v2/",
                {"key": self.api_key, "steamids": sid},
            )
            players = data.get("response", {}).get("players", [])
            if not players:
                return None
            return PlayerSummary.model_validate(players[0])

        return await self.cache.get_or_fetch(cache_key, fetch, TTL_PROFILE)

    async def get_player_level(self, steam_id: str | None = None) -> int | None:
        sid = self._resolve_steam_id(steam_id)
        cache_key = f"level:{sid}"

        async def fetch():
            data = await self._get(
                f"{WEB_API}/IPlayerService/GetSteamLevel/v1/",
                {"key": self.api_key, "steamid": sid},
            )
            return data.get("response", {}).get("player_level")

        return await self.cache.get_or_fetch(cache_key, fetch, TTL_PROFILE)

    async def get_player_bans(self, steam_id: str | None = None) -> PlayerBans | None:
        sid = self._resolve_steam_id(steam_id)
        cache_key = f"bans:{sid}"

        async def fetch():
            data = await self._get(
                f"{WEB_API}/ISteamUser/GetPlayerBans/v1/",
                {"key": self.api_key, "steamids": sid},
            )
            players = data.get("players", [])
            if not players:
                return None
            return PlayerBans.model_validate(players[0])

        return await self.cache.get_or_fetch(cache_key, fetch, TTL_BANS)

    # --- Game Library ---

    async def get_owned_games(
        self,
        steam_id: str | None = None,
        limit: int = 25,
        offset: int = 0,
        sort_by: str = "playtime",
    ) -> tuple[list[OwnedGame], int]:
        """Get owned games, sorted and paginated. Returns (games, total_count)."""
        sid = self._resolve_steam_id(steam_id)
        validate_count(limit, 250, "limit")
        cache_key = f"library:{sid}"

        async def fetch():
            data = await self._get(
                f"{WEB_API}/IPlayerService/GetOwnedGames/v1/",
                {
                    "key": self.api_key,
                    "steamid": sid,
                    "include_appinfo": 1,
                    "include_played_free_games": 1,
                },
            )
            resp = data.get("response", {})
            games = [OwnedGame.model_validate(g) for g in resp.get("games", [])]
            return games

        all_games = await self.cache.get_or_fetch(cache_key, fetch, TTL_LIBRARY)
        total = len(all_games)

        # Sort
        if sort_by == "playtime":
            all_games = sorted(all_games, key=lambda g: g.playtime_forever, reverse=True)
        elif sort_by == "recent":
            all_games = sorted(all_games, key=lambda g: g.rtime_last_played, reverse=True)
        elif sort_by == "name":
            all_games = sorted(all_games, key=lambda g: g.name.lower())

        return all_games[offset : offset + limit], total

    async def get_recent_games(
        self, steam_id: str | None = None, count: int = 10
    ) -> list[RecentGame]:
        sid = self._resolve_steam_id(steam_id)
        validate_count(count, 100, "count")
        cache_key = f"recent:{sid}:{count}"

        async def fetch():
            data = await self._get(
                f"{WEB_API}/IPlayerService/GetRecentlyPlayedGames/v1/",
                {"key": self.api_key, "steamid": sid, "count": count},
            )
            games = data.get("response", {}).get("games", [])
            return [RecentGame.model_validate(g) for g in games]

        return await self.cache.get_or_fetch(cache_key, fetch, TTL_RECENT)

    # --- Achievements ---

    async def get_achievements(
        self, app_id: int, steam_id: str | None = None
    ) -> list[Achievement]:
        validate_app_id(app_id)
        sid = self._resolve_steam_id(steam_id)
        cache_key = f"ach:{sid}:{app_id}"

        async def fetch():
            data = await self._get(
                f"{WEB_API}/ISteamUserStats/GetPlayerAchievements/v1/",
                {"key": self.api_key, "steamid": sid, "appid": app_id},
            )
            stats = data.get("playerstats", {})
            achievements = stats.get("achievements", [])
            return [Achievement.model_validate(a) for a in achievements]

        return await self.cache.get_or_fetch(cache_key, fetch, TTL_ACHIEVEMENTS)

    async def get_global_achievement_percentages(
        self, app_id: int
    ) -> list[GlobalAchievement]:
        validate_app_id(app_id)
        cache_key = f"global_ach:{app_id}"

        async def fetch():
            data = await self._get(
                f"{WEB_API}/ISteamUserStats/GetGlobalAchievementPercentagesForApp/v2/",
                {"gameid": app_id},
            )
            achievements = (
                data.get("achievementpercentages", {}).get("achievements", [])
            )
            return [GlobalAchievement(**a) for a in achievements]

        return await self.cache.get_or_fetch(cache_key, fetch, TTL_GLOBAL_STATS)

    # --- Friends ---

    async def get_friends(self, steam_id: str | None = None) -> list[Friend]:
        sid = self._resolve_steam_id(steam_id)
        cache_key = f"friends:{sid}"

        async def fetch():
            data = await self._get(
                f"{WEB_API}/ISteamUser/GetFriendList/v1/",
                {"key": self.api_key, "steamid": sid, "relationship": "friend"},
            )
            friends = data.get("friendslist", {}).get("friends", [])
            return [Friend.model_validate(f) for f in friends]

        return await self.cache.get_or_fetch(cache_key, fetch, TTL_FRIENDS)

    async def enrich_friends(
        self, friends: list[Friend]
    ) -> list[tuple[Friend, PlayerSummary | None]]:
        """Enrich friends with profile data. Batches in groups of 100."""
        result: list[tuple[Friend, PlayerSummary | None]] = []
        # Batch GetPlayerSummaries supports up to 100 IDs
        for i in range(0, len(friends), 100):
            batch = friends[i : i + 100]
            ids = ",".join(f.steam_id for f in batch)
            data = await self._get(
                f"{WEB_API}/ISteamUser/GetPlayerSummaries/v2/",
                {"key": self.api_key, "steamids": ids},
            )
            players = data.get("response", {}).get("players", [])
            summaries = {
                p["steamid"]: PlayerSummary.model_validate(p) for p in players
            }
            for friend in batch:
                result.append((friend, summaries.get(friend.steam_id)))
        return result

    # --- Game Info ---

    async def get_app_details(
        self, app_id: int, cc: str = "au"
    ) -> AppDetails | None:
        """Get store details for an app. Uses the Store API (no auth required)."""
        validate_app_id(app_id)
        cache_key = f"app:{app_id}:{cc}"

        async def fetch():
            data = await self._get(
                f"{STORE_API}/api/appdetails",
                {"appids": app_id, "cc": cc, "l": "english"},
            )
            app_data = data.get(str(app_id), {})
            if not app_data.get("success"):
                return None
            d = app_data.get("data", {})

            # Extract price info
            price = d.get("price_overview", {})
            metacritic = d.get("metacritic", {})
            release = d.get("release_date", {})
            platforms = d.get("platforms", {})

            return AppDetails(
                steam_appid=d.get("steam_appid", app_id),
                name=d.get("name", ""),
                type=d.get("type", ""),
                is_free=d.get("is_free", False),
                short_description=d.get("short_description", ""),
                header_image=d.get("header_image", ""),
                developers=d.get("developers", []),
                publishers=d.get("publishers", []),
                metacritic_score=metacritic.get("score"),
                metacritic_url=metacritic.get("url"),
                categories=[c.get("description", "") for c in d.get("categories", [])],
                genres=[g.get("description", "") for g in d.get("genres", [])],
                release_date=release.get("date", ""),
                coming_soon=release.get("coming_soon", False),
                platforms=platforms,
                price_initial=price.get("initial"),
                price_final=price.get("final"),
                price_currency=price.get("currency", ""),
                discount_percent=price.get("discount_percent", 0),
                recommendations=d.get("recommendations", {}).get("total"),
            )

        return await self.cache.get_or_fetch(cache_key, fetch, TTL_APP_DETAILS)

    async def get_news(
        self, app_id: int, count: int = 5, max_length: int = 300
    ) -> list[NewsItem]:
        validate_app_id(app_id)
        validate_count(count, 50, "count")
        cache_key = f"news:{app_id}:{count}:{max_length}"

        async def fetch():
            data = await self._get(
                f"{WEB_API}/ISteamNews/GetNewsForApp/v2/",
                {
                    "appid": app_id,
                    "count": count,
                    "maxlength": max_length,
                },
            )
            items = data.get("appnews", {}).get("newsitems", [])
            return [NewsItem.model_validate(n) for n in items]

        return await self.cache.get_or_fetch(cache_key, fetch, TTL_NEWS)

    async def get_player_count(self, app_id: int) -> int | None:
        validate_app_id(app_id)
        cache_key = f"players:{app_id}"

        async def fetch():
            data = await self._get(
                f"{WEB_API}/ISteamUserStats/GetNumberOfCurrentPlayers/v1/",
                {"appid": app_id},
            )
            return data.get("response", {}).get("player_count")

        return await self.cache.get_or_fetch(cache_key, fetch, TTL_PLAYER_COUNT)

    # --- Search ---

    async def _ensure_app_list(self) -> list[AppListEntry]:
        """Load and cache the full Steam app list for search."""
        if self._app_list is not None:
            cached = self.cache.get("app_list")
            if cached is not None:
                return cached

        async def fetch():
            data = await self._get(f"{WEB_API}/ISteamApps/GetAppList/v2/")
            apps = data.get("applist", {}).get("apps", [])
            entries = [AppListEntry.model_validate(a) for a in apps if a.get("name")]
            self._app_list = entries
            return entries

        return await self.cache.get_or_fetch("app_list", fetch, TTL_APP_LIST)

    async def search_apps(self, query: str, limit: int = 10) -> list[AppListEntry]:
        """Fuzzy search the Steam app list by name."""
        validate_count(limit, 50, "limit")
        app_list = await self._ensure_app_list()
        query_lower = query.lower()

        # Score and rank matches
        scored: list[tuple[float, AppListEntry]] = []
        for app in app_list:
            name_lower = app.name.lower()
            # Exact match
            if name_lower == query_lower:
                scored.append((1.0, app))
                continue
            # Starts with
            if name_lower.startswith(query_lower):
                scored.append((0.9, app))
                continue
            # Contains
            if query_lower in name_lower:
                scored.append((0.7, app))
                continue
            # Fuzzy (only for short queries to avoid perf issues)
            if len(query) >= 3:
                ratio = SequenceMatcher(None, query_lower, name_lower).ratio()
                if ratio > 0.5:
                    scored.append((ratio * 0.6, app))

        scored.sort(key=lambda x: x[0], reverse=True)
        return [app for _, app in scored[:limit]]

    # --- Inventory ---

    async def get_inventory(
        self, app_id: int, steam_id: str | None = None, count: int = 100
    ) -> list[InventoryItem]:
        """Get inventory items for a game. Uses Community API (no auth for public inventories)."""
        validate_app_id(app_id)
        sid = self._resolve_steam_id(steam_id)
        validate_count(count, 5000, "count")
        cache_key = f"inv:{sid}:{app_id}"

        async def fetch():
            data = await self._get(
                f"{COMMUNITY}/inventory/{sid}/{app_id}/2",
                {"l": "english", "count": count},
            )
            if not data:
                return []

            assets = data.get("assets", [])
            descriptions = {
                (d["classid"], d.get("instanceid", "0")): d
                for d in data.get("descriptions", [])
            }

            items = []
            for asset in assets:
                desc = descriptions.get(
                    (asset.get("classid", ""), asset.get("instanceid", "0")), {}
                )
                tags = [
                    t.get("localized_tag_name", "")
                    for t in desc.get("tags", [])
                    if t.get("localized_tag_name")
                ]
                items.append(
                    InventoryItem(
                        asset_id=asset.get("assetid", ""),
                        class_id=asset.get("classid", ""),
                        instance_id=asset.get("instanceid", "0"),
                        name=desc.get("name", ""),
                        market_hash_name=desc.get("market_hash_name", ""),
                        type=desc.get("type", ""),
                        tradable=bool(desc.get("tradable", 0)),
                        marketable=bool(desc.get("marketable", 0)),
                        icon_url=desc.get("icon_url", ""),
                        tags=tags,
                    )
                )
            return items

        return await self.cache.get_or_fetch(cache_key, fetch, TTL_INVENTORY)

    # --- Market ---

    async def get_market_price(
        self, app_id: int, market_hash_name: str, currency: int = 21
    ) -> MarketPrice | None:
        """Get current market price for an item. Currency 21 = AUD."""
        validate_app_id(app_id)
        cache_key = f"price:{app_id}:{market_hash_name}:{currency}"

        async def fetch():
            data = await self._get(
                f"{COMMUNITY}/market/priceoverview/",
                {
                    "appid": app_id,
                    "market_hash_name": market_hash_name,
                    "currency": currency,
                },
            )
            if not data.get("success"):
                return None
            return MarketPrice(
                lowest_price=data.get("lowest_price", ""),
                median_price=data.get("median_price", ""),
                volume=data.get("volume", ""),
            )

        return await self.cache.get_or_fetch(cache_key, fetch, TTL_MARKET)
