
import asyncio
import pandas as pd
from pathlib import Path
from sqlalchemy import select
from datetime import datetime, timedelta
import sys


sys.path.insert(0, str(Path(__file__).parent.parent))

from app.core.database import engine, Base, AsyncSessionLocal
from app.models.nba_models import PlayerGameLog, TeamDefensiveLog

#function to drop existing tables
async def drop_tables():
    print("Dropping existing tables...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    print("Tables dropped successfully")

#function to create tables
async def create_tables():
    print("Creating database tables...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("Tables created successfully")


async def migrate_player_logs():
    #migrate the player game logs using a 60 day cutoff, the ingestion hasnt been run so data may be out of date as of january 2, 2026
    print("\nMigrating player game logs...")

    csv_path = Path(__file__).parent.parent / "data" / "raw" / "player_game_logs.csv"
    df = pd.read_csv(csv_path, parse_dates=['GAME_DATE'])

    #filter to last 60 days for production predictions
    #60 days provides ~30 games per player, enough for L20 rolling averages
    #while keeping database to a small size
    cutoff_date = pd.Timestamp.now() - timedelta(days=60)
    df = df[df['GAME_DATE'] >= cutoff_date]

    print(f"Found {len(df)} player game log records (from {cutoff_date.date()} onwards)")
    print("Using 60-day rolling window for fresh, relevant data")

    async with AsyncSessionLocal() as session:
        #converting to database records
        records = []
        for _, row in df.iterrows():
            record = PlayerGameLog(
                player_id=int(row['PLAYER_ID']) if pd.notna(row['PLAYER_ID']) else None,
                player=row['PLAYER_NAME'],
                team=row['TEAM_ABBREVIATION'],
                game_date=row['GAME_DATE'].date(),
                matchup=row['MATCHUP'] if pd.notna(row['MATCHUP']) else None,
                position=row['POSITION'] if pd.notna(row['POSITION']) else None,
                is_home=bool(row['IS_HOME']) if pd.notna(row['IS_HOME']) else None,
                minutes=float(row['MIN']) if pd.notna(row['MIN']) else None,
                points=float(row['PTS']) if pd.notna(row['PTS']) else None,
                rebounds=float(row['REB']) if pd.notna(row['REB']) else None,
                assists=float(row['AST']) if pd.notna(row['AST']) else None,
                fg_made=float(row['FGM']) if pd.notna(row['FGM']) else None,
                fg_attempted=float(row['FGA']) if pd.notna(row['FGA']) else None,
                three_pt_made=float(row['FG3M']) if pd.notna(row['FG3M']) else None,
                three_pt_attempted=float(row['FG3A']) if pd.notna(row['FG3A']) else None,
                ft_made=float(row['FTM']) if pd.notna(row['FTM']) else None,
                ft_attempted=float(row['FTA']) if pd.notna(row['FTA']) else None,
                turnovers=float(row['TOV']) if pd.notna(row['TOV']) else None,
                personal_fouls=float(row['PF']) if pd.notna(row['PF']) else None,
                plus_minus=float(row['PLUS_MINUS']) if pd.notna(row['PLUS_MINUS']) else None,
            )
            records.append(record)

       
        session.add_all(records)
        await session.commit()

    print(f"✓ Migrated {len(records)} player game log records")


async def migrate_team_defensive_logs():
    #same logic for migrating defensive logs - 60 day cutoff for relevance and size
    print("\nMigrating team defensive logs...")

    csv_path = Path(__file__).parent.parent / "data" / "raw" / "team_defensive_game_logs.csv"
    df = pd.read_csv(csv_path, parse_dates=['GAME_DATE'])

    #filter to last 60 days for production predictions
    #60 days provides ~30 team games, enough for L10 defensive averages and worst case scenarios
    #while keeping database to a small size
    cutoff_date = pd.Timestamp.now() - timedelta(days=60)
    df = df[df['GAME_DATE'] >= cutoff_date]

    print(f"Found {len(df)} team defensive log records (from {cutoff_date.date()} onwards)")
    print(f"Using 60-day rolling window for fresh, relevant data")

    async with AsyncSessionLocal() as session:
        records = []
        for _, row in df.iterrows():
            record = TeamDefensiveLog(
                game_id=int(row['GAME_ID']) if pd.notna(row['GAME_ID']) else None,
                season=row['SEASON'] if pd.notna(row['SEASON']) else None,
                team_id=int(row['TEAM_ID']) if pd.notna(row['TEAM_ID']) else None,
                team=row['TEAM_NAME'],
                game_date=row['GAME_DATE'].date(),
                opponent=row['OPPONENT'],
                pts_allowed=float(row['PTS_ALLOWED']) if pd.notna(row['PTS_ALLOWED']) else None,
                fg3_allowed=float(row['FG3_ALLOWED']) if pd.notna(row['FG3_ALLOWED']) else None,
                fg3a_allowed=float(row['FG3A_ALLOWED']) if pd.notna(row['FG3A_ALLOWED']) else None,
                opp_fg3_pct=float(row['OPP_FG3_PCT']) if pd.notna(row['OPP_FG3_PCT']) else None,
                game_pace=float(row['GAME_PACE']) if pd.notna(row['GAME_PACE']) else None,
            )
            records.append(record)

        session.add_all(records)
        await session.commit()

    print(f"✓ Migrated {len(records)} team defensive log records")


async def verify_migration():
    #verifying the migration by counting records in each table
    print("\nVerifying migration...")

    async with AsyncSessionLocal() as session:
        
        result = await session.execute(select(PlayerGameLog))
        player_count = len(result.scalars().all())

        
        result = await session.execute(select(TeamDefensiveLog))
        team_count = len(result.scalars().all())

        print(f"✓ Database contains:")
        print(f"{player_count} player game logs")
        print(f"{team_count} team defensive logs")


async def main():
    print("=" * 60)
    print("CSV to PostgreSQL Migration")
    print("=" * 60)
    #drop existing tables if they exist
    try:
        await drop_tables()  #drop old tables first
    except Exception as e:
        print(f"⚠ No existing tables to drop (first migration): {e}")

    await create_tables()
    await migrate_player_logs()
    await migrate_team_defensive_logs()
    await verify_migration()

    print("\n" + "=" * 60)
    print("Migration completed successfully!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
