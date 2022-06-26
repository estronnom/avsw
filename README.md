# Тестовое задание для AVSOFT

Выполнил Чибисов Михаил

### Взаимодействие через бота

Бот доступен по ссылке https://t.me/avsoft_collectivism_bot

Бот принимает как текстовые файлы, так и URL

Для выгрузки обработанных файлов используйте команду `/dump`

### Запуск локально

Для запуска необходимо получить токен для телеграм бота и поместить его в
файл .env

`git clone https://github.com/estronnom/avsw.git`

`cd avsw && sudo mkdir raw_files && sudo mkdir processed_files`

`docker-compose up --build -d`