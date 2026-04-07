"""Pydantic models for Steam API responses and tool parameters."""

from pydantic import BaseModel, Field

# --- API Response Models ---


class PlayerSummary(BaseModel):
    steam_id: str = Field(alias="steamid")
    persona_name: str = Field(alias="personaname")
    profile_url: str = Field(alias="profileurl")
    avatar_full: str = Field(default="", alias="avatarfull")
    persona_state: int = Field(default=0, alias="personastate")
    visibility: int = Field(default=0, alias="communityvisibilitystate")
    last_logoff: int | None = Field(default=None, alias="lastlogoff")
    time_created: int | None = Field(default=None, alias="timecreated")
    loc_country: str | None = Field(default=None, alias="loccountrycode")
    game_id: str | None = Field(default=None, alias="gameid")
    game_extra_info: str | None = Field(default=None, alias="gameextrainfo")

    model_config = {"populate_by_name": True}


class OwnedGame(BaseModel):
    app_id: int = Field(alias="appid")
    name: str = ""
    playtime_forever: int = 0  # minutes
    playtime_2weeks: int = 0  # minutes
    img_icon_url: str = ""
    rtime_last_played: int = 0

    model_config = {"populate_by_name": True}


class RecentGame(BaseModel):
    app_id: int = Field(alias="appid")
    name: str = ""
    playtime_2weeks: int = 0  # minutes
    playtime_forever: int = 0  # minutes

    model_config = {"populate_by_name": True}


class Achievement(BaseModel):
    api_name: str = Field(alias="apiname")
    achieved: int = 0
    unlock_time: int = Field(default=0, alias="unlocktime")
    name: str | None = None
    description: str | None = None

    model_config = {"populate_by_name": True}


class GlobalAchievement(BaseModel):
    name: str
    percent: float


class Friend(BaseModel):
    steam_id: str = Field(alias="steamid")
    relationship: str = ""
    friend_since: int = 0

    model_config = {"populate_by_name": True}


class PlayerBans(BaseModel):
    steam_id: str = Field(alias="SteamId")
    community_banned: bool = Field(default=False, alias="CommunityBanned")
    vac_banned: bool = Field(default=False, alias="VACBanned")
    number_of_vac_bans: int = Field(default=0, alias="NumberOfVACBans")
    days_since_last_ban: int = Field(default=0, alias="DaysSinceLastBan")
    number_of_game_bans: int = Field(default=0, alias="NumberOfGameBans")
    economy_ban: str = Field(default="none", alias="EconomyBan")

    model_config = {"populate_by_name": True}


class NewsItem(BaseModel):
    gid: str = ""
    title: str = ""
    url: str = ""
    author: str = ""
    contents: str = ""
    feed_label: str = Field(default="", alias="feedlabel")
    date: int = 0
    feed_name: str = Field(default="", alias="feedname")

    model_config = {"populate_by_name": True}


class AppDetails(BaseModel):
    """Store API app details — subset of fields for token efficiency."""

    steam_appid: int = 0
    name: str = ""
    type: str = ""
    is_free: bool = False
    short_description: str = ""
    header_image: str = ""
    developers: list[str] = Field(default_factory=list)
    publishers: list[str] = Field(default_factory=list)
    metacritic_score: int | None = None
    metacritic_url: str | None = None
    categories: list[str] = Field(default_factory=list)
    genres: list[str] = Field(default_factory=list)
    release_date: str = ""
    coming_soon: bool = False
    platforms: dict[str, bool] = Field(default_factory=dict)
    price_initial: int | None = None  # cents
    price_final: int | None = None  # cents
    price_currency: str = ""
    discount_percent: int = 0
    recommendations: int | None = None


class AppListEntry(BaseModel):
    app_id: int = Field(alias="appid")
    name: str = ""

    model_config = {"populate_by_name": True}


class InventoryItem(BaseModel):
    asset_id: str = ""
    class_id: str = ""
    instance_id: str = ""
    name: str = ""
    market_hash_name: str = ""
    type: str = ""
    tradable: bool = False
    marketable: bool = False
    icon_url: str = ""
    tags: list[str] = Field(default_factory=list)


class MarketPrice(BaseModel):
    lowest_price: str = ""
    median_price: str = ""
    volume: str = ""
