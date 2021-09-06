<p align="center">
  <img width="200" height="200" src="https://i.imgur.com/ZNVzm1O.png">
  <h1 align="center">Dailies - Streak/Milestone Tracker</h1>
</p>
<p align="center">
  Dailies is a Discord bot that tracks messages in a single channel intended for streak 'posts': individual messages regarding some form of progress update. More information below.
</p>
<br>
<br>
<br>

## Table of Contents
- [About](#about)
- [Standalone Setup](#standalone-setup)
	- [Pre-Requisites](#pre-requisites)
	- [Setup](#setup)
- [Docker Setup](#docker-setup)
	- [Pre-Requisites](#pre-requisites-1)
	- [Setup](#setup-1)
- [Credits](#credits)

## About

Given the `DAILY_CHANNEL_ID`, Dailies will monitor this channel for any message sent by a user. Once a user sends a message, their streak is incremented for that day and any further messages will be ignored.

Every three day milestone gives a user one mercy day up to 30. Mercy days allow a user to miss a streak day without losing their streak.

Users can enable `!Casual` mode which instead allows them to post progress whenever they want without worrying about losing their streak. They do not gain mercy days and their streaks instead operate on a weekly and monthly basis, resetting at the end of the month and being shown every week.

At the rollover of each streak day (which occurs at 00:00:00 UTC), Dailies will post the list of milestones that users reached over the past 24hrs and the casual streaks if it is the beginning of a new week.

![Demonstration Image](https://i.imgur.com/oz5IEsy.png)



## Standalone Setup

This setup is perferred for development.

### Pre-Requisites

- [Git](https://git-scm.com/)
- [Python 3](https://python.org) (Tested with 3.8.4)

### Setup

1. Run the following commands:

```bash
git clone https://github.com/Gmanicus/Dailies.git
cd Dailies

# Create a new virtual environment. The environment will be in the "env" folder
python -m venv env

# For Windows (NOTE: doesn't work with Powershell)
env\Scripts\activate.bat
# For Unix-based machines (ex. Mac OS/Linux)
source env/bin/activate

# Install requirements inside our new virtual environment
pip install -r requirements.txt
```

2. Make a copy of `example.env` file and rename it to `.env`. Then, edit your new `.env` file and fill out the fields. This includes:

	- Discord bot token
	- Channel and Role IDs
	- API host address

3. Finally, run the script.

```bash
python dailies.py
```

## Docker Setup

This setup is perferred for server deployment.

### Pre-Requisites

- [Git](https://git-scm.com/)
- [Docker](https://www.docker.com/get-started)

### Setup

1. Clone the git repository.

```bash
git clone https://github.com/Gmanicus/Dailies.git
```

2. Make a copy of `example.env` file and rename it to `.env`. Then, edit your new `.env` file and fill out the fields. This includes:

	- Discord bot token
	- Channel and Role IDs
	- API host address

3. Run the bot with the command:

```bash
docker-compose up
```

## Credits

Thanks to [Some1chan](https://github.com/some1chan) and [FrozenAlex](https://github.com/FrozenAlex) for building the Docker and Environment setup. Dailies went through a lot of maintenance, and Some1chan spent many hours deploying and administrating it for me on the GDU server. If you're into Game Development by the way, [feel free to stop by](https://discord.gg/BadGvS4PV9).
