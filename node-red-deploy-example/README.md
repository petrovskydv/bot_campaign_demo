# Запуск проекта бота в Node-RED

![](.assets/node-red-flow.png)

Чтобы запустить проект демо-бота в node-red и побаловаться, надо:

Создать своего бота у `@botfather`

В этой же директории, где лежит `docker-compose.yml` cоздать переменные окружения:

- `TG_TOKEN` - для работы телеграм бота
- `TG_BOT_NAME` - имя бота
- `OPEN_WEATHER_MAP_TOKEN` - для работы тестовой команды /weather, получить можно [тут.](https://openweathermap.org/)

Затем в консоли:
```
docker-compose up
```
Открыть в браузере [http://127.0.0.1:1880/](http://127.0.0.1:1880/)
Появится сообщение, что потоки остановлены из-за отсутствующих типов узлов.

Поставить модули (Главное меню -> Управление палитрой -> Установить):
  - `node-red-contrib-chatbot`
  - `node-red-contrib-image-tools`
  - `node-red-contrib-telegrambot`

**TODO: модули должны ставиться сами.**

Установить значения для ноды Telegram Receiver (Свойства -> Bot configuration) в:

- Bot name: `${TG_BOT_NAME}`
- Token: `${TG_TOKEN}`


Обновить страницу.

Нажать `Развернуть`.

В панели справа есть отладочные сообщения для дебага.

Готово!

- [Работа с очередью RQ](https://github.com/LevelUp-developers/bot_campaign_demo#%D1%80%D0%B0%D0%B1%D0%BE%D1%82%D0%B0-%D1%81-%D0%BF%D1%80%D0%BE%D1%82%D0%BE%D1%82%D0%B8%D0%BF%D0%BE%D0%BC-%D0%BE%D1%87%D0%B5%D1%80%D0%B5%D0%B4%D0%B8-%D0%B4%D0%BB%D1%8F-%D0%BE%D0%B1%D1%89%D0%B5%D0%BD%D0%B8%D1%8F-%D1%81-%D1%84%D0%BD%D1%81)

# Документация по Node-RED
- [Документация на оф. сайте](https://nodered.org/docs/)
- [Перевод оф. документации](http://wikihandbk.com/wiki/Node-RED:%D0%A1%D0%BE%D0%B4%D0%B5%D1%80%D0%B6%D0%B0%D0%BD%D0%B8%D0%B5)
- [Примеры](https://github.com/guidone/node-red-contrib-chatbot/wiki#examples)