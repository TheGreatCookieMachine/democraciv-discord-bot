##  democraciv-discord-bot
 [![Discord](https://discordapp.com/api/guilds/208984105310879744/embed.png)](http://discord.gg/j7sZ3tD) ![Python Version](https://img.shields.io/badge/python-3.6%20%7C%203.7%20%7C%203.8-blue) [![Build Status](https://travis-ci.com/jonasbohmann/democraciv-discord-bot.svg?branch=master)](https://travis-ci.com/jonasbohmann/democraciv-discord-bot) [![Codacy Badge](https://api.codacy.com/project/badge/Grade/c6f2dc5d8f434756b5b0017845732715)](https://www.codacy.com/manual/jonasbohmann/democraciv-discord-bot?utm_source=github.com&amp;utm_medium=referral&amp;utm_content=jonasbohmann/democraciv-discord-bot&amp;utm_campaign=Badge_Grade)

General-purpose Discord Bot with unique features designed for the r/Democraciv Discord. 

Provides useful information, political party & role management and much more. 

##  Requirements

*  [Python](https://www.python.org/downloads//) 3.6 or newer
*  [discord.py](https://github.com/Rapptz/discord.py) 1.2.5 or newer
*  [PostgreSQL](https://www.postgresql.org/) 9.6 or newer 

**Run `pip install -r requirements.txt` to install all required dependencies.**

##  Installation

*As some features are implemented in a way to fit the very specific needs and use cases of the Democraciv Discord, it is not recommended 
to run the bot yourself as you might run into unexpected errors. Instead, invite the bot to your server with this
 [link](https://discordapp.com/oauth2/authorize?client_id=486971089222631455&scope=bot&permissions=8).*

After installing all the dependencies, create a `token.py` in the config folder.

The file should look like this:
```
# Token
ATOKEN = "NDg2OTcxMDg5MjIyNjMxNDU1.XL9_gw.JPB4ZFWnbfxIU6EsY1XT-iN-O3o"
TOKEN = "NDg3MzQ1OTAwMjM5MzIzMTQ3.D1CNEQ.l8G817yPN3wLdelMpvn88xSMR4M"
TWITCH_API_KEY = "r4lnx70cewwd1gbaeg1vur55w4o1uq"

# PostgreSQL config
POSTGRESQL_USER = "jonas"
POSTGRESQL_PASSWORD = "ehre"
POSTGRESQL_HOST = "127.0.0.1"
POSTGRESQL_DATABASE = "democraciv"
```
Add the token of your Discord App, your Twitch Helix API key if you enabled the Twitch module, and your
 PostgreSQL configuration like above. 

After you've done all that, run `client.py`.

####  Database

This bot needs a PostgreSQL database to run. To install and configure PostgreSQL, head [here](https://www.postgresql.org/).
 The bot was tested with PostgreSQL 9.6 and 12.1, everything else in between should work.


You only need to create an empty database, the bot will then fill that with tables on startup.


####  Twitch 

If you want to use the Twitch announcements feature, you have to get an API key from [here](https://dev.twitch.tv/console/apps)
and add it to the `token.py` in the config folder.

You can configure everything else that is Twitch related in the `config.py`.

If you do not want to use the Twitch announcements feature, you have to set `TWITCH_ENABLED` in the
`config.py` to `False`.

####  Reddit 

Notifications for new posts from a subreddit are enabled by default, but can be disabled in the `config.py`. Unlike the
Twitch Notification module, we don't need to register an API key for Reddit.

You can configure everything else that is Reddit related in the `config.py`.

If you do not want to use the Reddit announcements feature, you have to set `REDDIT_ENABLED` in the
`config.py` to `False`.


##  Features
*  Modular system for commands
*  Help command that automatically scales
*  Welcome messages & default roles
*  Announcements for live streams on twitch.tv/democraciv
*  Announcements for new posts from reddit.com/r/democraciv
*  Political party management
*  Self-assignable role management
*  Wikipedia queries
*  Event logging 


##  Modules
You can add and remove modules by adding or removing them from `initial_extensions` in `client.py`.

Module | Description 
------------ | ------------- |
module.links | Collection of useful links for the game (Wiki, Constitution, political parties etc.) |
module.about | Commands regarding the bot itself |
module.admin | Re-, un- and load modules and the config |
module.fun | `-whois`, `-veterans` and `-say` commands | 
module.help | Scaling `-help` command |
module.guild | Configure various functions of this bot for your guild |
module.roles | Add or remove roles from you |
module.parties | Join and leave political parties |
module.time | Get the current time in a number of different timezones |
module.legislature | Useful commands for Legislators on the Democraciv guild, such as `-submit` for submitting new bills |
module.wikipedia | Search for a topic on wikipedia |
module.random | Common choice commands (Heads or Tails etc.) |
event.logging | Logs events (member joins/leaves etc.) to a specified channel |
event.error_handler | Handles internal errors |
event.reddit | Handles notifications when there's a new post on r/democraciv |
event.twitch | Handles notifications when twitch.tv/democraciv is live |


##  Roadmap

####  Update 0.13.0 - The Performance & Stability Update ✅

*  ~~Refactor client.py~~
*  ~~Rewrite event modules~~
*  ~~Introduce custom exceptions~~
*  ~~Introduce utils to save time & code~~
*  ~~Replace blocking libraries (praw, wikipedia) with aiohttp API calls~~

####  Update 0.14.0 - The SQL Update

*  ~~Add a PostgreSQL database~~
*  ~~Migrate `guilds.json`, `parties.json` and `last_reddit_post.json` to new database~~
*  ~~Make roles case-insensitive~~
*  ~~Rewrite -addparty, -addrole, -deleteparty, -deleterole, -addalias, -deletealias to be safer and cover all needed values
for database~~
*  ~~Refactor asyncio.wait_for() tasks in guild.py~~
*  ~~Refactor help.py~~ (Update 0.14.2)


####  Update 0.15.0 - The Government Update

*  Add Legislature dashboard with session management
*  Add Ministry dashboard
*  Add webhook for notifications on new SC cases 
*  Rewrite the `time.py` module and allow converting between timezones


####  Update 0.16.0 - The Moderation Update

*  Add a Moderation module with `-kick`, `-ban` etc. commands
*  Add webhook for notifications on new Quire tasks

####  Update 0.17.0 - The Suggestions Update

*  Add suggestions from the community
*  **Refactor & Cleanup to prepare for 1.0.0 release**


##  Democraciv Discord Server
Join the [Democraciv Discord Server](https://discord.gg/AK7dYMG) to see the bot in action.

---

Contact @DerJonas#8109 on Discord if you have any questions left.
