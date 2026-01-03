from sqlalchemy import Column, Integer, String, Float, Date, Index, Boolean
from app.core.database import Base

#structuring for player game logs when migrating to supabse
class PlayerGameLog(Base):
     #data vlaidation to ensure all columns from player_game_logs.csv are stored properly with data types
    __tablename__ = "player_game_logs" 

    id = Column(Integer, primary_key=True, index=True)

    
    player_id = Column(Integer)                    # PLAYER_ID
    player = Column(String, nullable=False, index=True)  # PLAYER_NAME
    team = Column(String, nullable=False)          # TEAM_ABBREVIATION
    game_date = Column(Date, nullable=False, index=True)  # GAME_DATE
    matchup = Column(String)                       # MATCHUP
    position = Column(String)                      # POSITION
    is_home = Column(Boolean)                      # IS_HOME

    
    minutes = Column(Float)                        # MIN
    points = Column(Float)                         # PTS
    rebounds = Column(Float)                       # REB
    assists = Column(Float)                        # AST
    fg_made = Column(Float)                        # FGM
    fg_attempted = Column(Float)                   # FGA
    three_pt_made = Column(Float)                  # FG3M
    three_pt_attempted = Column(Float)             # FG3A
    ft_made = Column(Float)                        # FTM
    ft_attempted = Column(Float)                   # FTA
    turnovers = Column(Float)                      # TOV
    personal_fouls = Column(Float)                 # PF
    plus_minus = Column(Float)                     # PLUS_MINUS

    #define indexes for fast  queeries 
    #composite indexing player and game date for quick lookups
    #composite indexing = sorting based on multiple columns, allows for fast lookups when queried in order,
    #etc sleect lebron --> find lebron --> filter by date --> already sorted withint he lebron column --> sort by date as specified by query  
    __table_args__ = (
        Index('idx_player_date', 'player', 'game_date'),
    )


class TeamDefensiveLog(Base):
    
    __tablename__ = "team_defensive_logs"

    id = Column(Integer, primary_key=True, index=True)

    #game info
    game_id = Column(String(20))                   # GAME_ID - preserve leading zeros like "0042100406" by using string instead of integer
    season = Column(String)                        # SEASON
    team_id = Column(Integer)                      # TEAM_ID
    team = Column(String, nullable=False, index=True)  # TEAM_NAME
    game_date = Column(Date, nullable=False, index=True)  # GAME_DATE
    opponent = Column(String, nullable=False)      # OPPONENT

    #statistics 
    pts_allowed = Column(Float)                    # PTS_ALLOWED
    fg3_allowed = Column(Float)                    # FG3_ALLOWED
    fg3a_allowed = Column(Float)                   # FG3A_ALLOWED
    opp_fg3_pct = Column(Float)                    # OPP_FG3_PCT
    game_pace = Column(Float)                      # GAME_PACE

    #same composite indexing logic applies hjere 
    __table_args__ = (
        Index('idx_team_date', 'team', 'game_date'),
    )
