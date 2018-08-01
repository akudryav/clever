#! /usr/bin/env python
# -*- coding: utf-8 -*-
# Set up modules from https://libraries.io/pypi/cleverapi
# https://github.com/oncecreated/cleverapi
# pip install cleverapi --upgrade
# pip install yandex-search
# pip install --upgrade google-api-python-client
from cleverapi import CleverApi, CleverLongPoll
from yandex import Yandex
from googleapiclient.discovery import build
import json
import apis
# вопросительные слова для выкидывания из начала вопроса при поиске вместе с ответами
qwords = ["Что", "Чем", "Где", "Когда", "Кто", "Кем", "Кому", "Почему", "Зачем", "Как", "Какой", "Какая", "Какие", "Какое", "Какому", "Каким", "Чей", "Сколько", "Куда", "Откуда"]
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
    # проверяем наличие результатов
    if res["queries"]["request"][0]["totalResults"] != "0":
        return [x['snippet'] for x in res["items"]]
    else:
        return []
# подсчет числа ответов в выдаче (снипетах)
def count_answers(answers, snippets):
    res = [0, 0, 0]
    for ans in answers:
        for snip in snippets:
            if ans['text'].lower() in snip.lower():
                res[ans['id']] += 1
    return res

# Выполняем поиск и Суммируем число ответов по Яндексу и Гуглу вместе 
def count_frequency(question, answers):
    yandex_items = yandex_grep(question)
    google_items = google_grep(question)
    yandex_count = count_answers(answers, yandex_items)
    google_count = count_answers(answers, google_items)
    return [x + y for x, y in zip(yandex_count, google_count)]

@lp.question_handler()
def new_question(event):
    print(event["question"]["text"])
    print([x['text'] for x in event["question"]["answers"]])
    total_count = count_frequency(event["question"]["text"], event["question"]["answers"])
    #если обычный подсчет не помог 
    if total_count == [0, 0, 0]:
        # убираем из вопроса первое вопросительное слово
        first, _, rest = event["question"]["text"].partition(" ")
        if first in qwords:
            phrase = rest.replace('?','')
        else:
            phrase = event["question"]["text"].replace('?','')
        # выполняем поиск вместе с вариантами ответов через оператор ИЛИ
        pattern = "|".join([x['text'] for x in event["question"]["answers"]])+' '+phrase
        total_count = count_frequency(pattern, event["question"]["answers"])
   
    print(total_count)

@lp.right_answer_handler()
def new_answer(event):
    print("Правильный ответ: "+str(event["question"]["right_answer_id"]))

def main():
    #event = json.loads('{     "type":"sq_question",   "owner_id":-162894513,   "video_id":456239000,   "question":{        "id":11,      "text":"Кaкую из этих прoфеcсий кyкла Бaрби «освoила» рaньше, чeм остaльные?",      "answers":[           {              "id":0,            "text":"Учитeльницa"         },         {              "id":1,            "text":"Няня"         },         {              "id":2,            "text":"Мeдсeстра"         }      ],      "time":null,      "number":1   },   "version":2}')
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
