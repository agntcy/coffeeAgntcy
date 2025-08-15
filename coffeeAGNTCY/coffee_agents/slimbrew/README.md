
## Running the SLIM Server
docker run -it \
    -v ./slim-config.yaml:/config.yaml -p 46357:46357 \
    ghcr.io/agntcy/slim:latest /slim --config /config.yaml

## Create Shared Secret
export SLIM_SHARED_SECRET=$(python -c 'import secrets; print(secrets.token_urlsafe(48))')



## Unit Tests
Test Startup
[test 1]: Participants reply to session.destination_name
1. Moderator invites participants and sends one message. Expected results: Invited participants receive, Not invited participants do not receive
2. Participant replies with a message to session.destination_name. Expected results: it should go through without error (will fail for second participant)
3. Participant replies with a message to session.destination_name. Expected results: all participants should receive it
4. Participant replies with a message to session.destination_name: Expected results: participant should not receieve their own message (will fail)

[test 2]
1. Moderator invites participants and sends one message. Expected results: Invited participants receive, Not invited participants do not receive
2. Participant replies with a message to name of channel. Expected results: should go through without error 
3. Participant replies with a message to name of channel. Expected results: all participants should receive it
4. Participant replies with a message to name of channel. Expected results: participant should not receive their own message (will fail)

[test 3]
1. Moderator invites participants and sends one message. Expected results: Invited participants receive, Not invited participants do not receive
2. 

Permutations:
1 participant, 1 non-participant
2 participants, 1 non-participant
3 participant, 1 non-participant