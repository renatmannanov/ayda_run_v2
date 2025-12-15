#!/bin/bash

# Start both the bot and the API server concurrently
python main.py &
python api_server.py
