# NBA Stats API data fetching service
# Purpose: Fetch player game logs and team defensive stats for specific dates
# Used by: daily ingestion scripts and backfill scripts

import asyncio
import pandas as pd
import pickle
import os
from pathlib import Path
from nba_api.stats.endpoints import leaguegamelog, LeagueGameFinder
from datetime import datetime, timedelta
from typing import List, Dict, Optional


class NBADataService:
    # Service for fetching NBA game data from NBA Stats API

    def __init__(self, rate_limit_seconds: float = 2.0):
        self.rate_limit_seconds = rate_limit_seconds
        self._position_cache = None  # Lazy-loaded position cache

    def _load_position_cache(self):
        if self._position_cache is not None:
            return self._position_cache

        # Try to load from pickle cache
        backend_dir = Path(__file__).parent.parent.parent
        cache_path = backend_dir / "data" / "raw" / "player_positions_cache.pkl"

        if cache_path.exists():
            with open(cache_path, 'rb') as f:
                self._position_cache = pickle.load(f)
            # Filter out Unknown positions
            self._position_cache = {
                k: v for k, v in self._position_cache.items() if v != 'Unknown'
            }
        else:
            self._position_cache = {}

        return self._position_cache

    async def fetch_player_game_logs(self, game_date: str) -> List[Dict]:
        # Fetch player box scores for a specific date
        # Args: game_date: Date string in format "2026-01-08"
        # Returns: List of dicts with player game log data

        print(f"  Fetching player game logs for {game_date}...")

        try:
            # Determine which season this date belongs to
            # NBA season spans Oct-June, so dates Jan-June belong to current season year
            # Dates Oct-Dec belong to next year's season
            date_obj = datetime.strptime(game_date, "%Y-%m-%d")
            year = date_obj.year
            month = date_obj.month

            # If month is Oct-Dec, season starts this year
            # If month is Jan-Sep, season started previous year
            if month >= 10:
                season_str = f"{year}-{str(year + 1)[-2:]}"
            else:
                season_str = f"{year - 1}-{str(year)[-2:]}"

            # Fetch entire season's data (NBA API doesn't support date filtering)
            print(f"    Season: {season_str}")

            # Run blocking NBA API call in thread pool to avoid blocking event loop
            def fetch_logs():
                lg = leaguegamelog.LeagueGameLog(
                    season=season_str,
                    season_type_all_star="Regular Season",
                    player_or_team_abbreviation="P",
                )
                return lg.get_data_frames()[0]

            df = await asyncio.to_thread(fetch_logs)

            # Filter to specific date
            df["GAME_DATE"] = pd.to_datetime(df["GAME_DATE"])
            df = df[df["GAME_DATE"].dt.strftime("%Y-%m-%d") == game_date]

            # Filter out DNPs (Did Not Play)
            df = df[df["MIN"] > 0]

            if df.empty:
                print(f"    No games found for {game_date}")
                return []

            print(f"    Found {len(df)} player performances")

            # Load position cache
            position_cache = self._load_position_cache()

            # Convert to list of dicts
            player_logs = []
            for _, row in df.iterrows():
                player_id = int(row['PLAYER_ID']) if pd.notna(row['PLAYER_ID']) else None
                position = position_cache.get(player_id) if player_id else None

                player_logs.append({
                    'player_id': player_id,
                    'player': row['PLAYER_NAME'],
                    'team': row['TEAM_ABBREVIATION'],
                    'game_date': row['GAME_DATE'].date(),
                    'matchup': row['MATCHUP'] if pd.notna(row['MATCHUP']) else None,
                    'position': position,  # From position cache
                    'is_home': 1 if 'vs.' in row['MATCHUP'] else 0,
                    'minutes': float(row['MIN']) if pd.notna(row['MIN']) else None,
                    'points': float(row['PTS']) if pd.notna(row['PTS']) else None,
                    'rebounds': float(row['REB']) if pd.notna(row['REB']) else None,
                    'assists': float(row['AST']) if pd.notna(row['AST']) else None,
                    'fg_made': float(row['FGM']) if pd.notna(row['FGM']) else None,
                    'fg_attempted': float(row['FGA']) if pd.notna(row['FGA']) else None,
                    'three_pt_made': float(row['FG3M']) if pd.notna(row['FG3M']) else None,
                    'three_pt_attempted': float(row['FG3A']) if pd.notna(row['FG3A']) else None,
                    'ft_made': float(row['FTM']) if pd.notna(row['FTM']) else None,
                    'ft_attempted': float(row['FTA']) if pd.notna(row['FTA']) else None,
                    'turnovers': float(row['TOV']) if pd.notna(row['TOV']) else None,
                    'personal_fouls': float(row['PF']) if pd.notna(row['PF']) else None,
                    'plus_minus': float(row['PLUS_MINUS']) if pd.notna(row['PLUS_MINUS']) else None,
                })

            # Rate limit (use async sleep to avoid blocking event loop)
            await asyncio.sleep(self.rate_limit_seconds)

            return player_logs

        except Exception as e:
            print(f"    ERROR fetching player logs: {e}")
            return []

    async def fetch_team_defensive_logs(self, game_date: str) -> List[Dict]:
        # Fetch team defensive stats for a specific date
        # Args: game_date: Date string in format "2026-01-08"
        # Returns: List of dicts with team defensive data

        print(f"  Fetching team defensive logs for {game_date}...")

        try:
            # Determine which season this date belongs to
            date_obj = datetime.strptime(game_date, "%Y-%m-%d")
            year = date_obj.year
            month = date_obj.month

            # NBA season logic: Oct-Dec = current year start, Jan-Sep = previous year start
            if month >= 10:
                season_str = f"{year}-{str(year + 1)[-2:]}"
            else:
                season_str = f"{year - 1}-{str(year)[-2:]}"

            # Fetch entire season's data (NBA API doesn't support date filtering)
            print(f"    Season: {season_str}")

            # Run blocking NBA API call in thread pool to avoid blocking event loop
            def fetch_team_logs():
                lgf = LeagueGameFinder(season_nullable=season_str)
                return lgf.get_data_frames()[0]

            df = await asyncio.to_thread(fetch_team_logs)

            # Filter to specific date
            df["GAME_DATE"] = pd.to_datetime(df["GAME_DATE"])
            df = df[df["GAME_DATE"].dt.strftime("%Y-%m-%d") == game_date]

            if df.empty:
                print(f"    No games found for {game_date}")
                return []

            # Add season column
            df["SEASON"] = season_str

            # Select stats we want from the opponent (for defensive stats AND opponent possessions)
            opp = df[
                [
                    "GAME_ID",
                    "TEAM_ID",
                    "TEAM_NAME",
                    "PTS",
                    "FG3M",
                    "FG3A",
                    "FGA",
                    "FTA",
                    "OREB",
                    "TOV",
                ]
            ].rename(
                columns={
                    "TEAM_ID": "OPP_TEAM_ID",
                    "TEAM_NAME": "OPPONENT",
                    "PTS": "PTS_ALLOWED",
                    "FG3M": "FG3_ALLOWED",
                    "FG3A": "FG3A_ALLOWED",
                    "FGA": "OPP_FGA",
                    "FTA": "OPP_FTA",
                    "OREB": "OPP_OREB",
                    "TOV": "OPP_TOV",
                }
            )

            # Self-join on GAME_ID to match teams with opponents
            merged = df.merge(opp, on="GAME_ID", how="inner")

            # Drop self-joins (team matched to itself)
            merged = merged[merged["TEAM_ID"] != merged["OPP_TEAM_ID"]]

            # Calculate opponent 3-point percentage
            merged["OPP_FG3_PCT"] = (
                merged["FG3_ALLOWED"] / merged["FG3A_ALLOWED"].replace(0, pd.NA)
            )

            # Calculate possessions for BOTH teams
            # Formula: Possessions ≈ FGA + 0.44 × FTA - OREB + TOV
            merged["TEAM_POSSESSIONS"] = (
                merged["FGA"] +
                0.44 * merged["FTA"] -
                merged["OREB"] +
                merged["TOV"]
            )

            merged["OPP_POSSESSIONS"] = (
                merged["OPP_FGA"] +
                0.44 * merged["OPP_FTA"] -
                merged["OPP_OREB"] +
                merged["OPP_TOV"]
            )

            # Game pace = average of both teams' possessions (more accurate than single team)
            merged["GAME_PACE"] = (merged["TEAM_POSSESSIONS"] + merged["OPP_POSSESSIONS"]) / 2.0

            print(f"    Found {len(merged)} team defensive logs")

            # Convert to list of dicts
            team_logs = []
            for _, row in merged.iterrows():
                team_logs.append({
                    'game_id': str(row['GAME_ID']) if pd.notna(row['GAME_ID']) else None,
                    'season': row['SEASON'],
                    'team_id': int(row['TEAM_ID']) if pd.notna(row['TEAM_ID']) else None,
                    'team': row['TEAM_NAME'],
                    'game_date': row['GAME_DATE'].date(),
                    'opponent': row['OPPONENT'],
                    'pts_allowed': float(row['PTS_ALLOWED']) if pd.notna(row['PTS_ALLOWED']) else None,
                    'fg3_allowed': float(row['FG3_ALLOWED']) if pd.notna(row['FG3_ALLOWED']) else None,
                    'fg3a_allowed': float(row['FG3A_ALLOWED']) if pd.notna(row['FG3A_ALLOWED']) else None,
                    'opp_fg3_pct': float(row['OPP_FG3_PCT']) if pd.notna(row['OPP_FG3_PCT']) else None,
                    'game_pace': float(row['GAME_PACE']) if pd.notna(row['GAME_PACE']) else None,
                })

            # Rate limit (use async sleep to avoid blocking event loop)
            await asyncio.sleep(self.rate_limit_seconds)

            return team_logs

        except Exception as e:
            print(f"    ERROR fetching team defensive logs: {e}")
            return []

    async def insert_player_logs(self, player_logs: List[Dict], session):
        # Insert player game logs into database
        # Args:
        #   player_logs: List of dicts with player data
        #   session: SQLAlchemy async session

        from app.models.nba_models import PlayerGameLog

        if not player_logs:
            print("  No player logs to insert")
            return 0

        records = []
        for log in player_logs:
            record = PlayerGameLog(
                player_id=log.get('player_id'),
                player=log.get('player'),
                team=log.get('team'),
                game_date=log.get('game_date'),
                matchup=log.get('matchup'),
                position=log.get('position'),
                is_home=log.get('is_home'),
                minutes=log.get('minutes'),
                points=log.get('points'),
                rebounds=log.get('rebounds'),
                assists=log.get('assists'),
                fg_made=log.get('fg_made'),
                fg_attempted=log.get('fg_attempted'),
                three_pt_made=log.get('three_pt_made'),
                three_pt_attempted=log.get('three_pt_attempted'),
                ft_made=log.get('ft_made'),
                ft_attempted=log.get('ft_attempted'),
                turnovers=log.get('turnovers'),
                personal_fouls=log.get('personal_fouls'),
                plus_minus=log.get('plus_minus'),
            )
            records.append(record)

        session.add_all(records)
        await session.commit()
        print(f"  Inserted {len(records)} player game logs")
        return len(records)

    async def insert_team_defensive_logs(self, team_logs: List[Dict], session):
        # Insert team defensive logs into database
        # Args:
        #   team_logs: List of dicts with team defensive data
        #   session: SQLAlchemy async session

        from app.models.nba_models import TeamDefensiveLog

        if not team_logs:
            print("  No team defensive logs to insert")
            return 0

        records = []
        for log in team_logs:
            record = TeamDefensiveLog(
                game_id=log.get('game_id'),
                season=log.get('season'),
                team_id=log.get('team_id'),
                team=log.get('team'),
                game_date=log.get('game_date'),
                opponent=log.get('opponent'),
                pts_allowed=log.get('pts_allowed'),
                fg3_allowed=log.get('fg3_allowed'),
                fg3a_allowed=log.get('fg3a_allowed'),
                opp_fg3_pct=log.get('opp_fg3_pct'),
                game_pace=log.get('game_pace'),
            )
            records.append(record)

        session.add_all(records)
        await session.commit()
        print(f"  Inserted {len(records)} team defensive logs")
        return len(records)

    async def cleanup_old_data(self, cutoff_date: str, session):
        # Delete records older than cutoff_date from both tables
        # Args:
        #   cutoff_date: Date string in format "2026-01-08"
        #   session: SQLAlchemy async session

        from app.models.nba_models import PlayerGameLog, TeamDefensiveLog
        from sqlalchemy import delete
        from datetime import datetime

        cutoff = datetime.strptime(cutoff_date, "%Y-%m-%d").date()

        # Delete old player game logs
        result = await session.execute(
            delete(PlayerGameLog).where(PlayerGameLog.game_date < cutoff)
        )
        player_deleted = result.rowcount

        # Delete old team defensive logs
        result = await session.execute(
            delete(TeamDefensiveLog).where(TeamDefensiveLog.game_date < cutoff)
        )
        team_deleted = result.rowcount

        await session.commit()

        print(f"  Deleted {player_deleted} old player game logs")
        print(f"  Deleted {team_deleted} old team defensive logs")

        return player_deleted + team_deleted


# Global service instance
nba_data_service = NBADataService()
