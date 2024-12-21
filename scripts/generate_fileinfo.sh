#!/bin/sh

# Get the current working directory
here=$(pwd)

# Find all directories and iterate through them
find . -type d -print | while read dir; do
    # Change to the found directory
    cd "$dir"
    
    # Initialize/overwrite the file_info.txt file
    echo "File Checksum Size" > fileinfo.txt
    
    # Iterate over all .py and .mpy files
    for file in *.py *.mpy; do
        if [ -f "$file" ]; then
            # Calculate the checksum
            checksum=$(sha256sum "$file" | awk '{print $1}')
            # Get the file size
            filesize=$(stat -c%s "$file")
            # Write the checksum and size to fileinfo.txt
            echo "$file $checksum $filesize" >> fileinfo.txt
        fi
    done
    
    # Return to the original directory
    cd "$here"
done
