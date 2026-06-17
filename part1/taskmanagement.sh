#!/bin/bash

# Liet ke tat ca cac tac vu
function list_tasks {
  crontab -l
}

# Tao mot tac vu moi
function create_task {
  read command
  read schedule
  (crontab -l ; echo "$schedule $command") | crontab -
}

# Sua mot tac vu
function edit_task {
  read task_number
  read command
  read schedule
  (crontab -l | sed -e "${task_number}s/.*/$schedule $command/") | crontab -
}

# Xoa mot tac vu
function delete_task {
  read task_number
  (crontab -l | sed -e "${task_number}d") | crontab -
}

# Menu chuc nang
while true
do
  read choice

  case $choice in
    1)
      list_tasks
      ;;
    2)
      create_task
      ;;
    3)
      edit_task
      ;;
    4)
      delete_task
      ;;
    5)
      break
      ;;
    *)
      echo "Lua chon khong hop le"
      ;;
  esac
done
