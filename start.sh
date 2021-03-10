#!/bin/bash

# Starting the server 
sudo python3 -m waitress --call --port=7000 'app:create_app'