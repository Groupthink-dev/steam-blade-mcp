"""Tests for Steam API client."""

from unittest.mock import AsyncMock, patch

import pytest

from steam_blade_mcp.client import SteamClient


@pytest.fixture
def client():
    return SteamClient(api_key="test_key_12345", default_steam_id="76561198012345678")


class TestClientInit:
    def test_valid_init(self, client):
        assert client.default_steam_id == "76561198012345678"
        assert client.api_key == "test_key_12345"

    def test_invalid_steam_id(self):
        with pytest.raises(ValueError, match="exactly 17 digits"):
            SteamClient(api_key="key", default_steam_id="invalid")


class TestResolveId:
    def test_uses_default(self, client):
        assert client._resolve_steam_id(None) == "76561198012345678"

    def test_uses_provided(self, client):
        assert client._resolve_steam_id("76561198099999999") == "76561198099999999"

    def test_validates_provided(self, client):
        with pytest.raises(ValueError):
            client._resolve_steam_id("invalid")


class TestGetPlayerSummary:
    @pytest.mark.asyncio
    async def test_returns_summary(self, client, sample_player_data):
        with patch.object(client, "_get", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = sample_player_data
            result = await client.get_player_summary()
            assert result is not None
            assert result.persona_name == "TestPlayer"
            assert result.steam_id == "76561198012345678"
            assert result.game_extra_info == "Counter-Strike 2"

    @pytest.mark.asyncio
    async def test_returns_none_for_empty(self, client):
        with patch.object(client, "_get", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = {"response": {"players": []}}
            result = await client.get_player_summary()
            assert result is None

    @pytest.mark.asyncio
    async def test_caches_result(self, client, sample_player_data):
        with patch.object(client, "_get", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = sample_player_data
            await client.get_player_summary()
            await client.get_player_summary()
            assert mock_get.call_count == 1  # cached


class TestGetOwnedGames:
    @pytest.mark.asyncio
    async def test_returns_games_sorted(self, client, sample_owned_games):
        with patch.object(client, "_get", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = sample_owned_games
            games, total = await client.get_owned_games()
            assert total == 3
            assert len(games) == 3
            # Should be sorted by playtime desc
            assert games[0].name == "Counter-Strike 2"
            assert games[1].name == "Elden Ring"

    @pytest.mark.asyncio
    async def test_pagination(self, client, sample_owned_games):
        with patch.object(client, "_get", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = sample_owned_games
            games, total = await client.get_owned_games(limit=2, offset=0)
            assert len(games) == 2
            assert total == 3

    @pytest.mark.asyncio
    async def test_sort_by_name(self, client, sample_owned_games):
        with patch.object(client, "_get", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = sample_owned_games
            games, _ = await client.get_owned_games(sort_by="name")
            assert games[0].name == "Counter-Strike 2"


class TestGetAchievements:
    @pytest.mark.asyncio
    async def test_returns_achievements(self, client, sample_achievements):
        with patch.object(client, "_get", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = sample_achievements
            result = await client.get_achievements(730)
            assert len(result) == 3
            assert result[0].api_name == "WIN_ROUND"
            assert result[0].achieved == 1

    @pytest.mark.asyncio
    async def test_validates_app_id(self, client):
        with pytest.raises(ValueError, match="Invalid app ID"):
            await client.get_achievements(0)


class TestGetFriends:
    @pytest.mark.asyncio
    async def test_returns_friends(self, client, sample_friends):
        with patch.object(client, "_get", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = sample_friends
            result = await client.get_friends()
            assert len(result) == 2
            assert result[0].steam_id == "76561198099999999"


class TestGetAppDetails:
    @pytest.mark.asyncio
    async def test_returns_details(self, client, sample_app_details):
        with patch.object(client, "_get", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = sample_app_details
            result = await client.get_app_details(730)
            assert result is not None
            assert result.name == "Counter-Strike 2"
            assert result.is_free is True
            assert result.metacritic_score == 83

    @pytest.mark.asyncio
    async def test_returns_none_on_failure(self, client):
        with patch.object(client, "_get", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = {"730": {"success": False}}
            result = await client.get_app_details(730)
            assert result is None


class TestGetNews:
    @pytest.mark.asyncio
    async def test_returns_news(self, client, sample_news):
        with patch.object(client, "_get", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = sample_news
            result = await client.get_news(730)
            assert len(result) == 1
            assert result[0].title == "Release Notes for 4/1/2026"


class TestSearchApps:
    @pytest.mark.asyncio
    async def test_exact_match(self, client, sample_app_list):
        with patch.object(client, "_get", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = sample_app_list
            results = await client.search_apps("Counter-Strike 2")
            assert len(results) > 0
            assert results[0].name == "Counter-Strike 2"

    @pytest.mark.asyncio
    async def test_partial_match(self, client, sample_app_list):
        with patch.object(client, "_get", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = sample_app_list
            results = await client.search_apps("Dota")
            assert any(r.name == "Dota 2" for r in results)

    @pytest.mark.asyncio
    async def test_respects_limit(self, client, sample_app_list):
        with patch.object(client, "_get", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = sample_app_list
            results = await client.search_apps("2", limit=2)
            assert len(results) <= 2


class TestGetPlayerCount:
    @pytest.mark.asyncio
    async def test_returns_count(self, client):
        with patch.object(client, "_get", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = {"response": {"player_count": 1234567}}
            result = await client.get_player_count(730)
            assert result == 1234567
