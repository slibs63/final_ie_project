import re
import os
import json
import nltk
from xml.etree import ElementTree

class Event():
    def __init__(self, item):
        self.word = item[0]
        self.pos = item[1]
        self.position = None
        self.before = None
        self.after = None
        self.during = None
        self.modality = None

    def add_position(self, position):
        self.position = position

class Timex():
    def __init__(self, item):
        self.word = item[0]
        self.pos = item[1]
        self.position = None

    def add_position(self, position):
        self.position = position

TIME_EXPRESSIONS = {'after', 'afterward', 'afterwards', 'ago', 'as',
                    'as soon as', 'as long as', 'at', 'before', 'between', 'by',
                    'during', 'for', 'in', 'into', 'last', 'meanwhile', 'next',
                    'now', 'on', 'once', 'then', 'tomorrow', 'until', 'when',
                    'while', 'yesterday'}

'''
def read_file():
    """ Some basic text pre-processing on the input file. """
    with open(os.getcwd() + '/data/fables.txt') as infile:
        raw_string = infile.read()
    pattern = r'\n[A-Z+, ]+\n'
    fables = re.split(pattern, raw_string)
    new_fables = []
    # Some basic cleanup:
    for fable in fables:
        if fable.startswith('\n'):
            new_fables.append(fable[1:])
        elif not fable or fable.startswith('[Pg '):
            continue
        else:
            new_fables.append(fable)
    return new_fables

def tokenize(fables):
    return [[nltk.pos_tag(nltk.word_tokenize(sent))
             for sent in nltk.sent_tokenize(fable)[:-1]]
            for fable in fables]

def get_time_expressions():
    path = os.getcwd() + '/tempeval_training/data/taskAB/'
    pattern = r'>(\w+)<\/TIMEX3>'
    timexes = []
    for root, dirs, files in os.walk(path):
        for f in files:
            with open(path + f, 'r') as infile:
                timexes.extend(re.findall(pattern, infile.read()))
    return timexes
'''           

def read_json():
    with open(os.getcwd() + '/data/processed_fables.txt', 'r') as infile:
        return json.load(infile)

def build_event_graph(fable):
    """
    Given a sentence- and word-tokenized, part-of-speech tagged fable,
    iterate through (token, tag) pairs looking for verbs which will function
    as events.  Adjust pointers to default position of chronological order.
    """
    graph = []
    for i, sentence in enumerate(fable):
        for j, token in enumerate(sentence):
            if token[1].startswith('V'):
                event = Event(token)
                event.add_position((i, j))
                if graph:
                    event.before = graph[-1]
                graph.append(event)
    for i, item in enumerate(graph[:-1]):
        event.after = graph[i + 1]
    return graph

def build_timex_graph(fable):
    graph = []
    for i, sentence in enumerate(fable):
        for j, token in enumerate(sentence):
            if token[0] in TIME_EXPRESSIONS and token[1] in ('IN', 'RB'):
                timex = Timex(token)
                timex.add_position((i, j))
                graph.append(timex)
    return graph

def show_events(events):
    for event in events:
        word = event.word
        if event.before:
            before = event.before.word
        else:
            before = "None"
        if event.after:
            after = event.after.word
        else:
            after = "None"
        print before, word, after


if __name__ == "__main__":
    fables = read_json()
    events = build_event_graph(fables[0])
    timexes = build_timex_graph(fables[0])
