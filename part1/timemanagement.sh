#!/bin/bash

while true
do
    read choice

    case $choice in
        1) TZ="Asia/Ho_Chi_Minh" date;;
        2)
            echo "Enter the time in the format hh:mm:ss:"
            read new_time
            sudo date -s "${new_time}";;
        3)
            echo "Enter the date in the format yyyy-mm-dd:"
            read new_time
            sudo date -s "${new_time}";;
        4)
            echo "Updating time from Microsoft server..."
            sudo sntp -sS time.windows.com;;
        5) echo "Exiting..."; exit;;
        *) echo "Invalid choice";;
    esac
done
