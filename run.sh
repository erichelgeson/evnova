#!/bin/bash
set -x
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
echo
echo "You should use DecoderRing instead of this script https://macintoshgarden.org/games/decoder-ring
echo
echo "Renewed: $RENEW_NUMBER"
echo "Date: $(date)"
echo
echo "https://macintoshgarden.org/games/escape-velocity-nova"
echo
echo "aswreg_v2.py is from https://www.reddit.com/r/evnova/comments/g3ie3x/ambrosia_and_registration/"
python aswreg_v2.py

git config --global user.email "actions@github.com"
git config --global user.name "github"
git add README.txt
git commit -am "$(date)"
git push -f
