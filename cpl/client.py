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
    PLAYERS_ENDPOINT,
    ROSTER_BASE_URL,
    STANDINGS_BASE_URL,
    TEAM_INFO_BASE_URL,
    build_url,
    get_random_user_agent,
)
from .exceptions import APITimeoutError, RequestError
from .logger import logger
from .types import (
    Person,
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
        self._player_cache: dict[str, dict] = {}
        self._initialize_player_cache()

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
            self.logger.debug(f"Requesting URL: {url} with headers: {self.headers}")
            response = self.client.get(url, headers=self.headers)
            response.raise_for_status()
            return response.json()

        except httpx.TimeoutException as te:
            self.logger.error(f"Timeout error fetching {url}: {str(te)}")
            raise APITimeoutError(f"Timeout error: {str(te)}") from te

        except httpx.HTTPError as he:
            self.logger.error(f"HTTP error fetching {url}: {str(he)}")
            raise RequestError(f"Error fetching data: {str(he)}") from he

    def _initialize_player_cache(self) -> None:
        """Load all player data into cache during initialization."""
        try:
            url = PLAYERS_ENDPOINT
            data: dict[str, list[dict]] = self._get(url)

            if not data or "players" not in data:
                self.logger.warning("Failed to initialize player cache: No players data found")
                return

            # Build player cache with ID as key
            for player in data["players"]:
                player_id = player.get("id")
                if player_id:
                    self._player_cache[player_id] = {
                        "photo_url": player.get("thumbnail") or player.get("default") or "",
                        "bio": player.get("bio") or "",
                        "name": player.get("name") or "",
                    }

            self.logger.info(f"Player cache initialized with {len(self._player_cache)} players")

        except Exception as err:
            self.logger.error(f"Failed to initialize player cache: {err}")

    def _enrich_player_data(self, player_data: dict, player_id: str) -> dict:
        """Add image and bio to player data.

        Args:
            player_data: The player data dictionary to enrich
            player_id: The player's unique ID

        Returns:
            Enriched player data dictionary
        """
        if player_id in self._player_cache:
            player_data["photo_url"] = self._player_cache[player_id].get("photo_url")
            player_data["bio"] = self._player_cache[player_id].get("bio")

        return player_data

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
        """Retrieve roster for a specific team with enriched player data.

        Args:
            team_id: The team's unique ID

        Returns:
            Team roster data with enriched player information
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
            data = cast(TeamRoster, self._get(url))

            # Access and enrich player data in the squad if available
            squad_list = data.get("squad", [])
            if squad_list and len(squad_list) > 0:
                first_squad = squad_list[0]

                # Enrich each person's data directly in-place
                if "person" in first_squad:
                    for i, person in enumerate(first_squad["person"]):
                        player_id = person.get("id")
                        if player_id:
                            enriched_person = cast(Person, self._enrich_player_data(dict(person), player_id))
                            first_squad["person"][i] = enriched_person

            return data

        except RequestError as err:
            if "404" in str(err):
                self.logger.warning(f"Roster not found (404) for team_id: {team_id}")
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
        params = {"pageNumElement": 500}  # Request more players to avoid pagination
        full_url = build_url(url, params)
        resp = self._get(full_url)

        return {"players": resp["players"]}

    def get_player_career(self, player_id: str) -> PlayerCareerStats:
        """Retrieve career and detailed info for a specific player.

        Args:
            player_id: The player's unique ID

        Returns:
            Player career stats with enriched player information
        """
        params = {"prsn": player_id, "_fmt": DEFAULT_FMT, "_rt": DEFAULT_RT}
        url = build_url(PLAYER_CAREER_BASE_URL, params)

        try:
            data = self._get(url)
            career_data = cast(PlayerCareerStats, data)

            # Enrich each person's data in the career stats
            if "person" in career_data:
                for i, person in enumerate(career_data["person"]):
                    person_id = person.get("id")
                    if person_id:
                        enriched_person = cast(Person, self._enrich_player_data(dict(person), person_id))
                        career_data["person"][i] = enriched_person

            return career_data

        except RequestError as err:
            if "404" in str(err):
                self.logger.warning(f"Player career not found (404) for player_id: {player_id}")

                return {"person": [], "lastUpdated": ""}

            raise

    # TODO: add team name to leaderbaord
    def get_leaderboards(self) -> dict[str, list[PlayerLeaderboardEntry]]:
        """Retrieve player leaderboards for different statistical categories.

        Returns:
            Dictionary mapping category names to lists of top players
        """
        players = self._get_players()

        # Initialize leaderboards with empty lists for each category
        leaderboards: dict[str, list[PlayerLeaderboardEntry]] = {category: [] for category in LEADERBOARD_CATEGORIES}

        # Process each player's stats and add to relevant leaderboards
        for player in players:
            # Create lookup dictionary for player's stats by stat ID
            stats_dict = {stat["statsId"]: stat for stat in player.get("stats", [])}

            # Add player to each leaderboard category if they have the relevant stat
            for category, stat_id in LEADERBOARD_CATEGORIES.items():
                if stat_id in stats_dict:
                    stat = stats_dict[stat_id]

                    # Create leaderboard entry for this player
                    entry: PlayerLeaderboardEntry = {
                        "firstName": player.get("mediaFirstName", ""),
                        "lastName": player.get("mediaLastName", ""),
                        "nationality": player.get("nationality", ""),
                        "nationalityIsoCode": player.get("nationalityIsoCode", ""),
                        "position": player.get("roleLabel", ""),
                        "value": int(stat.get("statsValue", 0)),
                        "ranking": 0,  # Will be set after sorting
                    }

                    leaderboards[category].append(entry)

        # Sort each leaderboard by value (descending) and assign rankings
        for category, entries in leaderboards.items():
            entries.sort(key=lambda x: x["value"], reverse=True)
            leaderboards[category] = entries[:LEADERBOARD_LIMIT]

            # Assign rankings (1-based)
            for i, entry in enumerate(leaderboards[category], 1):
                entry["ranking"] = i

        return leaderboards
