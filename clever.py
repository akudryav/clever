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

api = CleverApi(apis.CLEVER)
lp = CleverLongPoll(api)

yandex = Yandex(api_user=apis.YANDEX_LOGIN, api_key=apis.YANDEX_KEY)
google = build("customsearch", "v1", developerKey=apis.GOOGLE_KEY, cache_discovery=False)

def yandex_grep(pattern):
    results = yandex.search(pattern)
    return [x['snippet'] for x in results.items]

def google_grep(pattern):
    res = google.cse().list(q=pattern, cx=apis.GOOGLE_ID).execute()
    return [x['snippet'] for x in res['items']]

def count_answers(answers, snippets):
    res = [0, 0, 0]
    for ans in answers:
        for snip in snippets:
            if ans['text'].lower() in snip.lower():
                res[ans['id']] += 1
    return res

@lp.question_handler()
def new_question(event):
    print(event["question"]["text"])
    yandex_items = yandex_grep(event["question"]["text"])
    google_items = google_grep(event["question"]["text"])
    yandex_count = count_answers(event["question"]["answers"], yandex_items)
    google_count = count_answers(event["question"]["answers"], google_items)
    total_count = [x + y for x, y in zip(yandex_count, google_count)]
    print(total_count)
       

def main():
    #event = json.loads('{     "type":"sq_question",   "owner_id":-162894513,   "video_id":456239000,   "question":{        "id":11,      "text":"Кто живёт с пятью сердцами?",      "answers":[           {              "id":0,            "text":"Зеленая лягушка"         },         {              "id":1,            "text":"Дождевой червь"         },         {              "id":2,            "text":"Синий кит"         }      ],      "time":null,      "number":1   },   "version":2}')
    lp.game_waiting()

if __name__ == '__main__':
    main()
