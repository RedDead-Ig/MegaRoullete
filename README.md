# Roulette Bot (Telegram)

## Rodar local
- Crie um bot no BotFather
- Defina a env:
  - TELEGRAM_BOT_TOKEN=...

## Rodar com Docker
docker build -t roulette-bot .
docker run --rm -e TELEGRAM_BOT_TOKEN=... roulette-bot
