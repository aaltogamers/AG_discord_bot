# Aalto Gamers Discord Bot

The Discord bot for the Aalto Gamers discord server. Bot is also known as Alvar Aalto

## Dependencies:

- Python 3.8+
- Python pip (pip3)
- discord.py (Installable via pip)
- pyyaml (Installable via pip)
- requests (Installable via pip)

## .env File

Copy .env-example, rename it .env and add Bot Token

```
DISCORD_TOKEN=Discord Bot Token
DEVELOPMENT=If has any value, uses dev server id values instead of real server ones
```

## Deployment

The deployment credentials are in github secrets and on push should automatically deploy a new version to azure 
If you want to test the bot in dev mode, change the actions to use `DISCORD_TOKEN_DEV`, set `development=1` in `environment-variables`-section of the action and change the `name` variable. But remember to take down the new container instance in azure after testing
