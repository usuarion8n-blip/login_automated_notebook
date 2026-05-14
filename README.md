# Login Automated Notebook API

This is a Python Flask API that executes the `npx notebooklm-sdk login` command when a POST request is made to `/login`.

## Installation

1. Install dependencies: `pip install -r requirements.txt`

## Running

Run the app: `python app.py`

The API will be available at http://localhost:5000

## Usage

Send a POST request to `/login` to execute the login command.

Note: The command may require interactive input or browser access, so it might not work in all environments.