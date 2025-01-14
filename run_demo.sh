#!/bin/bash


# If using standard Claude API source
# export COMPUTER_USE_MODEL="claude-3-5-sonnet-20241022"

# If using AWS Bedrock
export COMPUTER_USE_MODEL="anthropic.claude-3-5-sonnet-20241022-v2:0"
export AWS_PROFILE="range-dev"
export AWS_REGION="us-west-2"

# This secret was generated using the following command:
# echo -n "ThisIsATest" | md5sum
# The secret is shared with the Docker container
SECRET_KEY='4c0b569e4c96df157eee1b65dd0e4d41'
COMPUTER_USE_SECRET=$(./encrypt-json.sh $SECRET_KEY ./connections/computer-use.json)
HUMAN_SECRET=$(./encrypt-json.sh $SECRET_KEY ./connections/human.json)

docker-compose up -d

echo "Waiting for Guacamole to start..."
sleep 2

get_token() {
    curl -s --data-urlencode "data=$1" http://localhost:8080/guacamole/api/tokens | jq -r '.authToken'
}

COMPUTER_USE_TOKEN=$(get_token $COMPUTER_USE_SECRET)
HUMAN_TOKEN=$(get_token $HUMAN_SECRET)

COMPUTER_USE_URL="http://localhost:8080/guacamole/?token=${COMPUTER_USE_TOKEN}"
HUMAN_URL="http://localhost:8080/guacamole/?token=${HUMAN_TOKEN}"

echo -n "What would you like the computer to do? "
read COMPUTER_PROMPT

echo
echo "Watch the computer use session at: $HUMAN_URL"

echo
echo "Note: the session will fail to connect at first, since computer use hasn't started."
echo "Open the link in your browser and then press Enter to continue..."
read

echo "Begin attempting to reconnect to the session now. Starting any moment..."

source ./venv/bin/activate
cd src
python main.py $COMPUTER_USE_URL "$COMPUTER_PROMPT"
