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

`DYNAM_LICENSE_KEY` - Уникальный ключ для доступа к сервису распознавания qr-кодов. Можно получить после регистрации на сайте [dynamsoft.com](https://www.dynamsoft.com).

`BARCODE_FORMAT` - Определяет тип распознаваемых кодов на чеках. Варианты заполнения могут быть следующие: `All`, `OneD`, `QR Code`, `Code 39`, `Code 128`, `Code 93`, `Codabar`, `Interleaved 2 of 5`, `Industrial 2 of 5`, `EAN-13`, `EAN-8`, `UPC-A`, `UPC-E`, `PDF417`, `DATAMATRIX`, `AZTEC`, `Code 39 Extended`, `Maxicode`, `GS1 Databar`, `PatchCode`, `GS1 Composite`, `Postal  Code`, `DotCode`. Используется только для прототипа кода с целью отладки, затем будет убрано.

`TG_TOKEN` - Токен телеграмм бота привязанного к Node-RED.

`TG_BOT_NAME` - Имя телеграмм бота привязанного к Node-RED.


## Установка Postgres, Redis и Node-RED

Для установки сервисов требуется Docker.

```bash
$ docker-compose up
```

## Настройка Node-RED

Открыть в браузере [Node-RED](http://127.0.0.1:1880/).

Поставить модули (Главное меню -> Управление палитрой -> Установить):
  - `node-red-contrib-chatbot`
  - `node-red-contrib-image-tools`
  - `node-red-contrib-telegrambot`
  - `node-red-node-base64`

Развернуть файл проекта, меню Node-RED -> Импорт -> Указываем файл `flows.json` из каталога `node-red-api` проекта.

Установить в свойствах ноды Telegram Receiver и Telegram Sender конфигурацию заранее зарегистрированного бота для работы с Node-RED. Эти параметры указаны в файле виртуального окружения.

В ноде `HOST` указать адрес хоста. (TODO: перенести настройку в переменные окружения.)

Для запуска конфигурации Node-RED нажимаем Развернуть. 

## Создание и запуск проекта

Создание базы данных:

```bash
$ python manage.py migrate
```
Наполнение базы тестовыми данными:

```bash
$ python manage.py loaddata fixtures
```

Запуск сервера локально:

```bash
$ python manage.py runserver
```

Удачного кодинга!


# Запуск обмена с базой данных ФНС

Обмен осуществляется в автоматическом режиме при условии наличия необработанных чеков в базе данных. При их отсутствии, обработка ожидает в режиме бесконечного цикла.

```bash
$ python manage.py swap_with_fns
```

Для тестирования возможен запуск в режиме обработки единичного qr-кода из командной строки:

```bash
$ python manage.py swap_with_fns --qr "t=20200727T1117&s=4850.00&fn=9287440300634471&i=13571&fp=3730902192&n=1"
```
В результате в консоли будет выведена информация о чеке, полученная с сайта ФНС в формате json.


# Запуск распознавания qr-кодов на изображениях чеков

В качестве сервиса для распознавания qr-кодов [dynamsoft.com](https://www.dynamsoft.com). Что бы сервис успешно заработал, кроме регистрации и получения лицензионного ключа, необходимы два json файла с настройками: `qrcode_settings.json`, `barcode_format.json`. Нужные файлы находятся в папке `qr_codes_recognition` проекта. Их необходимо положить в каталог `qr_codes_recognition` проекта.
Запуск распознавания, необработанных чеков осуществляется менеджмент командой:

```bash
$ python manage.py read_barcodes
```

Для тестирования возможен запуск в режиме обработки единичного изображения чека из командной строки:

```bash
$ python manage.py read_barcodes --img "/Users/.../media/receipts/20210430_123506_7RWLprV.jpg"
```

В результате в консоли будет выведена информация зашифрованная в qr-коде на чеке или пустая строка при неудачном распознавании.
Пример распознанной строки:
```
t=20200727T1117&s=4850.00&fn=9287440300634471&i=13571&fp=3730902192&n=1
```


# Работа с прототипом очереди для общения с ФНС

Запустить сервис Redis:
```
docker run --name django-rq-queue -d -p 6379:6379 --restart always redis
```
Проверить, что контейнер запустился:
```
docker ps
```
Запустить воркер:
```
python manage.py rqworker
```
Тест работы с очередью (на указанный `telegram_chat_id` прилетит ответ от налоговой):
```
python manage.py qr_to_queue <telegram_chat_id> <qr>
```
Пример:
```
python manage.py qr_to_queue 12345 "t=20200727T1117&s=4850.00&fn=9287440300634471&i=13571&fp=3730902192&n=1"
```
## Мониторинг очереди
В консоли:
```
python manage.py rqstats --interval=1
```
```
Django RQ CLI Dashboard

------------------------------------------------------------------------------
| Name           |    Queued |    Active |  Deferred |  Finished |   Workers |
------------------------------------------------------------------------------
| default        |         0 |         0 |         0 |         0 |         1 |
------------------------------------------------------------------------------
```
RQ dashboard (легкий веб-интерфейс мониторинга на Flask)
```
rq-dashboard
```

![](https://python-rq.org/img/dashboard.png)

# Деплой на сервер

1. Клонировать репозиторий в `/opt/bot_campaign_demo/`
2. Создать виртуальное окружение:
```
python3 -m venv env
```
3. Установить зависимости:
```
pip install -r requirements.txt
```
4. Запустить docker-compose:
```
docker-compose up
```
5. Постаить [Nginx Unit](https://unit.nginx.org/installation/)
6. Настроить `Nginx Unit`, для Ubuntu (для других ОС инструкция на [оф. сайте](https://unit.nginx.org/installation/)):
```bash
sudo curl -X PUT --data-binary @unit.config --unix-socket /var/run/control.unit.sock http://localhost/config/
```
7. Скопировать `django-rqworker.service` в `/etc/systemd/system/`, затем:
```bash
systemctl start django-rqworker.service
systemctl enable django-rqworker.service
```
Убедиться, что сервис работает:
```bash
systemctl status django-rqworker.service
```
8. Готово!
