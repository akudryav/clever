#! /usr/bin/env python
# -*- coding: utf-8 -*-
# Set up modules from 
# pip install cleverapi --upgrade
# pip install yandex-search
# pip install --upgrade google-api-python-client
from cleverapi import CleverApi, CleverLongPoll
from yandex_search import Yandex
from googleapiclient.discovery import build
import json
import apis
# вопросительные слова для выкидывания из начала вопроса при поиске вместе с ответами
qwords = ["Что", "Где", "Когда", "Кто", "Почему", "Зачем", "Как", "Кем", "Какой"]
api = CleverApi(apis.CLEVER)
lp = CleverLongPoll(api)

yandex = Yandex(api_user=apis.YANDEX_LOGIN, api_key=apis.YANDEX_KEY)
google = build("customsearch", "v1", developerKey=apis.GOOGLE_KEY, cache_discovery=False)
# получение результатов поиска яндекс
def yandex_grep(pattern):
    results = yandex.search(pattern)
    return [x['snippet'] for x in results.items]
# получение результатов поиска гугл
def google_grep(pattern):
    res = google.cse().list(q=pattern, cx=apis.GOOGLE_ID).execute()
    return [x['snippet'] for x in res['items']]
# подсчет числа ответов в выдаче (снипетах)
def count_answers(answers, snippets):
    res = [0, 0, 0]
    for ans in answers:
        for snip in snippets:
            if ans['text'].lower() in snip.lower():
                res[ans['id']] += 1
    return res

# выбор ответа с максимальным числом результатов в поиске совместно с вопросом 
def count_found_yandex(answers, question):
    found_y = 0
    for ans in answers:
        pattern = ans['text']+' '+question
        result_y = yandex.search(pattern)
        if int(result_y.found["strict"]) > found_y:
            maxid_y = ans['id']
            found_y = int(result_y.found["strict"])
    return str(maxid_y + 1)

def count_found_google(answers, question):
    found_g = 0
    for ans in answers:
        pattern = ans['text']+' '+question
        result_g = google.cse().list(q=pattern, cx=apis.GOOGLE_ID).execute()
        if int(result_g["queries"]["request"][0]["totalResults"]) > found_g:
            maxid_g = ans['id']
            found_g = int(result_g["queries"]["request"][0]["totalResults"])
    return str(maxid_g + 1)

@lp.question_handler()
def new_question(event):
    print(event["question"]["text"])
    print(event["question"]["answers"])
    yandex_items = yandex_grep(event["question"]["text"])
    google_items = google_grep(event["question"]["text"])
    yandex_count = count_answers(event["question"]["answers"], yandex_items)
    google_count = count_answers(event["question"]["answers"], google_items)
    total_count = [x + y for x, y in zip(yandex_count, google_count)]
    #(если обычный подсчет не помог)
    if total_count == [0, 0, 0]:
        # убираем из вопроса первое вопросительное слово
        first, _, rest = event["question"]["text"].partition(" ")
        if first in qwords:
            phrase = rest.replace('?','')
        else:
            phrase = event["question"]["text"].replace('?','')
        # сразу печатаем ответ а потом ищем в гугле чтоб успеть за 10 сек)
        print("Яндекс "+count_found_yandex(event["question"]["answers"], phrase))
        print("Google "+count_found_google(event["question"]["answers"], phrase))
    else:
        print(total_count)
       

def main():
    #event = json.loads('{     "type":"sq_question",   "owner_id":-162894513,   "video_id":456239000,   "question":{        "id":11,      "text":"Кто живёт с пятью сердцами?",      "answers":[           {              "id":0,            "text":"Зеленая лягушка"         },         {              "id":1,            "text":"Дождевой червь"         },         {              "id":2,            "text":"Синий кит"         }      ],      "time":null,      "number":1   },   "version":2}')
    # тестируем работу поисковиков
    try:
        test = yandex_grep("test")
    except Exception as e:
        print("Ошибка работы с Яндексом:")
        print (e)
        return

    try:
        test = google_grep("test")
    except Exception as e:
        print("Ошибка работы с Гуглом:")
        print (e)
        return

    print("Тест поисковиков пройден успешно. Ждем вопросов.")
    lp.game_waiting()

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("Выход из программы")
        pass
