# Dailies

## Table of Contents

- [Standalone Setup](#standalone-setup)
	- [Pre-Requisites](#pre-requisites)
	- [Setup](#setup)
- [Docker Setup](#docker-setup)
	- [Pre-Requisites](#pre-requisites-1)
	- [Setup](#setup-1)

## Standalone Setup

This setup is perferred for development.

### Pre-Requisites

- [Git](https://git-scm.com/)
- [Python 3](python.org) (Tested with 3.8.4)

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
- [Docker Desktop](https://www.docker.com/get-started)

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