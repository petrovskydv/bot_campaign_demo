# bot_campaign_demo

Это проект демо-бота для розыгрыша призов по чекам супермаркетов.

# Установка

Клонируйте репозиторий, и создайте виртуальное окружение. После этого установите зависимости:

```bash
$ pip install -r requirements.txt
```

## Переменные окружения

`SECRET_KEY` - Секретный ключ проекта.

`DEBUG` - Режим отладки. Установите 'False' для боевого режима.

`ALLOWED_HOSTS` - см [Django docs](https://docs.djangoproject.com/en/3.1/ref/settings/#allowed-hosts).

`DATABASE_URL` - Строка соединения с базой данных: "postgres://user:password@127.0.0.1:5432/database".

`ROLLBAR_TOKEN` - Токен для Rollbar сервиса.


## Установка базы данных

Для установки Postgres сервиса, требуется Docker.

Создайте новый docker контейнер:

```bash
$ docker-compose up
```

Проверьте что Docker создан и выполняется:

```bash
$ docker ps
```

## Создание и запуск проекта

Создание базы данных:

```bash
$ python manage.py migrate
```

Запуск сервера локально:

```bash
$ python manage.py runserver
```


Удачного кодинга!