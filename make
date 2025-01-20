#!/bin/bash

# Check if mpy-cross exists
if [ ! -f "./bin/mpy-cross" ]; then
    echo "Error: Unable to locate mpy-cross. Make sure it exists in the './bin' directory."
    exit 1
fi

# Check if source directory exists
if [ ! -d "./src" ]; then
    echo "Error: Unable to locate source directory. Make sure 'src' exists in the './' directory."
    exit 2
fi

if [ -z "$(ls -A ./src/*.py 2>/dev/null)" ]; then
    echo "Error: No Python files found in the 'src' directory."
    exit 3
fi

# Create the build directory if it doesn't exist
mkdir -p ./build

# Check if build directory exists
if [ ! -d "./build" ]; then
    echo "Error: Unable to create build directory. Make sure you have permission to write to the './' directory."
    exit 4
fi

# Loop through each .py file in the current directory and compile it
for py_file in ./src/*.py; do
    # Get the base name of the file (without extension)
    base_name=$(basename "$py_file" .py)

    # Skip 'main.py' which is our entry point
    if [[ "$base_name" != "main" ]]; then
        # Compile the file to .mpy format and output it to ./build directory
        ./bin/mpy-cross -march=armv6m "$py_file" -o "./build/$base_name.mpy"

        if [[ $? -eq 0 ]]; then
            echo "Compiled $py_file to ./build/$base_name.mpy"
        else
            echo "Error compiling $py_file" >&2
           exit 5
        fi
    fi
done

# Copy the entry point
cp ./src/main.py ./build/

if [[ $? -ne 0 ]]; then
    echo "Error: Unable to copy the firmware entry point to the build directory."
    exit 6
fi

echo "Build process completed successfully. All files are in './build'."
