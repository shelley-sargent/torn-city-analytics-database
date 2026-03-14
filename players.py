import api
import time
import pandas as pd
import numpy as np
import psycopg2
from psycopg2.extras import execute_values
import os
from datetime import datetime, date
from dotenv import load_dotenv

load_dotenv()

# -- Stat chunks (10 per call max)
stat_chunks = [
    "attackswon,attackslost,attacksdraw,attacksassisted,defendswon,defendslost,defendsstalemated,elo,yourunaway,theyrunaway",
    "attackhits,attackmisses,attackdamage,bestdamage,onehitkills,attackcriticalhits,bestkillstreak,retals,moneymugged,largestmug",
    "itemslooted,respectforfaction,rankedwarhits,raidhits,xantaken,cantaken,victaken,drugsused,overdosed,boostersused",
    "energydrinkused,statenhancersused,refills,nerverefills,timeplayed,activestreak,hospital,jailed,networth"
]

# -- Contributor stats (faction API)
contributor_stat_list = ["gymenergy", "gymstrength", "gymdefense", "gymdexterity", "gymspeed", "gymtrains", "territoryrespect"]

# -------------------------------------------------------
# 1. Pull contributor stats
# -------------------------------------------------------
print("Pulling contributor stats...")
contributions = {}
for stat in contributor_stat_list:
    result = api.get("faction_contributors", stats=stat)
    contributions[stat] = result['contributors']
    time.sleep(1)

# Pivot contributor data: keyed by player_id
contributor_by_player = {}
for stat, contributors in contributions.items():
    for player in contributors:
        pid = player['id']
        if pid not in contributor_by_player:
            contributor_by_player[pid] = {
                'player_id': pid,
                'torn_name': player['username']
            }
        contributor_by_player[pid][stat] = player['value']

print(f"Contributor data pulled for {len(contributor_by_player)} players.")

# -------------------------------------------------------
# 2. Pull personal stats for each faction member
# -------------------------------------------------------
print("Pulling faction members...")
members = api.get("faction_members")
member_list = members['members']
print(f"{len(member_list)} members found.")

player_personal_stats = {}

for i, member in enumerate(member_list):
    pid = member['id']
    name = member['name']
    print(f"[{i+1}/{len(member_list)}] Pulling stats for {name}...")

    all_stats = {}
    for chunk in stat_chunks:
        info = api.get("user_personal_stats", user_id=pid, stats=chunk)
        try:
            for stat in info['personalstats']:
                all_stats[stat['name']] = stat['value']
        except KeyError as e:
            print(f"  KeyError: {e} - User ID: {pid}, response: {info}")
        time.sleep(1)

    player_personal_stats[pid] = {
        'player_id': pid,
        'torn_name': name,
        **all_stats
    }

print("Personal stats pull complete.")

# -------------------------------------------------------
# 3. Merge personal stats + contributor stats
# -------------------------------------------------------
for pid, contrib_stats in contributor_by_player.items():
    if pid in player_personal_stats:
        player_personal_stats[pid].update({
            k: v for k, v in contrib_stats.items()
            if k not in ('player_id', 'torn_name')  # don't overwrite these
        })
    else:
        # Player in contributors but not in members list (e.g. left faction)
        player_personal_stats[pid] = contrib_stats

# -------------------------------------------------------
# 4. Build DataFrame
# -------------------------------------------------------
snapshot_date = date.today()
rows = []
for pid, stats in player_personal_stats.items():
    row = {'snapshot_date': snapshot_date, **stats}
    rows.append(row)

df = pd.DataFrame(rows)
df = df.replace({np.nan: None, pd.NaT: None})
df = df.where(df.notnull(), None)

print(f"DataFrame built: {len(df)} rows, {len(df.columns)} columns.")
print(df.head(2))

# -------------------------------------------------------
# 5. Upsert into player_stats_daily
# -------------------------------------------------------
def upload(df):
    try:
        conn = psycopg2.connect(
            host=os.getenv("DB_HOST"),
            database=os.getenv("DB_NAME"),
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD"),
            port=os.getenv("DB_PORT", "5432")
        )
        print("✅ Database connected")
        cursor = conn.cursor()

        cols = list(df.columns)
        values = [tuple(x) for x in df.to_numpy()]

        update_cols = [col for col in cols if col not in ("player_id", "snapshot_date")]
        update_clause = ", ".join(
            [f"{col} = EXCLUDED.{col}" for col in update_cols]
        )

        query = f"""
            INSERT INTO player_stats_daily ({','.join(cols)})
            VALUES %s
            ON CONFLICT (player_id, snapshot_date) DO UPDATE SET {update_clause}
        """

        execute_values(cursor, query, values)
        conn.commit()
        cursor.close()
        conn.close()
        print(f"✅ player_stats_daily updated successfully. {datetime.now()}")

    except Exception as e:
        print(f"❌ Database update failed: {e}")

upload(df)