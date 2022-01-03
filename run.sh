#!/bin/bash
# set -x
source venv/bin/activate
pip install -r requirements.txt > /dev/null

NUMBER=6RHG-NTFP-M889
NAME="Special [K]"
GAME="EV Nova"
COPIES=200
DATE="November 9th, 2007" # Estimate

echo "Original:"
echo "Name: $NAME"
echo "Copies: $COPIES"
echo "Number: $NUMBER"
echo "Date: $DATE"

RENEW_NUMBER=$(python aswreg_v2.py renew $NUMBER "$NAME" $COPIES "$GAME")
echo
echo "Renewed: $RENEW_NUMBER"
echo "Date: $(date)"
echo
echo "https://macintoshgarden.org/games/escape-velocity-nova"
echo
python aswreg_v2.py
