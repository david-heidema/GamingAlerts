# About The Project
Notify your friends, significate other, etc when you start and stop playing Steam games. 

This project is Python script that runs locally on a gamers computer to text individuals your gaming status when start a new gaming session, launch a new game, and end your gaming session. 

# Requirements
To leverage this script you will need to know the phone number and mobile carrier of your recipient(s). The script expects for these values to be set within a configuration file "userConfig.yaml" at the root of the project. Below is an example of a possible configuration file. TODO

# Integrations
 - Discord API
 - GMAIL
 - Steam

# Setup
For each of the integrations above users must leverage an authenication method provided by these services. 

- Steam 
Provides the status of a Steam User, specifically leveraging the logon time, current game, and steam username via the ISteamUserStats API. To use the Steam API you must acquire an API associated to your account. See here for additional details on Steam Keys - https://steamcommunity.com/dev

- GMAIL
Provides access to the users email address for texting via the SMTP protocol. Setup requires the creation of an App Password, see here for additional details on App Passwords - https://support.google.com/accounts/answer/185833?hl=en  

- Discord 
Dynamically catures the Steam ID of the Discord user. This integration is optional as currently implemented, and provides minimal value until Discord modifies the scope of apps access to access activities. To enable Discord intregation, you must setup a Discord App, linked to your account. See here for more details on Discord Apps - https://discord.com/developers/docs/quick-start/overview-of-apps

Once you have secured the needed secrets from the intergation providers, you will need to create a .env file at the root of the project, which contains your relivant secrets with the exact naming as show below -- TODO 

# Roadmap
Version 1 only integrates with Steam and requires the creation of a Steam API Key.

Version 2 will integrate directly with the activities of discord to get the status of users. Therefore reducing overhead setup and increased functionality across all platform integrationed with the Discord account. 
