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
from carriers import carrier_gateway_map

load_dotenv.load_dotenv()

discord_client_id = os.getenv('DISCORD_CLIENT_ID')
discord_client_secret = os.getenv('DISCORD_CLIENT_SECRET')
discord_bot_token = os.getenv('DISCORD_BOT_TOKEN')
steam_key = os.getenv('STEAM_KEY')
steam_user_id = os.getenv('STEAM_USER_ID')
email_to_send_from = os.getenv('GMAIL_APP_EMAIL')
app_password_from_email = os.getenv('GMAIL_APP_PASSWORD')

carrier_gateway_map = carrier_gateway_map

def load_user_config():
    config_file_name = 'userConfig.yaml'
    with open(config_file_name) as stream:
        try: 
            return yaml.safe_load(stream)
        except OSError:
            print('Could not open/read file:', config_file_name)
            sys.exit()
       
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
    url = 'https://discord.com/api/v9/users/@me/connections'
    headers = {
        'Authorization': f'Bearer {token}'
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
        print(f'An error occurred: {e}')
        sys.exit()
    

def get_steam_user_summary(steam_id):
    api_key = steam_key  # Replace with your Steam API key
    url = f'http://api.steampowered.com/ISteamUser/GetPlayerSummaries/v0002/?key={api_key}&steamids={steam_id}'

    try:
        response = requests.get(url)
        response.raise_for_status() 
        data = response.json()
        return data

    except requests.exceptions.RequestException as e:
        print(f'An error occurred: {e}')
        sys.exit()


# Find the value associated with a key in a JSON object
def find_key(data, key):
    if isinstance(data, dict):
        if key in data:
            return data[key]
        # Recursively search in nested dictionaries
        for value in data.values():
            result = find_key(value, key)
            if result is not None:
                return result
    elif isinstance(data, list):
        # Search in each item if the data is a list
        for item in data:
            result = find_key(item, key)
            if result is not None:
                return result
    return None

def get_curr_steam_game(summary_data):
    return find_key(summary_data, 'gameextrainfo')

def get_steam_logoff(summary_data):
    return find_key(summary_data, 'lastlogoff')

def text_content(gamer_name, curr_game, gaming_status = True):

    ## TODO: Parameterize to be used to other time zones, make a map so user can enter plan english
    time_zone = pytz.timezone('America/New_York')
    curr_time = datetime.datetime.now(time_zone)
    print(curr_time)
    format_time= str(curr_time.strftime('%H:%M'))
    subject = 'GAMING ALERT!'

    if gaming_status:
        text = f'\n{gamer_name} is playing {curr_game}! \nGaming session started at {format_time}'
    else:
        text = f'Gaming session ended at {format_time}'
   
    ## Ensure the message is ASCII before using SMTP
    message = 'Subject: {}\n\n{}'.format(subject, text).encode('ascii', 'replace').decode('ascii').strip().replace('?','')
    return message
    
def send_text(curr_game, gamer_details, gaming_status = True):

    gamer_name = gamer_details.get('gamerName')
    recipient_carrier = gamer_details.get('recipientCarrier')
    recipient_number = gamer_details.get('recipientPhoneNumber')

    if gamer_name is None or recipient_carrier is None or recipient_number is None :
        sys.exit('Malformed data entered in the userConfig file.')
    
    recipient_carrier_gateway = carrier_gateway_map.get(recipient_carrier) 
    num = f'{recipient_number}@{recipient_carrier_gateway}'

    message = text_content(gamer_name, curr_game, gaming_status)
    try:
        s = smtplib.SMTP('smtp.gmail.com',587,timeout=3000)
        s.starttls()
        s.login(email_to_send_from, app_password_from_email)
        s.sendmail(email_to_send_from, num, message)
        print(f'Successfully texted - {message}')
        
    except Exception as e:
        sys.exit( 'mail failed- %s', e ) # give an error message
    finally:
        s.quit() 
    
if __name__ == '__main__':

    ##Default to getting the Steam User Id from the env vars, otherwise get it from Discord
    if(not steam_user_id and discord_client_secret and discord_client_id):
        response_data = get_discord_bot_token()
        discord_user_token = response_data['access_token']
        steam_user_id = get_steam_user_id(discord_user_token)

    user_details = load_user_config()
    last_iter_steam_game = None
    start_gaming_time = int(time.time())

    iter = 0
    while(True):
        iter+=1
        user_data = get_steam_user_summary(steam_user_id)
        current_steam_game = get_curr_steam_game(user_data)

        # Send an update text if playing a new game
        if current_steam_game is not None and current_steam_game != last_iter_steam_game:
            send_text(current_steam_game, user_details)
            iter = 0
        
        # Send another text every hour, if playing the same game
        elif iter == 5 and current_steam_game is not None:
            send_text(current_steam_game, user_details)
            iter = 0

        # If the player is inactive for 5 iterations, assume they are done gaming
        elif iter > 5 and last_iter_steam_game is None:
            send_text(current_steam_game, user_details, False)
            sys.exit('Gamer is no longer online, goodbye.')

        #Iterate every 15 minutes
        time.sleep(900)
        last_iter_steam_game = current_steam_game
