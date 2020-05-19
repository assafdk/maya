#!/bin/bash

today=$(date '+%Y_%m_%d')
#bckup_dir="~/projects/maya/bckup/${today}/"
bckup_dir="${HOME}/tmp/${today}/"
now=$(date)
echo "Starting at ${now}"

echo "Creating bckup dir: ${bckup_dir}"
mkdir -p $bckup_dir
echo "Done"

echo "Backing up data..."
cp -R intraday/ $bckup_dir
#cp -R test/ $bckup_dir
echo "Done"

echo "Running intraday_updater..."
python3 intraday_updater.py
now=$(date)
echo "Done at ${now}"
echo "Bye man, keep being awesome!"