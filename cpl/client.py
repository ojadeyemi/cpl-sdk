"""CPL API Client for accessing CPL data."""

from typing import cast

import httpx

from .constants import (
    CPL_DEFAULT_SEASON_ID,
    CPL_PLAYER_STATS_ENDPOINT,
    CPL_TEAM_STATS_ENDPOINT,
    DEFAULT_FMT,
    DEFAULT_HEADERS,
    DEFAULT_RT,
    DEFAULT_SEASON_ID,
    LEADERBOARD_CATEGORIES,
    LEADERBOARD_LIMIT,
    MATCH_BASE_URL,
    MATCH_PARAMS,
    PLAYER_CAREER_BASE_URL,
    ROSTER_BASE_URL,
    STANDINGS_BASE_URL,
    TEAM_INFO_BASE_URL,
    build_url,
    get_random_user_agent,
)
from .exceptions import APITimeoutError, RequestError
from .logger import logger
from .types import (
    PlayerCareerStats,
    PlayerLeaderboardEntry,
    PlayerStatsEntry,
    PlayerStatsResponse,
    Schedule,
    Standings,
    TeamInfo,
    TeamRoster,
    TeamStatsResponse,
)


class CPLClient:
    """Client for accessing CPL API data."""

    def __init__(self, timeout: float = 10.0) -> None:
        """Initialize the CPL API client.

        Args:
            timeout: HTTP request timeout in seconds
        """
        self.timeout = timeout
        self.client = httpx.Client(timeout=self.timeout)
        self.headers = {**DEFAULT_HEADERS, "User-Agent": get_random_user_agent()}
        self.logger = logger

    def _get(self, url: str) -> dict:
        """Perform a GET request and handle errors.

        Args:
            url: The API endpoint URL

        Returns:
            JSON response data as dictionary

        Raises:
            APITimeoutError: When request times out
            RequestError: When HTTP errors occur
        """
        try:
            self.logger.debug("Requesting URL: %s with headers: %s", url, self.headers)
            response = self.client.get(url, headers=self.headers)
            response.raise_for_status()
            return response.json()

        except httpx.TimeoutException as te:
            self.logger.error("Timeout error fetching %s: %s", url, te)
            raise APITimeoutError(f"Timeout error: {str(te)}") from te

        except httpx.HTTPError as he:
            self.logger.error("HTTP error fetching %s: %s", url, he)
            raise RequestError(f"Error fetching data: {str(he)}") from he

    def _get_players(self) -> list[PlayerStatsEntry]:
        """Get all player stats entries.

        Returns:
            list of player stats entries
        """
        response = self.get_player_stats() or {}
        if "players" not in response:
            self.logger.warning("No players data found")
            return []

        return response.get("players", [])

    def close(self) -> None:
        """Close the underlying HTTP client."""
        self.client.close()

    def get_standings(self) -> Standings:
        """Retrieve league standings data.

        Returns:
            Standings data
        """
        url = f"{STANDINGS_BASE_URL}?tmcl={DEFAULT_SEASON_ID}&_rt={DEFAULT_RT}&_fmt={DEFAULT_FMT}&_ordSrt=asc"
        data = self._get(url)
        return cast(Standings, data)

    def get_schedules(self) -> Schedule:
        """Retrieve match schedules data.

        Returns:
            Schedule data
        """
        url = build_url(MATCH_BASE_URL, MATCH_PARAMS)
        data = self._get(url)
        return cast(Schedule, data)

    def get_team_info(self) -> TeamInfo:
        """Retrieve team information data.

        Returns:
            Team information data
        """
        url = f"{TEAM_INFO_BASE_URL}?tmcl={DEFAULT_SEASON_ID}&_rt={DEFAULT_RT}&_fmt={DEFAULT_FMT}"
        data = self._get(url)
        return cast(TeamInfo, data)

    def get_roster(self, team_id: str) -> TeamRoster:
        """Retrieve roster for a specific team.

        Args:
            team_id: The team's unique ID

        Returns:
            Team roster data
        """
        params = {
            "tmcl": DEFAULT_SEASON_ID,
            "_rt": DEFAULT_RT,
            "detailed": "yes",
            "_fmt": DEFAULT_FMT,
            "ctst": team_id,
        }
        url = build_url(ROSTER_BASE_URL, params)

        try:
            return cast(TeamRoster, self._get(url))

        except RequestError as err:
            if "404" in str(err):
                self.logger.warning("Roster not found (404) for team_id: %s", team_id)
                return {"squad": [], "lastUpdated": ""}
            raise

    def get_team_stats(self, season_id: str = CPL_DEFAULT_SEASON_ID) -> TeamStatsResponse:
        """Retrieve team stats for a given CPL season.

        Args:
            season_id: The season ID to get stats for

        Returns:
            Team stats response containing only the teams data
        """
        url = CPL_TEAM_STATS_ENDPOINT.format(season_id=season_id)
        data = self._get(url)

        return {"teams": data["teams"]}

    def get_player_stats(
        self,
        season_id: str = CPL_DEFAULT_SEASON_ID,
    ) -> PlayerStatsResponse:
        """Retrieve player stats for a given CPL season.

        Args:
            season_id: The season ID to get stats for

        Returns:
            Player stats response containing only the players data
        """
        url = CPL_PLAYER_STATS_ENDPOINT.format(season_id=season_id)
        params = {"pageNumElement": 500}
        full_url = build_url(url, params)
        resp = self._get(full_url)

        return {"players": resp["players"]}

    def get_player_career(self, player_id: str) -> PlayerCareerStats:
        """Retrieve career and detailed info for a specific player.

        Args:
            player_id: The player's unique ID

        Returns:
            Player career stats
        """
        params = {"prsn": player_id, "_fmt": DEFAULT_FMT, "_rt": DEFAULT_RT}
        url = build_url(PLAYER_CAREER_BASE_URL, params)

        try:
            return cast(PlayerCareerStats, self._get(url))

        except RequestError as err:
            if "404" in str(err):
                self.logger.warning("Player career not found (404) for player_id: %s", player_id)

                return {"person": [], "lastUpdated": ""}

            raise

    def get_leaderboards(self) -> dict[str, list[PlayerLeaderboardEntry]]:
        """Retrieve player leaderboards for different statistical categories.

        Returns:
            Dictionary mapping category names to lists of top players
        """
        players = self._get_players()

        leaderboards: dict[str, list[PlayerLeaderboardEntry]] = {category: [] for category in LEADERBOARD_CATEGORIES}

        for player in players:
            stats_dict = {stat["statsId"]: stat for stat in player.get("stats", [])}
            team = player.get("team", {})

            for category, stat_id in LEADERBOARD_CATEGORIES.items():
                if stat_id in stats_dict:
                    stat = stats_dict[stat_id]

                    entry: PlayerLeaderboardEntry = {
                        "firstName": player.get("mediaFirstName", ""),
                        "lastName": player.get("mediaLastName", ""),
                        "nationality": player.get("nationality", ""),
                        "nationalityIsoCode": player.get("nationalityIsoCode", ""),
                        "position": player.get("roleLabel", ""),
                        "value": int(stat.get("statsValue", 0)),
                        "ranking": 0,
                        "teamAcronym": team.get("acronymName", ""),
                        "teamOfficialName": team.get("officialName", ""),
                        "teamShortName": team.get("shortName", ""),
                    }

                    leaderboards[category].append(entry)

        for category, entries in leaderboards.items():
            entries.sort(key=lambda x: x["value"], reverse=True)
            leaderboards[category] = entries[:LEADERBOARD_LIMIT]

            for i, entry in enumerate(leaderboards[category], 1):
                entry["ranking"] = i

        return leaderboards
