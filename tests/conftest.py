"""Shared test fixtures."""

import pytest


@pytest.fixture
def sample_player_data():
    return {
        "response": {
            "players": [
                {
                    "steamid": "76561198012345678",
                    "personaname": "TestPlayer",
                    "profileurl": "https://steamcommunity.com/id/testplayer/",
                    "avatarfull": "https://example.com/avatar.jpg",
                    "personastate": 1,
                    "communityvisibilitystate": 3,
                    "lastlogoff": 1700000000,
                    "timecreated": 1300000000,
                    "loccountrycode": "AU",
                    "gameid": "730",
                    "gameextrainfo": "Counter-Strike 2",
                }
            ]
        }
    }


@pytest.fixture
def sample_level_data():
    return {"response": {"player_level": 42}}


@pytest.fixture
def sample_bans_data():
    return {
        "players": [
            {
                "SteamId": "76561198012345678",
                "CommunityBanned": False,
                "VACBanned": False,
                "NumberOfVACBans": 0,
                "DaysSinceLastBan": 0,
                "NumberOfGameBans": 0,
                "EconomyBan": "none",
            }
        ]
    }


@pytest.fixture
def sample_owned_games():
    return {
        "response": {
            "game_count": 3,
            "games": [
                {
                    "appid": 730,
                    "name": "Counter-Strike 2",
                    "playtime_forever": 74040,
                    "playtime_2weeks": 120,
                    "rtime_last_played": 1700000000,
                },
                {
                    "appid": 1245620,
                    "name": "Elden Ring",
                    "playtime_forever": 53580,
                    "playtime_2weeks": 0,
                    "rtime_last_played": 1690000000,
                },
                {
                    "appid": 440,
                    "name": "Team Fortress 2",
                    "playtime_forever": 1200,
                    "playtime_2weeks": 0,
                    "rtime_last_played": 1600000000,
                },
            ],
        }
    }


@pytest.fixture
def sample_achievements():
    return {
        "playerstats": {
            "achievements": [
                {"apiname": "WIN_ROUND", "achieved": 1, "unlocktime": 1700000000},
                {"apiname": "HEADSHOT", "achieved": 1, "unlocktime": 1700001000},
                {"apiname": "FLAWLESS", "achieved": 0, "unlocktime": 0},
            ]
        }
    }


@pytest.fixture
def sample_friends():
    return {
        "friendslist": {
            "friends": [
                {
                    "steamid": "76561198099999999",
                    "relationship": "friend",
                    "friend_since": 1600000000,
                },
                {
                    "steamid": "76561198088888888",
                    "relationship": "friend",
                    "friend_since": 1650000000,
                },
            ]
        }
    }


@pytest.fixture
def sample_app_details():
    return {
        "730": {
            "success": True,
            "data": {
                "steam_appid": 730,
                "name": "Counter-Strike 2",
                "type": "game",
                "is_free": True,
                "short_description": "For over two decades...",
                "header_image": "https://example.com/header.jpg",
                "developers": ["Valve"],
                "publishers": ["Valve"],
                "metacritic": {"score": 83, "url": "https://metacritic.com/..."},
                "categories": [
                    {"description": "Multi-player"},
                    {"description": "Online Multi-Player"},
                ],
                "genres": [{"description": "Action"}, {"description": "Free to Play"}],
                "release_date": {"coming_soon": False, "date": "21 Aug, 2012"},
                "platforms": {"windows": True, "mac": True, "linux": True},
                "recommendations": {"total": 1200000},
            },
        }
    }


@pytest.fixture
def sample_news():
    return {
        "appnews": {
            "newsitems": [
                {
                    "gid": "123",
                    "title": "Release Notes for 4/1/2026",
                    "url": "https://example.com/news",
                    "author": "Valve",
                    "contents": "Bug fixes and improvements.",
                    "feedlabel": "Community Announcements",
                    "date": 1700000000,
                    "feedname": "steam_community_announcements",
                }
            ]
        }
    }


@pytest.fixture
def sample_app_list():
    return {
        "applist": {
            "apps": [
                {"appid": 730, "name": "Counter-Strike 2"},
                {"appid": 440, "name": "Team Fortress 2"},
                {"appid": 570, "name": "Dota 2"},
                {"appid": 1245620, "name": "ELDEN RING"},
                {"appid": 292030, "name": "The Witcher 3: Wild Hunt"},
            ]
        }
    }
