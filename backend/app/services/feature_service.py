
# Feature Calculation Service
# Queries PostgreSQL for player and team stats to build features for XGBoost model.
# Replaces CSV-based feature calculation from predict_player.py


from datetime import date, datetime
from typing import Dict, Optional, Tuple
from sqlalchemy import select, and_, func
from sqlalchemy.ext.asyncio import AsyncSession
import pandas as pd

from app.models.nba_models import PlayerGameLog, TeamDefensiveLog


# Team abbreviation to full name mapping
TEAM_ABBR_TO_NAME = {
    "ATL": "Atlanta Hawks", "BOS": "Boston Celtics", "BKN": "Brooklyn Nets",
    "CHA": "Charlotte Hornets", "CHI": "Chicago Bulls", "CLE": "Cleveland Cavaliers",
    "DAL": "Dallas Mavericks", "DEN": "Denver Nuggets", "DET": "Detroit Pistons",
    "GSW": "Golden State Warriors", "HOU": "Houston Rockets", "IND": "Indiana Pacers",
    "LAC": "LA Clippers", "LAL": "Los Angeles Lakers", "MEM": "Memphis Grizzlies",
    "MIA": "Miami Heat", "MIL": "Milwaukee Bucks", "MIN": "Minnesota Timberwolves",
    "NOP": "New Orleans Pelicans", "NYK": "New York Knicks", "OKC": "Oklahoma City Thunder",
    "ORL": "Orlando Magic", "PHI": "Philadelphia 76ers", "PHX": "Phoenix Suns",
    "POR": "Portland Trail Blazers", "SAC": "Sacramento Kings", "SAS": "San Antonio Spurs",
    "TOR": "Toronto Raptors", "UTA": "Utah Jazz", "WAS": "Washington Wizards",
}


class FeatureCalculationService:
    
    # Calculates all features needed for player points prediction from PostgreSQL.

    # Features include:
    # - Player rolling averages (L5, L10)
    # - Rest days
    # - Home/away splits
    # - Opponent defensive stats
    # - Team pace metrics
    # - Positional defense stats
    

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_player_rolling_stats(
        self,
        player_name: str,
        game_date: date,
        lookback_days: int = 5
    ) -> Dict[str, float]:
        
        # Get player's rolling averages for last N games before game_date.

        # Args:
        #     player_name: Player's full name
        #     game_date: Prediction date (exclude games on/after this date)
        #     lookback_days: Number of games to include (5, 10, or 20)

        # Returns:
        #     Dictionary with rolling stats (PTS, MIN, FGA, etc.)
        
        # Query player games before prediction date, ordered by date descending
        stmt = select(PlayerGameLog).where(
            and_(
                PlayerGameLog.player == player_name,
                PlayerGameLog.game_date < game_date #preventing lookahead bias 
            )
        ).order_by(PlayerGameLog.game_date.desc()).limit(lookback_days)

        result = await self.db.execute(stmt)
        games = result.scalars().all()

        # CRITICAL: Require minimum 10 games for reliable predictions
        # This prevents garbage predictions from insufficient data
        if len(games) < lookback_days:
            raise ValueError(
                f"Insufficient data for {player_name}: only {len(games)} games found, "
                f"need {lookback_days} for L{lookback_days} rolling stats."
            )

        # Convert to pandas for easy aggregation
        games_data = [{
            'PTS': g.points,
            'MIN': g.minutes,
            'FGA': g.fg_attempted,
            'FG3A': g.three_pt_attempted,
            'FG3M': g.three_pt_made,
            'FTA': g.ft_attempted,
            'REB': g.rebounds,
            'AST': g.assists,
            'TOV': g.turnovers,
        } for g in games]

        df = pd.DataFrame(games_data)

        # Calculate rolling stats
        stats = {
            f'PTS_L{lookback_days}': df['PTS'].mean(),
            f'PTS_STD_L{lookback_days}': df['PTS'].std() if len(df) > 1 else 0.0,
            f'MIN_L{lookback_days}': df['MIN'].mean(),
            f'FGA_L{lookback_days}': df['FGA'].mean(),
            f'FG3A_L{lookback_days}': df['FG3A'].mean(),
            f'FG3M_L{lookback_days}': df['FG3M'].mean(),
            f'REB_L{lookback_days}': df['REB'].mean(),
            f'AST_L{lookback_days}': df['AST'].mean(),
        }

        # Calculate derived stats
        pts_l = stats[f'PTS_L{lookback_days}']
        min_l = stats[f'MIN_L{lookback_days}']
        stats[f'PTS_PER_MIN_L{lookback_days}'] = pts_l / min_l if min_l > 0 else 0.0

        # Usage proxy (FGA + 0.44*FTA + TOV)
        df['USAGE_PROXY'] = df['FGA'] + 0.44 * df['FTA'] + df['TOV']
        stats[f'USAGE_L{lookback_days}'] = df['USAGE_PROXY'].mean()

        return stats

    async def get_rest_days(
        self,
        player_name: str,
        game_date: date
    ) -> int:
        
        # Calculate days since player's last game before game_date.

        # Args:
        #     player_name: Player's full name
        #     game_date: Prediction date

        # Returns:
        #     Number of rest days (defaults to 2 if no previous game found)
        
        # Get most recent game before prediction date
        stmt = select(PlayerGameLog.game_date).where(
            and_(
                PlayerGameLog.player == player_name,
                PlayerGameLog.game_date < game_date
            )
        ).order_by(PlayerGameLog.game_date.desc()).limit(1)

        result = await self.db.execute(stmt)
        last_game_date = result.scalar()

        if not last_game_date:
            return 2  # Default if no previous game

        return (game_date - last_game_date).days

    async def get_player_info(
        self,
        player_name: str,
        game_date: Optional[date] = None
    ) -> Tuple[str, str, str]:
        # Get player's full name, current team, and position
        # CRITICAL: Uses game_date filter to prevent data leakage from future games
        # Returns player info as of the prediction date, not their most recent game

        # Get most recent game BEFORE prediction date to prevent future data leakage
        if game_date:
            stmt = select(PlayerGameLog).where(
                and_(
                    PlayerGameLog.player.ilike(f'%{player_name}%'),
                    PlayerGameLog.game_date < game_date  # CRITICAL: Prevent lookahead bias
                )
            ).order_by(PlayerGameLog.game_date.desc()).limit(1)
        else:
            # Fallback for non-prediction queries (debug endpoints)
            stmt = select(PlayerGameLog).where(
                PlayerGameLog.player.ilike(f'%{player_name}%')
            ).order_by(PlayerGameLog.game_date.desc()).limit(1)

        result = await self.db.execute(stmt)
        player = result.scalar()

        if not player:
            raise ValueError(f"Player '{player_name}' not found in database")

        return (
            player.player,
            player.team,
            player.position or 'Unknown'
        )

    async def get_opponent_defensive_stats(
        self,
        opponent_full_name: str,
        game_date: date,
        lookback_days: int = 5
    ) -> Dict[str, float]:
        
        # Get opponent's defensive rolling averages (L5 or L10).

        # Args:
        #     opponent_full_name: Opponent team's full name
        #     game_date: Prediction date
        #     lookback_days: Number of games to include (5 or 10)

        # Returns:
        #     Dictionary with defensive stats
        
        # Query opponent's defensive games before prediction date
        stmt = select(TeamDefensiveLog).where(
            and_(
                TeamDefensiveLog.team == opponent_full_name,
                TeamDefensiveLog.game_date < game_date
            )
        ).order_by(TeamDefensiveLog.game_date.desc()).limit(lookback_days)

        result = await self.db.execute(stmt)
        games = result.scalars().all()

        if not games:
            return self._get_default_defensive_stats(lookback_days)

        # Calculate averages
        pts_allowed = sum(g.pts_allowed for g in games) / len(games)
        fg3_allowed = sum(g.fg3_allowed for g in games if g.fg3_allowed) / len(games)
        fg3_pct = sum(g.opp_fg3_pct for g in games if g.opp_fg3_pct) / len(games)
        pace = sum(g.game_pace for g in games if g.game_pace) / len(games)

        return {
            f'DEF_PTS_ALLOWED_L{lookback_days}': pts_allowed,
            f'DEF_3PT_ALLOWED_L{lookback_days}': fg3_allowed,
            f'DEF_3PT_PCT_L{lookback_days}': fg3_pct,
            f'OPP_PACE_L{lookback_days}': pace,
        }

    async def get_positional_defense_stats(
        self,
        opponent_abbr: str,
        player_position: str,
        game_date: date,
        lookback_days: int = 5
    ) -> Dict[str, float]:
        
        # Get opponent's points allowed to specific position (Guard/Forward/Center).

        # This calculates how many points per game opponents at this position
        # have scored against this team.

        # Args:
        #     opponent_abbr: Opponent team abbreviation (e.g., "LAL")
        #     player_position: Position ("Guard", "Forward", "Center")
        #     game_date: Prediction date
        #     lookback_days: Number of games to include

        # Returns:
        #     Dictionary with positional defensive stats
        
        if player_position not in ['Guard', 'Forward', 'Center']:
            return {
                f'DEF_PTS_VS_POSITION_L{lookback_days}': 55.0,
            }

        # Get all games where players of this position played against opponent
        # Extract opponent from matchup (e.g., "@ LAL" or "vs. LAL")
        stmt = select(PlayerGameLog).where(
            and_(
                PlayerGameLog.position == player_position,
                PlayerGameLog.game_date < game_date,
                # Match opponent in matchup string
                PlayerGameLog.matchup.contains(opponent_abbr)
            )
        ).order_by(PlayerGameLog.game_date.desc())

        result = await self.db.execute(stmt)
        games = result.scalars().all()

        if len(games) < 5:
            # Not enough data
            return {
                f'DEF_PTS_VS_POSITION_L{lookback_days}': 55.0,
            }

        # Group by game_date and sum points (multiple players per game)
        games_by_date = {}
        for g in games:
            if g.game_date not in games_by_date:
                games_by_date[g.game_date] = 0
            games_by_date[g.game_date] += g.points

        # Get last N games
        sorted_dates = sorted(games_by_date.keys(), reverse=True)[:lookback_days]
        total_pts = sum(games_by_date[d] for d in sorted_dates)
        avg_pts = total_pts / len(sorted_dates) if sorted_dates else 55.0

        return {
            f'DEF_PTS_VS_POSITION_L{lookback_days}': avg_pts,
        }

    async def get_team_pace_stats(
        self,
        team_abbr: str,
        game_date: date,
        lookback_days: int = 5
    ) -> Dict[str, float]:
        
        # Get team's game pace rolling averages.

        # Args:
        #     team_abbr: Team abbreviation
        #     game_date: Prediction date
        #     lookback_days: Number of games to include

        # Returns:
        #     Dictionary with team pace stats
        
        team_full_name = TEAM_ABBR_TO_NAME.get(team_abbr)

        if not team_full_name:
            return {f'PLAYER_TEAM_PACE_L{lookback_days}': 100.0}

        # Query team's games before prediction date
        stmt = select(TeamDefensiveLog).where(
            and_(
                TeamDefensiveLog.team == team_full_name,
                TeamDefensiveLog.game_date < game_date
            )
        ).order_by(TeamDefensiveLog.game_date.desc()).limit(lookback_days)

        result = await self.db.execute(stmt)
        games = result.scalars().all()

        if not games:
            return {f'PLAYER_TEAM_PACE_L{lookback_days}': 100.0}

        pace_games = [g for g in games if g.game_pace is not None]
        pace = sum(g.game_pace for g in pace_games) / len(pace_games) if pace_games else 100.0

        return {
            f'PLAYER_TEAM_PACE_L{lookback_days}': pace,
        }

    async def build_features_for_prediction(
        self,
        player_name: str,
        player_team: str,
        opponent: str,
        game_date: date,
        is_home: bool
    ) -> Dict[str, float]:
        
        # Build complete feature dictionary for XGBoost prediction.

        # This is the main function that combines all feature calculations.

        # Args:
        #     player_name: Player's full name
        #     player_team: Player's team abbreviation
        #     opponent: Opponent team full name
        #     game_date: Prediction date
        #     is_home: True if home game, False if away

        # Returns:
        #     Dictionary with all features needed for prediction
        
        features = {}

        # Basic feature
        features['IS_HOME'] = 1 if is_home else 0

        # Get player info (validate player exists) - PASS game_date to prevent leakage
        full_name, current_team, position = await self.get_player_info(player_name, game_date)

        # Player rolling stats (L5 and L10)
        l5_stats = await self.get_player_rolling_stats(full_name, game_date, lookback_days=5)
        l10_stats = await self.get_player_rolling_stats(full_name, game_date, lookback_days=10)
        features.update(l5_stats)
        features.update(l10_stats)

        # Rest days
        features['REST_DAYS'] = await self.get_rest_days(full_name, game_date)

        # Opponent defensive stats (L5 and L10)
        opp_def_l5 = await self.get_opponent_defensive_stats(opponent, game_date, lookback_days=5)
        opp_def_l10 = await self.get_opponent_defensive_stats(opponent, game_date, lookback_days=10)
        features.update(opp_def_l5)
        features.update(opp_def_l10)

        # Get opponent abbreviation for positional defense
        opponent_abbr = None
        for abbr, full in TEAM_ABBR_TO_NAME.items():
            if full.lower() == opponent.lower():
                opponent_abbr = abbr
                break

        # Positional defense (L5 and L10)
        if opponent_abbr:
            pos_def_l5 = await self.get_positional_defense_stats(
                opponent_abbr, position, game_date, lookback_days=5
            )
            pos_def_l10 = await self.get_positional_defense_stats(
                opponent_abbr, position, game_date, lookback_days=10
            )
            features.update(pos_def_l5)
            features.update(pos_def_l10)
        else:
            features['DEF_PTS_VS_POSITION_L5'] = 55.0
            features['DEF_PTS_VS_POSITION_L10'] = 55.0

        # Team pace stats (L5 and L10)
        player_pace_l5 = await self.get_team_pace_stats(current_team, game_date, lookback_days=5)
        player_pace_l10 = await self.get_team_pace_stats(current_team, game_date, lookback_days=10)
        features.update(player_pace_l5)
        features.update(player_pace_l10)

        # Calculate expected game pace and possessions
        # These are derived features that combine player and opponent pace
        features['EXPECTED_GAME_PACE_L5'] = (
            features.get('PLAYER_TEAM_PACE_L5', 100.0) + features.get('OPP_PACE_L5', 100.0)
        ) / 2.0

        features['EXPECTED_GAME_PACE_L10'] = (
            features.get('PLAYER_TEAM_PACE_L10', 100.0) + features.get('OPP_PACE_L10', 100.0)
        ) / 2.0

        # Expected possessions (player's share of team possessions)
        min_l5 = features.get('MIN_L5', 30.0)
        min_l10 = features.get('MIN_L10', 30.0)

        features['EXPECTED_POSSESSIONS_L5'] = (
            (min_l5 / 48.0) * features['EXPECTED_GAME_PACE_L5']
        )

        features['EXPECTED_POSSESSIONS_L10'] = (
            (min_l10 / 48.0) * features['EXPECTED_GAME_PACE_L10']
        )

        return features

    def _get_default_player_stats(self) -> Dict[str, float]:
        # Return default player stats when no data available.
        return {
            'PTS_L5': 10.0,
            'PTS_STD_L5': 3.0,
            'MIN_L5': 20.0,
            'FGA_L5': 8.0,
            'FG3A_L5': 2.0,
            'FG3M_L5': 0.7,
            'REB_L5': 3.0,
            'AST_L5': 2.0,
            'PTS_PER_MIN_L5': 0.5,
            'USAGE_L5': 10.0,
        }

    def _get_default_defensive_stats(self, lookback_days: int) -> Dict[str, float]:
        # Return default defensive stats when no data available.
        return {
            f'DEF_PTS_ALLOWED_L{lookback_days}': 110.0,
            f'DEF_3PT_ALLOWED_L{lookback_days}': 12.0,
            f'DEF_3PT_PCT_L{lookback_days}': 0.36,
            f'OPP_PACE_L{lookback_days}': 100.0,
        }
