# LK HR Assistant

Telegram-бот для HR-отдела LK Bauservice GmbH.

## Структура проекта

- `bot/` — логика Telegram-бота и базы знаний
- `server/` — FastAPI-сервер и webhook
- `data/` — база знаний в JSON
- `config/` — настройки окружения и примеры конфигурации

## Установка

1. Создайте виртуальное окружение:
   ```bash
   python -m venv .venv
   .venv\Scripts\activate
   ```
2. Установите зависимости:
   ```bash
   pip install -r requirements.txt
   ```
3. Скопируйте `config/.env.example` в `.env` и заполните параметры.

## Запуск

1. Запустите сервер FastAPI:
   ```bash
   uvicorn server.main:app --host 0.0.0.0 --port 8000
   ```
2. Настройте `WEBHOOK_URL` в Telegram через BotFather или напрямую.

## Команды бота

- `/start` — начать работу с ассистентом
- `/help` — подсказки по использованию
- `/topics` — список тем базы знаний

## База знаний

Файл `data/knowledge_base.json` содержит темы, шаблоны вопросов и ответы. Добавляйте новые темы и вопросы через этот файл.

## Структура ответа

- краткий профессиональный ответ
- чек-лист действий
- предупреждение, если требуется проверка у руководителя, юриста или Steuerberater

## Export / Import KB (API)

- Export current KB JSON:

```bash
curl -s http://localhost:8000/kb/export | jq '.'
```

- Import KB JSON (replace):

```bash
curl -X POST http://localhost:8000/kb/import -H "Content-Type: application/json" --data-binary @knowledge_base.json
```

## Docker

Build and run with Docker:

```bash
docker build -t lk-hr-assistant .
docker run -e TELEGRAM_BOT_TOKEN=your_token -e WEBHOOK_URL=your_webhook -e ADMIN_API_KEY=your_admin_key -p 8000:8000 lk-hr-assistant
```

## Security notes

- `ADMIN_API_KEY` protects admin forms and admin APIs for editing and import/export.
- Admin pages `/admin` and `/admin/topic/*` now require the API key to view.
- `WEBHOOK_SECRET` can be set to require Telegram webhook requests to include `X-Telegram-Bot-Api-Secret-Token`.
- If `WEBHOOK_SECRET` is not set, keep `WEBHOOK_URL` secret and use HTTPS.

## Tests

Run unit tests with `pytest`:

```bash
pytest -q
```
