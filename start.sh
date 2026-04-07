#!/bin/bash
echo "🚲 Starting BikeGuard..."
cd ~/environment/bike-guard
source venv/bin/activate

# Kill any existing processes
pkill -f "sensors/" 2>/dev/null
pkill -f "fog_node" 2>/dev/null
pkill -f "server.py" 2>/dev/null
sleep 2

# Start all sensors
nohup venv/bin/python sensors/vibration_sensor.py > /dev/null 2>&1 &
nohup venv/bin/python sensors/gps_sensor.py > /dev/null 2>&1 &
nohup venv/bin/python sensors/tilt_sensor.py > /dev/null 2>&1 &
nohup venv/bin/python sensors/sound_sensor.py > /dev/null 2>&1 &
nohup venv/bin/python sensors/battery_sensor.py > /dev/null 2>&1 &
echo "✅ All 5 sensors started!"

# Start fog node
nohup venv/bin/python fog/fog_node.py > /tmp/fog.log 2>&1 &
echo "✅ Fog node started!"

# Start dashboard server
#echo "✅ Starting dashboard server..."
#echo "🌐 Open: https://6e8e3c0e3b1b4aad8ab458d59d502dd7.vfs.cloud9.us-east-1.amazonaws.com:8082"
#python3 server.py