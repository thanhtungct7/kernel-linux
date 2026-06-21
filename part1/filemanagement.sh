
# Function to get user input
get_input() {
    read choice
}

# Loop to display the menu and get user input
while true
do
    get_input

    case $choice in
        1) command="list" ;;
        2) command="create-file" ;;
        3) command="remove-file" ;;
        4) command="show-file" ;;
        5) command="edit-file" ;;
        6) command="rename-file" ;;
        7) command="copy-file" ;;
        8) command="read-file" ;;
        9) command="save-file" ;;
        0) exit ;;
        *) echo "Invalid choice" ;;
    esac

    # Execute the command based on user choice
    if [ -n "$command" ]
    then
        if [ "$command" = "list" ]
        then
            ls -la
        else
            read filename

            if [ -z "$filename" ]
            then
                echo "Missing file name"
            else
                case "$command" in
                    "create-file")
                        if [ -e "$filename" ]; then
                            echo "File '$filename' đã tồn tại"
                        else
                            touch "$filename"
                            echo "Đã tạo file '$filename'"
                        fi
                        ;;
                    "remove-file") rm -rf "$filename" ;;
                    "show-file") less "$filename" ;;
                    "rename-file")
                        read new_filename
                        if [ -z "$new_filename" ]
                        then
                            echo "Missing new file name"
                        else
                            if mv "$filename" "$new_filename"; then
                                echo "Đã đổi tên '$filename' → '$new_filename'"
                            else
                                echo "Lỗi: không thể đổi tên '$filename'"
                            fi
                        fi
                        ;;
                    "copy-file")
                        read destination_filename
                        if [ -z "$destination_filename" ]
                        then
                            echo "Missing destination file name"
                        else
                            if cp "$filename" "$destination_filename"; then
                                echo "Đã sao chép '$filename' → '$destination_filename'"
                            else
                                echo "Lỗi: không thể sao chép '$filename'"
                            fi
                        fi
                        ;;
                    "read-file")
                        cat "$filename"
                        ;;
                    "save-file")
                        read dest_filename
                        if [ -z "$dest_filename" ]; then
                            echo "Missing destination file name"
                        else
                            if mv "$filename" "$dest_filename"; then
                                echo "Đã lưu: '$dest_filename'"
                            else
                                echo "Lỗi: không thể lưu '$dest_filename'"
                            fi
                        fi
                        ;;
                esac
            fi
            command=""
        fi
    fi
done
