# IoT Server

Simple IoT Server, Configuration Tool & Dashboard

## Requirements

 - Python 3.9+
 - Git
 - Mosquitto
 - SQLite

## Installation

```bash
git clone git@github.com:hacklabza/iotserver.git
cd iotserver/

# Create a virtualenv or use pyenv
python3 -m venv ve
. ve/bin/activate

# Install the requirements
pip install -r requirments.txt

# Run the server to test your installation
./manage.py runserver
```

## Getting Started

To create a super user which you can use to populate your devices and users, execute the following command in your terminal and follow the prompts.

```bash
./manage.py createsuperuser
```
