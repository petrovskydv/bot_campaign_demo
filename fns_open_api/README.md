# Получение сведений о чеках ККМ с сервиса ФНС

Получение сведений о чеках ККМ с базы данных ФНС. Используется сервис `irkkt-mobile.nalog.ru:8888`.

## Как установить

Вам понадобится Python версии 3.8 или старше. Для установки пакетов рекомендуется создать виртуальное окружение. 

Установите пакеты:

```python3
pip install -r requirements.txt
```

Установите переменные окружения в `.env` файле:

` INN `         - ИНН юридического лица или предпринимателя, на который зарегистрирован личный кабинет на [сайте ИФНС](https://lkfl2.nalog.ru/lkfl/login).

` PASSWORD `    - Пароль от личного кабинета на [сайте ИФНС](https://lkfl2.nalog.ru/lkfl/login).

` CLIENT_SECRET` - Секретный ключ который задается согласно коду: `IyvrAbKt9h/8p6a7QPh8gpkXYQ4=` и отвечает за авторизацию приложения.


## Как запустить

Запустите скрипт:

```python3
python bill_check.py
```

Для запуска используйте следующие параметры:

`-t`    timestamp, время, когда вы осуществили покупку.

`-s`    сумма чека.

`-fn`   кодовый номер fss.

`-i`    номер чека.

`-fp`   параметр fiscalsign.

`-qr`   qr код строкой формата "t=20200727T1117&s=4850.00&fn=9287440300634471&i=13571&fp=3730902192&n=1", если заполнено, остальные параметры игнорируются, и их можно оставлять пустыми. 


## Результат работы

Результат работы выводится в консоль в виде структуры json:

```js
{
    "status": 2,
    "id": "608bc73c03f538ed90211d2b",
    "kind": "kkt",
    "createdAt": "2021-04-30T15:31:51+03:00",
    "statusDescription": {},
    "qr": "t=20210131T1721&s=4145.00&fn=9282440300702585&i=11686&fp=565643487&n=1",
    "operation": {
        "date": "2021-01-31T17:21",
        "type": 1,
        "sum": 414500
    },
    "process": [
        {
            "time": "2021-04-30T09:00:44+00:00",
            "result": 21
        },
        {
            "time": "2021-04-30T09:00:46+00:00",
            "result": 2
        }
    ],
    "query": {
        "operationType": 1,
        "sum": 414500,
        "documentId": 11686,
        "fsId": "9282440300702585",
        "fiscalSign": "565643487",
        "date": "2021-01-31T17:21"
    },
    "ticket": {
        "document": {
            "receipt": {
                "dateTime": 1612102860,
                "cashTotalSum": 0,
                "code": 3,
                "creditSum": 0,
                "ecashTotalSum": 0,
                "fiscalDocumentFormatVer": 2,
                "fiscalDocumentNumber": 11686,
                "fiscalDriveNumber": "9282440300702585",
                "fiscalSign": 565643487,
                "items": [
                    {
                        "name": "Хлебопечка\nBM Hyundai HYBM-M0313G",
                        "nds": 1,
                        "price": 414500,
                        "productType": 1,
                        "quantity": 1,
                        "sum": 414500
                    }
                ],
                "kktRegId": "0000603395032371",
                "nds18": 69083,
                "operationType": 1,
                "operator": "Продавец Мирошниченко Анна Александровна",
                "operatorInn": "236403546486",
                "prepaidSum": 414500,
                "provisionSum": 0,
                "requestNumber": 81,
                "shiftNumber": 121,
                "taxationType": 1,
                "appliedTaxationType": 1,
                "totalSum": 414500,
                "user": "ОБЩЕСТВО С ОГРАНИЧЕННОЙ ОТВЕТСТВЕННОСТЬЮ \"МВМ\"",
                "userInn": "7707548740"
            }
        }
    }, ...
```

## Цели проекта

Прототип получения информации по чекам ккм.
