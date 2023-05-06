#rs_utils.py

from osrs_api import Hiscores
from osrs_api.const import AccountType
import requests


def get_rs_username(db_conn, user_id):
    cursor = db_conn.cursor()
    cursor.execute("SELECT rs_username FROM user_links WHERE discord_id = ?", (user_id,))
    row = cursor.fetchone()
    cursor.close()
    return row[0] if row else None

def get_total_level(username):
    return Hiscores(username, AccountType.NORMAL).total_level

def get_ehb(username):
    search_url = f"https://api.wiseoldman.net/v2/players/search?username={username}&limit=2"
    search_response = requests.get(search_url)

    search_data = search_response.json()
    
    if len(search_data) > 0:
        player_id = search_data[0]["id"]
        ehb_url = f"https://api.wiseoldman.net/v2/players/id/{player_id}"
        ehb_response = requests.get(ehb_url)
        
        if ehb_response.status_code == 200:
            ehb_data = ehb_response.json()
            return ehb_data["ehb"]
        else:
            print(f"Failed to retrieve EHB for player {username}: {ehb_response.status_code}")
    else:
        print(f"Player {username} not found.")

