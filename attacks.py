import api
import pandas as pd
import time
import numpy as np
import psycopg2
from psycopg2.extras import execute_values
import datetime
import os

# ------------------------------------
# -- 1. Collect & Clean Attack Data --
# ------------------------------------

# --  Pull latest attack data from Torn API
faction_attacks_full = api.get("faction_attacks_full")
faction_attacks_dict = faction_attacks_full["attacks"]

# -- Convert attacks dict to DataFrame
faction_attacks = pd.DataFrame.from_dict(faction_attacks_dict)

# -- Drop stealthed / incomplete attacks
faction_attacks.dropna(inplace=True)

# -- Extract attacker/defender IDs and faction IDs
faction_attacks["attacker_id"] = faction_attacks["attacker"].apply(
    lambda x: x.get("id") if isinstance(x, dict) else None
)
faction_attacks["attacker_faction_id"] = faction_attacks["attacker"].apply(
    lambda x: x.get("faction_id") if isinstance(x, dict) else None
)
faction_attacks["defender_id"] = faction_attacks["defender"].apply(
    lambda x: x.get("id") if isinstance(x, dict) else None
)
faction_attacks["defender_faction_id"] = faction_attacks["defender"].apply(
    lambda x: x.get("faction_id") if isinstance(x, dict) else None
)
faction_attacks.drop(columns=["attacker", "defender"], inplace=True)

# -- Ensure attack IDs are strings
faction_attacks["id"] = faction_attacks["id"].astype(str)

# -- Convert timestamps
faction_attacks["started"] = pd.to_datetime(faction_attacks["started"], unit="s")
faction_attacks["ended"] = pd.to_datetime(faction_attacks["ended"], unit="s")

# -- Ensure player IDs are integers
faction_attacks["attacker_id"] = faction_attacks["attacker_id"].astype(int)
faction_attacks["defender_id"] = faction_attacks["defender_id"].astype(int)

print(f"{len(faction_attacks)} attacks found.")

# -- Collect player ID numbers
players = pd.unique(faction_attacks[["attacker_id", "defender_id"]].values.ravel("K"))
players = [p for p in players if pd.notna(p)]
print(f"{len(players)} unique players found.")

# ----------------------------------------
# -- 2. Collect Individual Player Stats --
# ----------------------------------------

# -- Collect player personal stats
personal_stats = "elo,bestdamage,revives,attackcriticalhits,boostersused,cantaken,statenhancersused,refills,networth,xantaken"
player_personal_stats = {}
'''

# -- Test for stats in case of API update
for stat in personal_stats.split(","):
    try:
        retrieved_stat = api.get("user_personal_stats", user_id=players[:10], stats=stat)
        print(f"Stats for {players[0]}: {stat} fetched: {retrieved_stat}")
    except Exception as e:
        print(f"Error fetching stats for {stat}: {e}")

for i, player in enumerate(players[:10], start=1):
    try:
        player_stats = api.get("user_personal_stats", user_id=player, stats=personal_stats)
        player_personal_stats[player] = {
            ps["name"]: ps["value"] for ps in player_stats["personalstats"]
        }
        print(player_personal_stats[player])
    except Exception as e:
        print(f"Error fetching stats for player {player}: {e}")
        continue

    # print(f"[{i}/{len(players)}] Player {player} stats fetched.")
    time.sleep(1)

print('All stats fetched.')

'''
for i, player in enumerate(players, start=1):
    try:
        player_stats = api.get("user_personal_stats", user_id=player, stats=personal_stats)
        player_personal_stats[player] = {
            ps["name"]: ps["value"] for ps in player_stats["personalstats"]
        }
    except Exception as e:
        print(f"Error fetching stats for player {player}: {e}")
        continue

    # print(f"[{i}/{len(players)}] Player {player} stats fetched.")
    time.sleep(1)

print('All stats fetched.')

# ---------------------------------------
# -- 1. Merge Data & Create DataFrames --
# ---------------------------------------


# -- Create dataframe with player stats
player_stats_df = pd.DataFrame.from_dict(player_personal_stats, orient="index")
player_stats_df.index = player_stats_df.index.astype(int)
# print(player_stats_df)
print('Initial dataframe created.')

# Join stats to faction attacks
full_attack_info = faction_attacks.merge(
    player_stats_df.rename(columns=lambda c: f"attacker_{c}"),
    left_on="attacker_id",
    right_index=True,
    how="left"
)
print('Attacker stats joined.')

full_attack_info = full_attack_info.merge(
    player_stats_df.rename(columns=lambda c: f"defender_{c}"),
    left_on="defender_id",
    right_index=True,
    how="left"
)
print('Defender stats joined.')
    # -- Deduplicate
full_attack_info.drop_duplicates(subset="id", inplace=True)

# -- Eliminate NaN/NaT values for DB import
df = full_attack_info.replace({np.nan: None, pd.NaT: None})
df = full_attack_info.where(full_attack_info.notnull(), None)
print('Final dataframe created.')

# print(full_attack_info.notnull().sum().sort_values(ascending=False))

bigint_cols = [
    'attacker_attackcriticalhits', 'attacker_xantaken', 'attacker_boostersused',
    'attacker_revives', 'attacker_cantaken', 'attacker_networth', 'attacker_bestdamage',
    'attacker_refills', 'attacker_statenhancersused', 'defender_attackcriticalhits',
    'defender_xantaken', 'defender_boostersused', 'defender_revives', 'defender_cantaken',
    'defender_networth', 'defender_bestdamage', 'defender_refills', 'defender_statenhancersused'
]

for col in bigint_cols:
    full_attack_info[col] = pd.to_numeric(full_attack_info[col], errors='coerce').astype('Int64')

# -- connect to database
def upload():
    try:
        conn = psycopg2.connect(
            host=os.getenv("DB_HOST"),
            database=os.getenv("DB_NAME"),
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD"),
            port=os.getenv("DB_PORT")
        )

        print("✅ Database connected")

        cursor = conn.cursor()

        cols = list(df.columns)
        print(df.head())
        print(cols)
        values = [tuple(x) for x in df.to_numpy()]

        update_cols = [col for col in cols if col != "id"]

        update_clause = ", ".join(
            [f"{col} = COALESCE(EXCLUDED.{col}, attacks.{col})" for col in update_cols]
        )

        query = f"""
                INSERT INTO attacks({','.join(cols)})
                VALUES %s
                ON CONFLICT (id) DO UPDATE SET {update_clause}
        """

        execute_values(cursor, query, values)
        print(f"✅ Query executed successfully. {datetime.now()}")

        conn.commit()
        cursor.close()
        conn.close()
        print(f"✅ Connection closed successfully.")
    except Exception as e:
        print(f"❌ Database update failed: {e}")


upload()
