"""CPL API CLient for accessing CPL data"""

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
    def __init__(self, timeout: float = 10.0) -> None:
        self.timeout = timeout
        self.client = httpx.Client(timeout=self.timeout)

        self.headers = {**DEFAULT_HEADERS, "User-Agent": get_random_user_agent()}

        self.logger = logger
        self._player_cache: dict[str, dict] = {}
        self._initialize_player_cache()

    def _initialize_player_cache(self):
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

    def _enrich_player_data(self, player_data: dict, player_id: str):
        """Add image and bio to player data."""
        if player_id in self._player_cache:
            player_data["photo_url"] = self._player_cache[player_id].get("photo_url")
            player_data["bio"] = self._player_cache[player_id].get("bio")

        return player_data

    def _get(self, url: str) -> dict:
        """
        Generic method to perform a GET request and handle errors.
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

    def close(self) -> None:
        """
        Close the underlying HTTP client.
        """

        self.client.close()

    def get_standings(self) -> Standings:
        """
        Retrieve league standings data.
        """
        url = f"{STANDINGS_BASE_URL}?tmcl={DEFAULT_SEASON_ID}&_rt={DEFAULT_RT}&_fmt={DEFAULT_FMT}&_ordSrt=asc"
        data = self._get(url)

        return cast(Standings, data)

    def get_schedules(self) -> Schedule:
        """
        Retrieve match schedules data.
        """
        url = build_url(MATCH_BASE_URL, MATCH_PARAMS)
        data = self._get(url)

        return cast(Schedule, data)

    def get_team_info(self) -> TeamInfo:
        """
        Retrieve team information data.
        """
        url = f"{TEAM_INFO_BASE_URL}?tmcl={DEFAULT_SEASON_ID}&_rt={DEFAULT_RT}&_fmt={DEFAULT_FMT}"

        # Cast used to ensure type checker recognizes data as TeamInfo type
        data = cast(TeamInfo, self._get(url))

        return data

    def get_roster(self, team_id: str) -> TeamRoster:
        """Retrieve roster for a specific team with enriched player data."""
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

            # Directly access squad if available
            squad_list = data.get("squad", [])
            if squad_list and len(squad_list) > 0:
                first_squad = squad_list[0]

                # Enrich each person directly in-place
                if "person" in first_squad:
                    for i, person in enumerate(first_squad["person"]):
                        player_id = person.get("id")
                        if player_id:
                            # Update person directly in the original structure
                            enriched_person = cast(Person, self._enrich_player_data(dict(person), player_id))
                            first_squad["person"][i] = enriched_person

            return data

        except RequestError as err:
            if "404" in str(err):
                self.logger.warning(f"Roster not found (404) for team_id: {team_id}")

                return {"squad": [], "lastUpdated": ""}

            raise

    def get_team_stats(self, season_id: str = CPL_DEFAULT_SEASON_ID) -> TeamStatsResponse:
        """
        Retrieve only the list of team stats for a given CPL season,
        filtering out competition and pagination metadata.
        """
        url = CPL_TEAM_STATS_ENDPOINT.format(season_id=season_id)
        data = self._get(url)
        return {"teams": data["teams"]}

    def get_player_stats(
        self,
        season_id: str = CPL_DEFAULT_SEASON_ID,
    ) -> PlayerStatsResponse | None:
        """
        Retrieve player stats for a given CPL season with a single request,
        filtering out competition and pagination metadata.
        """
        url = CPL_PLAYER_STATS_ENDPOINT.format(season_id=season_id)
        params = {"pageNumElement": 500}
        full_url = build_url(url, params)
        resp = self._get(full_url)

        return {"players": resp["players"]}

    def get_player_career(self, player_id: str) -> PlayerCareerStats:
        """
        Retrieve career and detailed info for a specific player with enriched data.
        """
        params = {"prsn": player_id, "_fmt": DEFAULT_FMT, "_rt": DEFAULT_RT}
        url = build_url(PLAYER_CAREER_BASE_URL, params)

        try:
            data = self._get(url)
            career_data = cast(PlayerCareerStats, data)

            if "person" in career_data:
                for i, person in enumerate(career_data["person"]):
                    person_id = person.get("id")
                    if person_id:
                        # Cast the result back to Person type
                        enriched_person = cast(Person, self._enrich_player_data(dict(person), person_id))
                        career_data["person"][i] = enriched_person

            return career_data

        except RequestError as err:
            if "404" in str(err):
                self.logger.warning(f"Player career not found (404) for player_id: {player_id}")

                return {"person": [], "lastUpdated": ""}

            raise

    def _get_players(self) -> list[PlayerStatsEntry]:
        response = self.get_player_stats() or {}
        if "players" not in response:
            self.logger.warning("No players data found")

            return []

        return response.get("players", [])

    def get_leaderboards(self) -> dict[str, list[PlayerLeaderboardEntry]]:
        players = self._get_players()

        leaderboards: dict[str, list[PlayerLeaderboardEntry]] = {category: [] for category in LEADERBOARD_CATEGORIES}

        for player in players:
            stats_dict = {stat["statsId"]: stat for stat in player.get("stats", [])}

            for category, stat_id in LEADERBOARD_CATEGORIES.items():
                if stat_id in stats_dict:
                    stat = stats_dict[stat_id]
                    if stat.get("statsValue") > 2:
                        print(f"Player ID: {player['mediaFirstName']}, Stat ID: {stat_id}, Value: {stat['statsValue']}")

                    entry: PlayerLeaderboardEntry = {
                        "firstName": player.get("mediaFirstName", ""),
                        "lastName": player.get("mediaLastName", ""),
                        "nationality": player.get("nationality", ""),
                        "nationalityIsoCode": player.get("nationalityIsoCode", ""),
                        "value": int(stat.get("statsValue", 0)),
                        "ranking": 0,
                    }

                    leaderboards[category].append(entry)

        for category, entries in leaderboards.items():
            entries.sort(key=lambda x: x["value"], reverse=True)
            leaderboards[category] = entries[:5]

            for i, entry in enumerate(leaderboards[category], 1):
                entry["ranking"] = i

        return leaderboards
