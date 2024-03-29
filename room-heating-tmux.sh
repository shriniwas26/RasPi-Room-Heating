#!/bin/bash

SESSIONNAME="workspace"
PROJECT_FOLDER="/home/pi/RasPi-Room-Heating"

tmux has-session -t $SESSIONNAME &> /dev/null
HAS_SESSION=$?

if [[ ${HAS_SESSION} != 0 ]]
    then
        # new session with name $SESSIONNAME and window 0 named "base"
        tmux new-session -s ${SESSIONNAME} -n "Logs" -d
        tmux send-keys "tail -n 100 -f ${PROJECT_FOLDER}/logs/update_offset.log" 'C-m'

        tmux splitw -v -p 50 # split it into two halves

        tmux send-keys "tail -n 100 -f ${PROJECT_FOLDER}/logs/room_weather.log" 'C-m'

        tmux splitw -h -p 50 # split it into two halves
fi

tmux attach -t ${SESSIONNAME}
