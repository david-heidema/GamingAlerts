import datetime
import smtplib
import sys
from time import sleep
import time
import pytz
import requests
import os
import load_dotenv
import yaml

load_dotenv.load_dotenv() 

discord_client_id = os.getenv("CLIENT_ID")
discord_client_secret = os.getenv("CLIENT_SECRET")
discord_bot_token = os.getenv("BOT_TOKEN")
steam_key = os.getenv("STEAM_KEY")
steam_user_id = os.getenv("STEAM_USER_ID")
email_to_send_from = os.getenv("GMAIL_APP_EMAIL")
app_password_from_email = os.getenv("GMAIL_APP_PASSWORD")


carrier_gateway_map = {
    "Verizon": "vtext.com",
    "Mint_Mobile": "tmomail.net",
    "T_Mobile": "tmomail.net",
    "Sprint": "messaging.sprintpcs.com",
    "AT&T": "txt.att.net",
    "Pure_Talk": "txt.att.net",
    "Boost_Mobile": "smsmyboostmobile.com",
    "Cricket": "sms.cricketwireless.net",
    "US_Cellular": "email.uscc.net"
}


def load_user_config():
    with open("userConfig.yaml") as stream:
        try: 
            return yaml.safe_load(stream)
        except:
            print(exec)
       


###https://discord.com/developers/docs/topics/oauth2#bot-users
def get_discord_bot_token():
  
    data = {
        'scope': 'identify connections',
        'grant_type': 'client_credentials'
    
    }
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded'
    }
    r = requests.post('https://discord.com/api/v10/oauth2/token', data=data, headers=headers, auth=(discord_client_id, discord_client_secret))
    return r.json()


def get_steam_user_id(token):
    url = "https://discord.com/api/v9/users/@me/connections"
    headers = {
        "Authorization": f"Bearer {token}"
    }

    try:
        # Fetch user connections
        response = requests.get(url, headers=headers)
        response.raise_for_status()  # Raise an exception for 4xx/5xx status codes
        connections = response.json()
        # Find the Steam connection and get the current game
        for connection in connections:
            if connection.get('type') == 'steam':
                steam_user_id = connection.get('id')
                return steam_user_id
            
    except requests.exceptions.RequestException as e:
        print(f"An error occurred: {e}")
        return None
    

def get_steam_user_summary(steam_id):
    api_key = steam_key  # Replace with your Steam API key
    url = f'http://api.steampowered.com/ISteamUser/GetPlayerSummaries/v0002/?key={api_key}&steamids={steam_id}'

    try:
        response = requests.get(url)
        response.raise_for_status() 
        data = response.json()
        return data

    except requests.exceptions.RequestException as e:
        print(f"An error occurred: {e}")
        return None

def get_curr_steam_game(summary_data):
    player = summary_data['response']['players'][0]
    if "gameextrainfo" in player:
        return player['gameextrainfo']
    return "0"

def get_steam_logoff(summary_data):
    player = summary_data['response']['players'][0]
    return player['lastlogoff']

def textContent(gamer_name, curr_game, gaming_status = True):

    now = pytz.timezone('America/New_York')
    utc_Ny = datetime.datetime.now(now)
    format_time= str(utc_Ny.strftime('%H:%M'))
    subject = 'GAMING ALERT!'

    if gaming_status:
        text = f'\n{gamer_name} is playing {curr_game}! \nGaming session started at {format_time}'
    else:
        text = 'Gaming session ended at {format_time}'
   
    ## ensure the message is ASCII before using SMTP protocol
    message = 'Subject: {}\n\n{}'.format(subject, text).encode('ascii', 'replace').decode('ascii').strip().replace("?","")
    return message
    
def sendText(curr_game, gamer_details, gaming_status = True):

    gamer_name = gamer_details.get('gamerName') 
    recipient_carrier = gamer_details.get('recipientCarrier')
    recipient_number = gamer_details.get('recipientPhoneNumber')
    recipient_name = gamer_details.get('recipientName')

    if gamer_name is None or recipient_carrier is None or recipient_number is None or recipient_name is None:
        sys.exit('Malformed data entered in the userConfig file.')
    
    recipient_carrier_gateway = carrier_gateway_map.get(recipient_carrier) 
    num = f'{recipient_number}@{recipient_carrier_gateway}'

    message = textContent(gamer_name, curr_game, gaming_status)
    try:
        s = smtplib.SMTP('smtp.gmail.com',587,timeout=3000)
        s.starttls()
        s.login(email_to_send_from, app_password_from_email)
        s.sendmail(email_to_send_from, num, message)
        print("Successfully texted", recipient_name)
        
    except Exception as e:
        sys.exit( "mail failed- %s", e ) # give an error message
    finally:
        s.quit() 
    
if __name__ == "__main__":

    ##Default to getting the Steam User Id from the env vars, otherwise get it from Discord
    if(not steam_user_id and discord_client_secret and discord_client_id):
        response_data = get_discord_bot_token()
        discord_user_token = response_data["access_token"]
        steam_user_id = get_steam_user_id(discord_user_token)

    user_details = load_user_config()
    last_iter_steam_game = "NA"
    start_gaming_time = int(time.time())

    while(True):
        user_data = get_steam_user_summary(steam_user_id)
        current_steam_game = get_curr_steam_game(user_data)
        print(user_data)
        if start_gaming_time < get_steam_logoff(user_data) and last_iter_steam_game != "NA":
            sendText(current_steam_game, user_details, False)
            sys.exit("Gamer is no longer online, goodbye.")
        elif current_steam_game != "0" and current_steam_game != last_iter_steam_game:
            sendText(current_steam_game, user_details)
            last_iter_steam_game = current_steam_game
        print(last_iter_steam_game)
        time.sleep(6000)
