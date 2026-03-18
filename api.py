import os
import json
import random
import requests
import datetime
from dotenv import load_dotenv

load_dotenv()

def get(api_name, version=2, start=0, end=0, fac_id=int(os.getenv('FACTION_ID')), user_id=2864080, cat=all, limit=1000, war=0, stats=''):

    # -- Load rotating API keys from .env file
    api_keys = os.getenv("API_KEYS") # Retrieves API keys
    selected_key = random.choice(list(json.loads(api_keys).keys())) # Chooses a random API key'''

    base_url = 'https://api.torn.com/v2/' # Torn API V2 Base URL

    # print(api_keys) # -- test
    # print(selected_key) # -- test

    # Dictionary of API endpoints
    api_endpoints = {
        "faction_ranked_wars": f"faction/{fac_id}/rankedwars?cat={cat}&sort=DESC", # -- returns rws faction is in
        "faction_attacks_full": f"faction/attacksfull?limit={limit}&sort=DESC&to={end}&from={start}", # -- returns less info for more attacks
        "faction_attacks": f"faction/attacks?limit={limit}&sort=DESC&to={end}&from={start}", # -- returns more info for fewer attacks
        "faction_organized_crimes": f"faction/crimes?cat={cat}", # -- returns faction crime info
        "faction_ranked_war_report": f"faction/{war}/rankedwarreport", # -- returns war report for specific war #
        "faction_contributors": f"faction/contributors?stat={stats}", # -- returns faction contributor categories
        "faction_members": f"faction/{fac_id}/members", # -- returns list of members in faction
        "user_personal_stats": f"user/{user_id}/personalstats?stat={stats}&timestamp={end}", # -- returns specific publicaly available stats
        "user": f"user?selections={stats}&id={user_id}", # -- returns basic user information
        "forum_threads": f"forum/{cat}/threads?limit={limit}&to={end}" # -- returns forum posts for a specific category
    }

    if api_name not in api_endpoints:
        raise ValueError(f"API name '{api_name}' not recognized.")

    url = base_url + api_endpoints[api_name]

    headers = {'Authorization': f'ApiKey {selected_key}'}

    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        print(f"Error fetching data: {e} - Key used: {selected_key}")
        return None

now = datetime.datetime.now().timestamp()

'''
# Example usage (tests)
result = get("user_personal_stats", end=1740313909, user_id='2893108', stats='xantaken,victaken,timeplayed,refills,retals,respectforfaction,overdosed,boostersused,'
                                 'timespenttraveling,energydrinkused')
print(result)
result = fetch_json("user_personal_stats", end=1740261600, user_id='2893108', stats='xantaken,victaken,timeplayed,refills,retals,respectforfaction,overdosed,boostersused,'
                                 'timespenttraveling,energydrinkused')
print(json.dumps(result, indent=2))

result = fetch_json("user_personal_stats", end=1740313909,
                                             stats='xantaken,victaken,timeplayed,refills,retals,respectforfaction,overdosed,boostersused,'
                                                   'timespenttraveling,energydrinkused')
print(json.dumps(result, indent=2))'''
