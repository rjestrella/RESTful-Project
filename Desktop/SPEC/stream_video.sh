#!/bin/bash

cd ~/mjpg-streamer/mjpg-streamer-experimental
./mjpg_streamer -o "output_http.so -w ./www" -i "input_raspicam.so -hf"
echo "Live Stream Enabled"
