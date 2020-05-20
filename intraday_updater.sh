#!/bin/bash
echo ""
today=$(date '+%Y_%m_%d')
bckup_dir="${HOME}/projects/maya/bckup/${today}/"
now=$(date)
echo "Starting at ${now}"
echo "----------------------------"
echo "Creating bckup dir: ${bckup_dir}"
mkdir -p $bckup_dir
echo "Done"

echo "Backing up data..."
cp -R intraday/ $bckup_dir
echo "Done"

echo "Running intraday_updater..."
/usr/local/bin/python3 intraday_updater.py
now=$(date)
echo "----------------------------"
echo "Done at ${now}"
echo "Bye man, keep being awesome!"
echo ""