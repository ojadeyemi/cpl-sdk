from typing import Literal, NotRequired, Required, TypedDict


class Team(TypedDict):
    id: str
    name: str
    shortName: str
    officialName: str
    code: str
    lastUpdated: str


class TeamInfo(TypedDict):
    """Type hint for TeamInfo"""

    contestant: list[Team]
    lastUpdated: str


class Sport(TypedDict):
    id: str
    name: str


class Ruleset(TypedDict):
    id: str
    name: str


class Country(TypedDict):
    id: str
    name: str


class Competition(TypedDict, total=False):
    id: Required[str]
    name: Required[str]
    knownName: str
    competitionCode: str
    competitionFormat: str
    country: Country


class TournamentCalendar(TypedDict, total=False):
    id: Required[str]
    startDate: str
    endDate: str
    name: Required[str]


class ScheduleStage(TypedDict):
    id: str
    formatId: str
    startDate: str
    endDate: str
    name: str


class Venue(TypedDict):
    id: str
    neutral: str
    longName: str
    shortName: str


class ScheduleContestant(TypedDict):
    id: str
    name: str
    shortName: str
    officialName: str
    code: str
    position: str
    country: Country


class BaseContestant(TypedDict):
    contestantId: str
    contestantName: str
    contestantShortName: str
    contestantClubName: str
    contestantCode: str
    rank: int
    matchesPlayed: int


class StandardRanking(BaseContestant):
    points: int
    matchesWon: int
    matchesLost: int
    matchesDrawn: int
    goalsFor: int | None
    goalsAgainst: int | None
    goaldifference: str


class TotalRanking(StandardRanking, total=False):
    rankStatus: str | None
    rankId: str | None
    lastSix: str | None


class AttendanceRanking(BaseContestant):
    venueId: str
    venueName: str
    minimumAttendance: int
    maximumAttendance: int
    totalAttendance: int
    averageAttendance: int
    capacity: int
    percentSold: str


class OverUnderRanking(BaseContestant):
    goals0: int
    goals1: int
    goals2: int
    goals3: int
    goals4: int
    goals5: int
    goals6: int
    goals7: int
    goalsMoreThan7: int
    goalsAverage: str


class Division(TypedDict):
    type: Literal[
        "total",
        "home",
        "away",
        "form-total",
        "form-home",
        "form-away",
        "half-time-total",
        "half-time-home",
        "half-time-away",
        "attendance",
        "over-under",
    ]
    ranking: list[TotalRanking | StandardRanking | AttendanceRanking | OverUnderRanking]


class Stage(TypedDict):
    id: str
    formatId: str
    name: str
    vertical: int
    startDate: str
    endDate: str
    division: list[Division]


class Standings(TypedDict):
    """Type hint for Standings"""

    sport: Sport
    ruleset: Ruleset
    competition: Competition
    tournamentCalendar: TournamentCalendar
    stage: list[Stage]


class MatchInfo(TypedDict):
    id: str
    coverageLevel: str
    date: str
    time: str
    localDate: str
    localTime: str
    week: str
    numberOfPeriods: int
    periodLength: int
    lastUpdated: str
    description: str
    sport: Sport
    ruleset: Ruleset
    competition: Competition
    tournamentCalendar: TournamentCalendar
    stage: Stage
    contestant: list[ScheduleContestant]
    venue: Venue


class Period(TypedDict):
    id: int
    start: str
    end: str
    lengthMin: int
    lengthSec: int
    announcedInjuryTime: int


class Scores(TypedDict):
    ht: dict[str, int]
    ft: dict[str, int]
    total: dict[str, int]


class MatchDetails(TypedDict, total=False):
    periodId: int
    matchStatus: str
    winner: str | None
    matchLengthMin: int | None
    matchLengthSec: int | None
    period: list[Period] | None
    scores: Scores | None
    attendance: str | None


class MatchOfficial(TypedDict):
    id: str
    type: str
    firstName: str
    lastName: str
    shortFirstName: str
    shortLastName: str


class MatchDetailsExtra(TypedDict):
    attendance: str
    matchOfficial: list[MatchOfficial]


class EventBase(TypedDict):
    contestantId: str
    periodId: int
    timeMin: int
    timeMinSec: str
    lastUpdated: str
    timestamp: str
    type: str
    playerId: str
    playerName: str
    optaEventId: str


class Goal(EventBase):
    scorerId: str
    scorerName: str
    homeScore: int
    awayScore: int


class Card(EventBase):
    cardReason: str


class Substitute(TypedDict):
    contestantId: str
    periodId: int
    timeMin: int
    timeMinSec: str
    lastUpdated: str
    timestamp: str
    playerOnId: str
    playerOnName: str
    playerOffId: str
    playerOffName: str
    subReason: str


class LiveData(TypedDict, total=False):
    matchDetails: MatchDetails
    goal: list[Goal] | None
    card: list[Card] | None
    substitute: list[Substitute] | None
    matchDetailsExtra: MatchDetailsExtra | None


class Match(TypedDict):
    matchInfo: MatchInfo
    liveData: LiveData


class Schedule(TypedDict):
    """Type hint for Schedule"""

    match: list[Match]


class Stat(TypedDict):
    name: str
    value: str


class Feed(TypedDict):
    url: str
    team: str


class TeamContestant(TypedDict):
    id: str
    name: str
    stat: list[Stat]
    team: str


class Player(TypedDict):
    position: str
    id: str
    shirtNumber: str
    firstName: str
    lastName: str
    shortFirstName: str
    shortLastName: str
    matchName: str
    team: str
    stat: NotRequired[list[Stat]]
    # Images
    image_url: str
    bio: str


class TeamStats(TypedDict):
    """Type hint for Team stats"""

    ip: str
    feeds: list[Feed]
    contestant: list[TeamContestant]


class PlayerStats(TypedDict):
    """Type hint for Player stats"""

    ip: str
    feeds: list[Feed]
    player: list[Player]


class CompetitionStat(TypedDict):
    competitionId: str
    competitionName: str
    tournamentCalendarId: str
    tournamentCalendarName: str
    goals: int
    assists: int
    penaltyGoals: int
    appearances: int
    yellowCards: int
    secondYellowCards: int
    redCards: int
    substituteIn: int
    substituteOut: int
    subsOnBench: int
    minutesPlayed: int
    shirtNumber: int | None
    competitionFormat: str
    isFriendly: str


class Membership(TypedDict):
    contestantId: str
    contestantType: str
    contestantName: str
    contestantShortName: str
    active: str
    startDate: str
    endDate: str | None
    role: str
    type: str
    transferType: str
    stat: list[CompetitionStat] | None


class Person(TypedDict, total=False):
    # Common fields
    id: str
    firstName: str
    lastName: str
    shortFirstName: str
    shortLastName: str
    matchName: str
    type: str
    gender: str
    nationality: str
    nationalityId: str
    dateOfBirth: str
    status: str

    # Optional fields in both
    secondNationality: str | None
    secondNationalityId: str | None
    placeOfBirth: str | None
    countryOfBirth: str | None
    countryOfBirthId: str | None
    height: int | str | None
    weight: int | str | None

    # Fields in PlayerCareerStats
    lastUpdated: str
    ocSecondNationalityId: str | None
    opSecondNationalityId: str | None
    membership: list["Membership"] | None
    position: str

    # Fields in TeamRoster
    foot: str | None
    shirtNumber: int | None
    startDate: str
    endDate: str | None
    active: str
    knownName: str | None

    # Images
    image_url: str
    bio: str
    name: str


class Kit(TypedDict):
    type: str
    shirtColour1: str
    shortsColour1: str
    socksColour1: str
    socksColour2: str | None


class TeamKits(TypedDict):
    kit: list[Kit]


class Squad(TypedDict):
    contestantId: str
    contestantName: str
    contestantShortName: str
    contestantClubName: str
    contestantCode: str
    tournamentCalendarId: str
    tournamentCalendarStartDate: str
    tournamentCalendarEndDate: str
    competitionName: str
    competitionId: str
    type: str
    teamType: str
    venueName: str
    venueId: str
    person: list[Person]
    teamKits: TeamKits


class PlayerCareerStats(TypedDict):
    """Type hint for a player career stats"""

    person: list[Person]
    lastUpdated: str


class TeamRoster(TypedDict):
    """Type hint for a team's roster"""

    squad: list[Squad]
    lastUpdated: str


class LeaderboardEntry(TypedDict):
    player_id: str
    full_name: str
    position: str
    shirt_number: str
    short_first_name: str
    short_last_name: str
    match_name: str
    team_id: str
    team_name: str
    value: int
    ranking: int
    image_url: NotRequired[str]
    bio: NotRequired[str]


class PlayerLeaderboards(TypedDict):
    """Type hint for player leaderboard"""

    GOALS: list[LeaderboardEntry]
    ASSISTS: list[LeaderboardEntry]
    SAVES: list[LeaderboardEntry]
    PASSES: list[LeaderboardEntry]
    INTERCEPTIONS: list[LeaderboardEntry]
    TACKLES: list[LeaderboardEntry]
    RED_CARDS: list[LeaderboardEntry]
    YELLOW_CARDS: list[LeaderboardEntry]
