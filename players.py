from logging import exception

import api
import time

# list of stats to pull
stat_chunks = stat_chunks = [
    "attackswon,attackslost,attacksdraw,attacksassisted,defendswon,defendslost,defendsstalemated,elo,yourunaway,theyrunaway",
    "attackhits,attackmisses,attackdamage,bestdamage,onehitkills,attackcriticalhits,bestkillstreak,retals,moneymugged,largestmug",
    "itemslooted,respectforfaction,rankedwarhits,raidhits,xantaken,cantaken,victaken,drugsused,overdosed,boostersused",
    "energydrinkused,statenhancersused,refills,nerverefills,timeplayed,activestreak,hospital,jailed,networth"
]

contributor_stats = ["gymenergy", "gymstrength", "gymdefense", "gymdexterity", "gymspeed", "gymtrains", "territoryrespect"]

contributions = {}
for stat in contributor_stats:
    result = api.get("faction_contributors", stats=stat)
    contributions[stat] = result['contributors']
    time.sleep(1)

# Pivot contributor data to be keyed by player_id
contributor_by_player = {}
for stat, contributors in contributions.items():
    for player in contributors:
        pid = player['id']
        if pid not in contributor_by_player:
            contributor_by_player[pid] = {'player_id': pid, 'torn_name': player['username']}
        contributor_by_player[pid][stat] = player['value']

'''
# get list of faction members
members = api.get("faction_members")
count = 0
for member in members['members']:
    print(f"gathering stats for {member['name']} - {count} / {len(members['members'])}")
    count += 1
    all_stats = {}
    for chunk in stat_chunks:
        print(f"gathering {chunk} for {member['name']}")
        info = api.get("user_personal_stats", user_id=member['id'], stats=chunk)
        try:
            for stat in info['personalstats']:
                print(f"gathering {stat}")
                all_stats[stat['name']] = stat['value']
        except KeyError as e:
            print(f"KeyError: {e} - User ID: {member['id']}, stat: {info}")
        time.sleep(1)'''
