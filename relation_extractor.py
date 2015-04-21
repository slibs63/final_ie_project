import os
import re

def get_windows_tokens():
    path = os.getcwd() + '/data/pos_tagged/'
    relations = ['father', 'mother', 'son', 'daughter', 'aunt', 'uncle',
                 'brother', 'sister', 'niece', 'nephew', 'cousin', 'husband',
                 'wife']
    windows = {}
    for relation in ['father', 'mother', 'son', 'daughter', 'brother', 'sister']:
        windows[relation] = []
        for root, dirs, files in os.walk(path):
            for f in files:
                with open(path + f, 'r') as infile:
                    tokens = infile.read().split()
                    for i, token in enumerate(tokens):
                        if token.split('_')[0].lower() == relation:
                            if i < 3:
                                before = tokens[:i]
                            else:
                                before = tokens[i-3:i]
                            if i > len(tokens) - 3:
                                after = tokens[i:]
                            else:
                                after = tokens[i+1:i+4]
                            window = before + [token] + after
                            windows[relation].append(window)
    return windows

def get_windows_strings():
    path = os.getcwd() + '/data/chapters/'
    examples = []
    pattern = r"[\w ]+ father [\w \"\',]+"
    for root, dirs, files in os.walk(path):
        for f in files:
            with open(path + f, 'r') as infile:
                text = infile.read()
                matches = re.findall(pattern, text)
                print matches
    

def extract_people():
    path = os.getcwd() + '/data/ner_tagged/'
    titles = {'king', 'queen', 'prince', 'princess', 'ser', 'khal', 'khaleesi',
              'maester', 'lord', 'lady'}
    characters = []
    for root, dirs, files in os.walk(path):
        for f in files:
            with open(path + f, 'r') as infile:
                text = infile.read()
                text = re.sub('\n', '', text)
                tokens = text.split(' ')
                # Group consecutive 'PERSON' mentions together:
                holding_character = False # a flag for whether we're mid-entity
                character = None
                for i, token in enumerate(tokens):
                    if (token.endswith('/PERSON') and token[0].isupper() and
                        token.split('/')[0].lower() not in titles):
                        if not holding_character:
                            character = token.split('/')[0]
                        else:
                            character += ' ' + token.split('/')[0]
                        holding_character = True
                    else:
                        if character:
                            characters.append(character)
                        holding_character = False
    characters = set([char for char in characters if ' ' in char])

    return characters

def extract_families():
    people = list(extract_people())
    people = [person.split() for person in people]
    surnames = [name[-1] for name in people]
    surnames = set([name for name in surnames if surnames.count(name) > 1])
    families = {}
    for surname in surnames:
        for name in people:
            if name[-1] == surname:
                if surname not in families:
                    families[surname] = [' '.join(name[:-1])]
                else:
                    families[surname].append(' '.join(name[:-1]))
    return families

if __name__ == "__main__":  
    families = extract_families()
