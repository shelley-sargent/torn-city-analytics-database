import api
import time
import os
import json
import psycopg2
import pandas as pd
import numpy as np
from psycopg2.extras import execute_values
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

# -------------------------------------------------------
# 1. Check for active ranked war
# -------------------------------------------------------

print("Checking for active ranked war...")
ranked_wars = api.get("faction_ranked_wars")
wars = ranked_wars.get("rankedwars", [])

active_war = None
for war in wars:
    if not war.get("end") and war.get("start") <= time.time():
        active_war = war
        break

if not active_war:
    print("No active ranked war. Exiting.")
    exit(0)

war_id = active_war["id"]
war_start = active_war["start"]

opponent_faction = next(
    (f for f in active_war["factions"] if f["id"] != int(os.getenv("FACTION_ID"))),
    None
)
opponent_name = opponent_faction["name"] if opponent_faction else "Unknown"
print(f"Active war found: ID {war_id} vs {opponent_name}")

# -------------------------------------------------------
# 2. Get the last collected attack timestamp from DB
# -------------------------------------------------------
from_timestamp = war_start  # default to war start

try:
    conn = psycopg2.connect(
        host=os.getenv("DB_HOST"),
        database=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        port=os.getenv("DB_PORT", "5432")
    )
    cursor = conn.cursor()
    cursor.execute(
        "SELECT EXTRACT(EPOCH FROM MAX(started))::BIGINT FROM ranked_war_attacks WHERE war_id = %s",
        (war_id,)
    )
    result = cursor.fetchone()
    if result and result[0]:
        from_timestamp = result[0]
        print(f"Pulling attacks from last collected: {datetime.utcfromtimestamp(from_timestamp)}")
    else:
        print(f"No previous attacks found, pulling from war start: {datetime.utcfromtimestamp(war_start)}")
    cursor.close()
    conn.close()
except Exception as e:
    print(f"⚠️ Could not fetch last timestamp, defaulting to war start: {e}")

to_timestamp = int(time.time())

# -------------------------------------------------------
# 3. Pull attacks using timestamp window
# -------------------------------------------------------
print(f"Pulling attacks from {from_timestamp} to {to_timestamp}...")
attacks_raw = api.get("faction_attacks", start=from_timestamp, end=to_timestamp)
all_attacks = attacks_raw.get("attacks", [])

print(f"{len(all_attacks)} attacks found.")

if not all_attacks:
    print("No new attacks. Exiting.")
    exit(0)

# -------------------------------------------------------
# 4. Parse into rows
# -------------------------------------------------------
rows = []
for a in all_attacks:
    attacker = a.get("attacker") or {}
    defender = a.get("defender") or {}
    mods = a.get("modifiers") or {}
    attacker_faction = attacker.get("faction") or {}
    defender_faction = defender.get("faction") or {}
    finishing_effects = a.get("finishing_hit_effects") or []

    rows.append({
        "id": str(a.get("id")),
        "war_id": war_id,
        "code": a.get("code"),
        "started": pd.to_datetime(a.get("started"), unit="s", utc=True),
        "ended": pd.to_datetime(a.get("ended"), unit="s", utc=True),
        "attacker_id": attacker.get("id"),
        "attacker_name": attacker.get("name"),
        "attacker_level": attacker.get("level"),
        "attacker_faction_id": attacker_faction.get("id"),
        "attacker_faction": attacker_faction.get("name"),
        "defender_id": defender.get("id"),
        "defender_name": defender.get("name"),
        "defender_level": defender.get("level"),
        "defender_faction_id": defender_faction.get("id"),
        "defender_faction": defender_faction.get("name"),
        "result": a.get("result"),
        "respect_gain": a.get("respect_gain"),
        "respect_loss": a.get("respect_loss"),
        "chain": a.get("chain"),
        "is_interrupted": a.get("is_interrupted"),
        "is_stealthed": a.get("is_stealthed"),
        "is_raid": a.get("is_raid"),
        "is_ranked_war": a.get("is_ranked_war"),
        "mod_fair_fight": mods.get("fair_fight"),
        "mod_war": mods.get("war"),
        "mod_retaliation": mods.get("retaliation"),
        "mod_group": mods.get("group"),
        "mod_overseas": mods.get("overseas"),
        "mod_chain": mods.get("chain"),
        "mod_warlord": mods.get("warlord"),
        "finishing_hit_effects": json.dumps(finishing_effects) if finishing_effects else None,
    })

df = pd.DataFrame(rows)
df = df.replace({np.nan: None, pd.NaT: None})
df = df.where(df.notnull(), None)

print(f"DataFrame built: {len(df)} rows.")


# -------------------------------------------------------
# 5. Upsert into ranked_war_attacks
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

        update_cols = [col for col in cols if col != "id"]
        update_clause = ", ".join(
            [f"{col} = COALESCE(EXCLUDED.{col}, ranked_war_attacks.{col})" for col in update_cols]
        )

        query = f"""
            INSERT INTO ranked_war_attacks ({','.join(cols)})
            VALUES %s
            ON CONFLICT (id) DO UPDATE SET {update_clause}
        """

        execute_values(cursor, query, values)
        conn.commit()
        cursor.close()
        conn.close()
        print(f"✅ ranked_war_attacks updated successfully. {datetime.now()}")

    except Exception as e:
        print(f"❌ Database update failed: {e}")


upload(df)