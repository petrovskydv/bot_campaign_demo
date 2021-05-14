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

`RECOGNITION_QUALITY` - Строка регулирующая качество и скорость распознавания qr-кодов. Возможно три варианта значений: `Best Coverage Settings`, `Best Speed Settings`, `Balance Settings`.

`BARCODE_FORMAT` - Определяет тип распознаваемых кодов на чеках. Варианты заполнения могут быть следующие: `All`, `OneD`, `QR Code`, `Code 39`, `Code 128`, `Code 93`, `Codabar`, `Interleaved 2 of 5`, `Industrial 2 of 5`, `EAN-13`, `EAN-8`, `UPC-A`, `UPC-E`, `PDF417`, `DATAMATRIX`, `AZTEC`, `Code 39 Extended`, `Maxicode`, `GS1 Databar`, `PatchCode`, `GS1 Composite`, `Postal  Code`, `DotCode`.


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

В качестве сервиса для распознавания qr-кодов [dynamsoft.com](https://www.dynamsoft.com). Что бы сервис успешно заработал, кроме регистрации и получения лицензионного ключа, необходимы два json файла с настройками: `qrcode_settings.json`, `barcode_format.json`. Нужные файлы находятся в папке `qr_codes_recognition` проекта. Их необходимо положить в каталог определенный `STATIC_ROOT` в настройках проекта.
Запуск распознавания, необработанных чеков осуществляется менеджмент командой:

```bash
$ python manage.py read_barcodes
```

Для тестирования возможен запуск в режиме обработки единичного изображения чека из командной строки:

```bash
$ python manage.py read_barcodes --img "/Users/.../media/receipts/20210430_123506_7RWLprV.jpg"
```

В результате в консоли будет выведена информация зашифрованная в qr-коде на чеке или пустая строка при неудачном распознавании.


# Работа с прототипом очереди для общения с ФНС

Запустить сервис Redis:
```
docker run --name jango-rq-queue -d -p 6379:6379 --restart always redis
```
Проверить, что контейнер запустился:
```
docker ps
```
Тест работы с очередью (на указанный `telegram_chat_id` прилетит ответ от налоговой):
```
python manage.py qr_to_queue <telegram_chat_id> <qr>
Пример: 
```
Мониторинг очереди:
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
