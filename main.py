import requests
from datetime import datetime, timedelta
import json


url = 'http://construction.irkutskoil.ru/'
class_line = '811d766b-0783-ec11-911c-005056b6948b' # класс уровня линии
class_material = 'b09d6dc1-4256-ec11-911a-005056b6948b' # класс уровня материала
plan_atr = 'b495b7d5-8da5-ec11-9122-005056b6948b'
status_atr = 'e5668064-b4ac-eb11-9115-005056b6948b'
admin_node_id = '6709b168-41af-ec11-9124-005056b6948b'
MT_list_atr = 'ee1ffb4d-41af-ec11-9124-005056b6948b'

def authentification(url, aut_string):  # функция возвращает токен для атуентификации. Учетные данные берет из файла
    req_url = url + 'connect/token'
    payload = aut_string  # строка вида grant_type=password&username=????&password=??????&client_id=??????&client_secret=??????
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded'
    }
    response = requests.post(req_url, data=payload, headers=headers)
    if response.status_code == 200:
        token = json.loads(response.text)['access_token']
    else:
        token = ''
    return token


def find_line(url, token, attribute_id, filter_list, mod_date):  # возвращает ответ поискового запроса целиком
    req_url = url + 'api/objects/search?take=30000'
    payload = json.dumps({
        "Filters": filter_list,

        "Conditions": [  # условия для поиска в Неосинтез
            {
                "Type": 1,  # тип условия 1 - по атрибуту
                "Attribute": attribute_id,  # id атрибута в Неосинтез
                "Operator": 7,  # оператор сравнения. 7 - существует
                "Direction": 0,
                "Logic": 0
            },
            {
                "Type": 10,  # тип условия дата модификации
                "Operator": 3,  # оператор сравнения. 3 - больше
                "Direction": 0,
                "Logic": 2,
                "Value": mod_date
            }
        ]
    })
    headers = {
        'Accept': 'application/json',
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json-patch+json',
        'X-HTTP-Method-Override': 'GET'
    }
    response = requests.post(req_url, headers=headers, data=payload)  # поисковый запрос с десериализацией ответа
    return response


def find_item(url, token, folder_id, date_value):  # возвращает ответ поискового запроса целиком
    req_url = url + 'api/objects/search?take=30000'
    payload = json.dumps({
        "Filters": [
            {
                "Type": 4,
                "Value": folder_id  # id узла поиска в Неосинтез
            }
        ],
        "Conditions": [  # условия для поиска в Неосинтез
            {
                "Type": 1,  # тип условия 1 - по атрибуту
                "Attribute": plan_atr,  # id атрибута в Неосинтез
                "Operator": 2,  # оператор сравнения. 7 - существует
                "Value": date_value,
                "Group": 1,
                "Direction": 0,
                "Logic": 0
            },
            {
                "Type": 1,  # тип условия 1 - по атрибуту
                "Attribute": plan_atr,  # id атрибута в Неосинтез
                "Operator": 8,  # оператор сравнения. 7 - существует
                "Group": 1,
                "Direction": 0,
                "Logic": 1
            },
            {
                "Type": 1,  # тип условия 1 - по атрибуту
                "Attribute": status_atr,  # id атрибута в Неосинтез
                "Operator": 8,  # оператор сравнения. 7 - существует
                "Direction": 1,
                "Logic": 2
            }
        ]
    })
    headers = {
        'Accept': 'application/json',
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json-patch+json',
        'X-HTTP-Method-Override': 'GET'
    }
    response = requests.post(req_url, headers=headers, data=payload)  # поисковый запрос с десериализацией ответа
    return response


def put_attributes(url, token, neosintez_id, date_value):  # функция обновляет атрибуты объекта в неосинтез и возвращает весь ответ
    req_url = url + f'api/objects/{neosintez_id}/attributes'  # id сущности, в которой меняем атрибут
    payload = json.dumps([{
        "Name": 'forvalidation',
        'Type': 3,
        'Id': plan_atr,
        'Value': date_value
    }])  # тело запроса в виде списка/словаря

    headers = {
        'Accept': 'application/json',
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json-patch+json'
    }
    response = requests.put(req_url, headers=headers, data=payload)
    if response.status_code != 200:
        # print(req_body)
        # print(response.text)
        pass
    return response


def update_plan_date():
    resp_line = json.loads(find_line(url, token, plan_atr, filter_list, mod_date).text)


    if resp_line['Total'] != 0:  #  проверка, что запрос вернул непустой ответ, т.е линии по условию найдены
        line_list = resp_line['Result']
        for line in line_list:
            line_id = line["Object"]['Id']
            date_value = line['Object']['Attributes'][plan_atr]['Value']
            #print(line_id, date_value)
            resp_item = json.loads(find_item(url, token, line_id, date_value).text)

            if resp_item['Total'] != 0:
                item_list = resp_item['Result']
                for item in item_list:
                    item_id = item["Object"]['Id']
                    resp_put = put_attributes(url, token, item_id, date_value)
                    #print(item_id, resp_put.status_code)
    else:
        #print('Нет результатов')
        pass


def get_configuration(*, url, token, node_id, atribute_id):
    req_url = url + f'api/objects/{node_id}'
    headers = {
        'Accept': 'application/json',
        'Authorization': f'Bearer {token}'
    }
    response = requests.get(req_url, headers=headers)
    response = json.loads(response.text)
    mt_list = response['Attributes'][atribute_id]['Value'].split(';')
    return mt_list




# прочитать файл с данными для аутентификации
with open('auth_data.txt') as f:
    aut_string = f.read()

#  получить токен аутантификации
token = authentification(url=url, aut_string=aut_string)
if not token:
    print('Ошибка аутентификации')

#  получить список МТ для поиска в первый запуск
mt_list = get_configuration(url=url, token=token, node_id=admin_node_id, atribute_id=MT_list_atr)
filter_list = [{'Type': 4, 'Value': id} for id in mt_list]

# начальная дата модификации
mod_date = datetime.now() - timedelta(seconds=5)  #  дата больше которой ищутся линии в момент запуска скрипта
mod_date = mod_date.strftime("%Y-%m-%dT%H:%M:%S")
print(mod_date)



# бесконечный цикл проверки изменений даты план
while True:
    try:
        update_plan_date()
        pass
    except Exception as err:  # в случае ошибки писать ее в файл в папке лог в корне скрипта
        with open(f'log/exception_{datetime.now().strftime("%Y-%m-%dT%H:%M:%S")}.txt', 'wr') as f:
            f.write(str(err))
    mod_date = datetime.now()
    mod_date = mod_date.strftime("%Y-%m-%dT%H:%M:%S") # дата модификации для запроса линий с датой модификации больше
    #  получить список МТ для поиска каждый раз проверять переменную конфига
    mt_list = get_configuration(url=url, token=token, node_id=admin_node_id, atribute_id=MT_list_atr)
    filter_list = [{'Type': 4, 'Value': id} for id in mt_list]
