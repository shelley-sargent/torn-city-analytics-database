import api
import pandas as pd
import time
import numpy as np

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
personal_stats = ("elo,bestdamage,revives,attackcriticalhits,boostersused,cantaken,statenhancersused,refills,networth,xantaken")
player_personal_stats = {}

'''
# -- Test for stats in case of API update
for stat in personal_stats.split(","):
    try:
        retrieved_stat = api.get("user_personal_stats", user_id=players[10], stats=stat)
        print(f"Stats for {players[0]}: {stat} fetched: {retrieved_stat}")
    except Exception as e:
        print(f"Error fetching stats for {stat}: {e}")
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
full_attack_info = full_attack_info.replace({np.nan: None, pd.NaT: None})
full_attack_info = full_attack_info.where(full_attack_info.notnull(), None)
print('Final dataframe created.')

# print(full_attack_info.notnull().sum().sort_values(ascending=False))
