"""Constant values"""

import random
import urllib.parse

COMPETITION_ID = "1ha7bnfgb89131ey8cpx5vvvpl"
DEFAULT_SEASON_ID = "110qulr80h8ail8rgwi0o7x0"
DEFAULT_RT = "c"
DEFAULT_FMT = "json"

# Base URLs for the endpoints
API_BASE = "https://api.performfeeds.com/soccerdata"
MATCH_BASE_URL = f"{API_BASE}/match/{COMPETITION_ID}"
STANDINGS_BASE_URL = f"{API_BASE}/standings/{COMPETITION_ID}"
TEAM_INFO_BASE_URL = f"{API_BASE}/team/{COMPETITION_ID}"
ROSTER_BASE_URL = f"{API_BASE}/squads/{COMPETITION_ID}"
PLAYER_CAREER_BASE_URL = f"{API_BASE}/playercareer/{COMPETITION_ID}"


CPL_BASE_API_URL = "https://login.canpl.ca/api"
PLAYERS_ENDPOINT = f"{CPL_BASE_API_URL}/players"


# — new CPL-specific constants —
CPL_DEFAULT_SEASON_ID = "cpl::Football_Season::fd43e1d61dfe4396a7356bc432de0007"
CPL_STATS_BASE_URL = "https://api-sdp.canpl.ca/v1/cpl/football"

# stats endpoints (templated by season_id)
CPL_TEAM_STATS_ENDPOINT = f"{CPL_STATS_BASE_URL}/seasons/{{season_id}}/stats/teams"
CPL_PLAYER_STATS_ENDPOINT = f"{CPL_STATS_BASE_URL}/seasons/{{season_id}}/stats/players"

# Query parameters for the match schedule endpoint
MATCH_PARAMS = {
    "tmcl": DEFAULT_SEASON_ID,
    "_rt": DEFAULT_RT,
    "_pgSz": "200",
    "_ordSrt": "asc",
    "live": "yes",
    "_fmt": DEFAULT_FMT,
}


DEFAULT_HEADERS = {
    "Origin": "https://canpl.ca",
    "Referer": "https://canpl.ca/",
    "Accept": "application/json, text/javascript, */*; q=0.01",
}


USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.1 Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.131 Safari/537.36",
]


def get_random_user_agent() -> str:
    return random.choice(USER_AGENTS)


def build_url(base: str, params: dict) -> str:
    """
    Helper to build a URL with query parameters.
    """
    return f"{base}?{urllib.parse.urlencode(params)}"


LEADERBOARD_CATEGORIES: dict[str, str] = {
    "GOALS": "goals",
    "ASSISTS": "assists",
    "SAVES": "saves",
    "PASSES": "total-pass",
    "INTERCEPTIONS": "interception",
    "TACKLES": "tackle",
    "RED_CARDS": "red-cards",
    "YELLOW_CARDS": "yellow-cards",
}

LEADERBOARD_LIMIT = 5
