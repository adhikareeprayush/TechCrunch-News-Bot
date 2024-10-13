# TechCrunch News Bot

This FastAPI application fetches news from TechCrunch RSS feed and sends it to a specified Telegram chat.

## Features

- Fetches news from TechCrunch RSS feed
- Filters news based on specified categories
- Sends news links to a Telegram chat
- Runs as a background task in a FastAPI application

## Setup

1. Clone this repository
2. Install dependencies: `pip install -r requirements.txt`
3. Set environment variables:
   - `BOT_TOKEN`: Your Telegram bot token
   - `CHAT_ID`: Your Telegram chat ID
4. Run the application: `uvicorn main:app --host 0.0.0.0 --port 8000`

## Endpoints

- `/`: Root endpoint, returns a status message
- `/start`: Starts the bot as a background task

## Deployment

This application is designed to be deployed on Render. Make sure to set the environment variables in your Render dashboard.