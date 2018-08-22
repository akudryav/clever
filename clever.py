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
qwords = ["Что", "Чем", "Где", "Когда", "Кто", "Кем", "Кому", "Почему", "Зачем", "Как", "Какой", "Какая", "Какие", "Какое", "Какому", "Каким", "Кaкую", "Чей", "Сколько", "Куда", "Откуда"]
api = CleverApi(apis.CLEVER)
lp = CleverLongPoll(api)
# словарь для перевода числительных 0-9
units = (
    u'ноль', u'один',  u'два',
    u'три', u'четыре', u'пять',
    u'шесть', u'семь', u'восемь', u'девять'
)

yandex = Yandex(api_user=apis.YANDEX_LOGIN, api_key=apis.YANDEX_KEY)
google = build("customsearch", "v1", developerKey=apis.GOOGLE_KEY, cache_discovery=False)

# получение текстового названия цифры
def digit_name(s):
    # проверка на число от 0 до 9
    try:
        n = int(s)
        if n >= 0 and n <10:
            return units[n]
        return s
    except ValueError:
        return s
# предварительная обработка ответов
def process_answers(answers):
    return [digit_name(x['text']) for x in answers]
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
    for idx, ans in enumerate(answers):
        for snip in snippets:
            if ans.lower() in snip.lower():
                res[idx] += 1
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
    answers = process_answers(event["question"]["answers"])
    print(answers)
    total_count = count_frequency(event["question"]["text"], answers)
    #если обычный подсчет не помог 
    if total_count == [0, 0, 0]:
        # убираем из вопроса первое вопросительное слово
        first, _, rest = event["question"]["text"].partition(" ")
        if first in qwords:
            phrase = rest.replace('?','')
        else:
            phrase = event["question"]["text"].replace('?','')
        # выполняем поиск вместе с вариантами ответов через оператор ИЛИ
        pattern = "|".join(answers)+' '+phrase
        total_count = count_frequency(pattern, answers)
   
    print(total_count)

@lp.right_answer_handler()
def new_answer(event):
    print("Правильный ответ: "+str(event["question"]["right_answer_id"]+1))

def main():
    #event = json.loads('{     "type":"sq_question",   "owner_id":-162894513,   "video_id":456239000,   "question":{        "id":11,      "text":"Сколько в Москве холмов?",      "answers":[           {              "id":0,            "text":"11"         },         {              "id":1,            "text":"2"         },         {              "id":2,            "text":"7"         }      ],      "time":null,      "number":1   },   "version":2}')
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
