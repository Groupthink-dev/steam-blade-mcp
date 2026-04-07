"""Tests for token-efficient output formatters."""

from steam_blade_mcp.formatters import (
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
from steam_blade_mcp.types import (
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


class TestProfileFormatter:
    def test_summary(self):
        summary = PlayerSummary(
            steamid="76561198012345678",
            personaname="TestPlayer",
            profileurl="https://example.com",
            personastate=1,
            communityvisibilitystate=3,
            loccountrycode="AU",
            gameextrainfo="CS2",
        )
        bans = PlayerBans(
            SteamId="76561198012345678",
            CommunityBanned=False,
            VACBanned=False,
            NumberOfVACBans=0,
            DaysSinceLastBan=0,
            NumberOfGameBans=0,
            EconomyBan="none",
        )
        result = format_profile(summary, 42, bans, "summary")
        assert "TestPlayer" in result
        assert "Online" in result
        assert "Level 42" in result
        assert "AU" in result
        assert "Playing: CS2" in result

    def test_summary_with_bans(self):
        summary = PlayerSummary(
            steamid="76561198012345678",
            personaname="Banned",
            profileurl="https://example.com",
            personastate=0,
        )
        bans = PlayerBans(
            SteamId="76561198012345678",
            VACBanned=True,
            NumberOfVACBans=2,
            NumberOfGameBans=1,
        )
        result = format_profile(summary, None, bans, "summary")
        assert "BANS:" in result
        assert "VAC=2" in result
        assert "Game=1" in result

    def test_full(self):
        summary = PlayerSummary(
            steamid="76561198012345678",
            personaname="TestPlayer",
            profileurl="https://example.com",
            personastate=1,
            timecreated=1300000000,
        )
        result = format_profile(summary, 42, None, "full")
        assert "Name: TestPlayer" in result
        assert "Steam ID: 76561198012345678" in result
        assert "Level: 42" in result


class TestLibraryFormatter:
    def test_summary(self):
        games = [
            OwnedGame(appid=730, name="CS2", playtime_forever=74040),
            OwnedGame(appid=440, name="TF2", playtime_forever=1200),
        ]
        result = format_library(games, 100, 0, "summary")
        assert "Games 1-2 of 100" in result
        assert "CS2 | 1234h" in result
        assert "TF2 | 20h" in result

    def test_empty(self):
        result = format_library([], 0, 0, "summary")
        assert "No games found" in result

    def test_full_includes_appid(self):
        games = [OwnedGame(appid=730, name="CS2", playtime_forever=100)]
        result = format_library(games, 1, 0, "full")
        assert "appid=730" in result

    def test_unplayed(self):
        games = [OwnedGame(appid=730, name="CS2", playtime_forever=0)]
        result = format_library(games, 1, 0, "summary")
        assert "unplayed" in result


class TestRecentFormatter:
    def test_summary(self):
        games = [RecentGame(appid=730, name="CS2", playtime_2weeks=120)]
        result = format_recent(games, "summary")
        assert "CS2 | 2wk: 2.0h" in result

    def test_empty(self):
        result = format_recent([], "summary")
        assert "No recently played" in result


class TestAchievementFormatter:
    def test_summary(self):
        achs = [
            Achievement(apiname="A", achieved=1, unlocktime=0),
            Achievement(apiname="B", achieved=1, unlocktime=0),
            Achievement(apiname="C", achieved=0, unlocktime=0),
        ]
        result = format_achievements(achs, 730, "summary")
        assert "2/3 (67%)" in result

    def test_empty(self):
        result = format_achievements([], 730, "summary")
        assert "No achievements" in result


class TestGlobalStatsFormatter:
    def test_summary_shows_top_and_bottom(self):
        achs = [
            GlobalAchievement(name="Easy", percent=95.0),
            GlobalAchievement(name="Hard", percent=1.2),
            GlobalAchievement(name="Medium", percent=50.0),
        ]
        result = format_global_stats(achs, "summary")
        assert "Easiest:" in result
        assert "Hardest:" in result
        assert "Easy" in result
        assert "Hard" in result


class TestFriendsFormatter:
    def test_summary_without_enrichment(self):
        friends = [Friend(steamid="76561198099999999", friend_since=1600000000)]
        result = format_friends(friends, detail="summary")
        assert "Friends (1):" in result
        assert "76561198099999999" in result

    def test_empty(self):
        result = format_friends([], detail="summary")
        assert "No friends" in result


class TestGameFormatter:
    def test_summary_free_game(self):
        app = AppDetails(
            name="CS2",
            is_free=True,
            metacritic_score=83,
            platforms={"windows": True, "mac": True, "linux": True},
            recommendations=1200000,
        )
        result = format_game(app, "summary")
        assert "CS2" in result
        assert "Free" in result
        assert "MC: 83" in result
        assert "1,200,000 reviews" in result

    def test_summary_paid_with_discount(self):
        app = AppDetails(
            name="Game",
            is_free=False,
            price_final=1999,
            price_initial=3999,
            price_currency="AUD",
            discount_percent=50,
            platforms={"windows": True},
        )
        result = format_game(app, "summary")
        assert "AUD 19.99" in result
        assert "-50%" in result


class TestNewsFormatter:
    def test_summary(self):
        items = [NewsItem(title="Update 1.0", date=1700000000)]
        result = format_news(items, "summary")
        assert "Update 1.0" in result

    def test_empty(self):
        result = format_news([], "summary")
        assert "No news" in result


class TestSearchFormatter:
    def test_results(self):
        results = [AppListEntry(appid=730, name="CS2")]
        result = format_search(results)
        assert "CS2 | appid=730" in result

    def test_empty(self):
        result = format_search([])
        assert "No matches" in result


class TestInventoryFormatter:
    def test_summary(self):
        items = [
            InventoryItem(
                name="AK-47 | Redline",
                type="Rifle",
                tradable=True,
                marketable=True,
            ),
            InventoryItem(
                name="M4A4 | Howl",
                type="Rifle",
                tradable=False,
                marketable=False,
            ),
        ]
        result = format_inventory(items, 730, "summary")
        assert "2 items" in result
        assert "1 tradable" in result
        assert "1 marketable" in result

    def test_empty(self):
        result = format_inventory([], 730, "summary")
        assert "No inventory" in result


class TestMarketPriceFormatter:
    def test_summary(self):
        price = MarketPrice(lowest_price="$12.50", median_price="$13.00", volume="42")
        result = format_market_price(price, "AK-47 | Redline", "summary")
        assert "AK-47 | Redline" in result
        assert "$12.50" in result
        assert "vol: 42" in result


class TestPlayerCountFormatter:
    def test_with_count(self):
        result = format_player_count(1234567, 730)
        assert "1,234,567" in result

    def test_none(self):
        result = format_player_count(None, 730)
        assert "unavailable" in result
