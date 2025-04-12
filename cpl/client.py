"""CPL API CLient for accessing CPL data"""

from typing import cast

import httpx

from .constants import (
    DEFAULT_FMT,
    DEFAULT_HEADERS,
    DEFAULT_RT,
    DEFAULT_SEASON_ID,
    MATCH_BASE_URL,
    MATCH_PARAMS,
    PLAYER_CAREER_BASE_URL,
    PLAYER_STATS_BASE_URL,
    PLAYERS_ENDPOINT,
    ROSTER_BASE_URL,
    STANDINGS_BASE_URL,
    TEAM_INFO_BASE_URL,
    TEAM_STATS_BASE_URL,
    build_url,
    get_random_user_agent,
)
from .exceptions import APITimeoutError, RequestError
from .logger import logger
from .types import (
    LeaderboardEntry,
    Person,
    Player,
    PlayerCareerStats,
    PlayerLeaderboards,
    PlayerStats,
    Schedule,
    Standings,
    Stat,
    TeamInfo,
    TeamRoster,
    TeamStats,
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
                        "image_url": player.get("thumbnail") or player.get("default") or "",
                        "bio": player.get("bio") or "",
                        "name": player.get("name") or "",
                    }

            self.logger.info(f"Player cache initialized with {len(self._player_cache)} players")

        except Exception as err:
            self.logger.error(f"Failed to initialize player cache: {err}")

    def _enrich_player_data(self, player_data: dict, player_id: str):
        """Add image and bio to player data."""
        if player_id in self._player_cache:
            player_data["image_url"] = self._player_cache[player_id].get("image_url")
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

    def get_team_stats(self, season_id: str = DEFAULT_SEASON_ID) -> TeamStats:
        """
        Retrieve team statistics data.
        """
        url = f"{TEAM_STATS_BASE_URL}?season={season_id}"

        try:
            data = self._get(url)
            return cast(TeamStats, data)

        except RequestError as err:
            if "404" in str(err):
                self.logger.warning(f"Team stats not found (404) for season_id: {season_id}")

                return {"ip": "", "feeds": [], "contestant": []}

            raise

    def get_player_stats(self, season_id: str = DEFAULT_SEASON_ID) -> PlayerStats:
        """
        Retrieve player statistics data with enriched bio and image URL.
        """
        url = f"{PLAYER_STATS_BASE_URL}?season={season_id}"

        try:
            data = self._get(url)
            stats_data = cast(PlayerStats, data)

            # Enrich each player with bio and image URL
            if "player" in stats_data:
                for i, player in enumerate(stats_data["player"]):
                    player_id = player.get("id")
                    if player_id:
                        # Must modify player object directly since Player TypedDict doesn't have bio/image fields
                        player_data = dict(player)
                        enriched_player = self._enrich_player_data(player_data, player_id)

                        # Update player in the original data structure with type cast
                        stats_data["player"][i] = cast(Player, enriched_player)

            return stats_data

        except RequestError as err:
            if "404" in str(err):
                self.logger.warning(f"Player stats not found (404) for season: {season_id}")

                return {"ip": "", "feeds": [], "player": []}

            raise

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

    def get_leaderboards(self, player_stats: PlayerStats, team_stats: TeamStats):
        """Get both player and team leaderboards."""

        leaderboard_data = self._calculate_player_leaderboards(player_stats, team_stats)

        return leaderboard_data

    def _extract_stat_value(self, stats: list[Stat], stat_names: list[str]) -> int:
        """Extract and sum values for specified stat names."""
        total = 0
        for stat in stats:
            if stat["name"] in stat_names:
                total += int(stat["value"])

        return total

    def _calculate_player_leaderboards(self, player_stats: PlayerStats, team_stats: TeamStats) -> PlayerLeaderboards:
        """Calculate player leaderboards for various stats."""
        leaderboards: PlayerLeaderboards = {
            "GOALS": [],
            "ASSISTS": [],
            "SAVES": [],
            "PASSES": [],
            "INTERCEPTIONS": [],
            "TACKLES": [],
            "RED_CARDS": [],
            "YELLOW_CARDS": [],
        }

        # Create team code to name mapping
        team_map = {contestant["team"]: contestant["name"] for contestant in team_stats.get("contestant", [])}

        for player in player_stats.get("player", []):
            if "stat" not in player:
                continue

            # Extract stats
            goals = self._extract_stat_value(player["stat"], ["Goals"])
            assists = self._extract_stat_value(player["stat"], ["Goal Assists"])
            saves = self._extract_stat_value(player["stat"], ["Saves Made"])
            passes = self._extract_stat_value(player["stat"], ["Total Passes"])
            interceptions = self._extract_stat_value(player["stat"], ["Interceptions"])
            tackles = self._extract_stat_value(player["stat"], ["Tackles Won"])
            red_cards = self._extract_stat_value(player["stat"], ["Total Red Cards"])
            yellow_cards = self._extract_stat_value(player["stat"], ["Yellow Cards"])

            # Base player data
            player_id = player["id"]
            current_player_data: LeaderboardEntry = {
                "player_id": player_id,
                "full_name": f"{player['firstName']} {player['lastName']}",
                "position": player["position"],
                "shirt_number": player["shirtNumber"],
                "short_first_name": player["shortFirstName"],
                "short_last_name": player["shortLastName"],
                "match_name": player["matchName"],
                "team_id": player["team"],
                "team_name": team_map.get(player["team"], ""),
                "value": 0,
                "ranking": 0,
            }

            player_data = self._enrich_player_data(dict(current_player_data), player_id)

            # Add to leaderboards if values exist
            stat_mappings = [
                (goals, "GOALS"),
                (assists, "ASSISTS"),
                (saves, "SAVES"),
                (passes, "PASSES"),
                (interceptions, "INTERCEPTIONS"),
                (tackles, "TACKLES"),
                (red_cards, "RED_CARDS"),
                (yellow_cards, "YELLOW_CARDS"),
            ]

            for value, category in stat_mappings:
                if value > 0:
                    entry = player_data.copy()
                    entry["value"] = value
                    leaderboards[category].append(entry)

        # Sort and rank each leaderboard
        for category in leaderboards:
            leaderboards[category] = sorted(leaderboards[category], key=lambda x: x["value"], reverse=True)

            for i, entry in enumerate(leaderboards[category]):
                entry["ranking"] = i + 1

        return leaderboards
