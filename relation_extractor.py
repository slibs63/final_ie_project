import os
import re
import json
import nltk

"""
def save_chapters(chapters):
    path = os.getcwd() + '/data/chapters/chapter_'
    for i, chapter in enumerate(chapters):
        with open(path + str(i) + '.txt', 'w') as outfile:
            json.dump(chapter, outfile)

def preprocess_text(chapter):
    chapter = [[nltk.pos_tag(nltk.word_tokenize(sent)) for sent in
                nltk.sent_tokenize(paragraph)]
               for paragraph in chapter]
    return chapter

def write_to_file(chapter, i):
    path = os.getcwd() + '/data/pos_tagged/chapter_'
    with open(path + str(i) + '.pos', 'w') as outfile:
        for paragraph in chapter:
            string = ''
            for sentence in paragraph:
                string += ' '.join([t[0] + '_' + t[1] for t in sentence]) + '\n'
            outfile.write(string + '\n')
"""

def read_file():
    with open(os.getcwd() + '/data/game_of_thrones.txt', 'r') as infile:
        raw_text = infile.read()

    paragraphs = raw_text.split(' \n\n')
    paragraphs = [para for para in paragraphs if para]
    paragraphs = [re.sub('\n', '', para) for para in paragraphs]
    return paras_to_chapters(paragraphs)

def paras_to_chapters(paragraphs):
    chapters = []
    chapter = [paragraphs[0]]
    for paragraph in paragraphs[1:]:
        if paragraph.isupper() and paragraph.isalpha():
            chapters.append(chapter)
            chapter = [paragraph]
        else:
            chapter.append(paragraph)
    chapters.append(chapter)
    return chapters

def relation_of():
    terms = {'father', 'mother', 'son', 'daughter', 'aunt', 'uncle', 'brother',
             'sister', 'niece', 'nephew', 'cousin', 'husband', 'wife'}

def extract_people():
    path = os.getcwd() + '/data/ner_tagged/'
    people = {}
    characters = []
    for root, dirs, files in os.walk(path):
        for f in files:
            with open(path + f, 'r') as infile:
                text = infile.read()
                text = re.sub('\n', '', text)
                tokens = text.split(' ')
                # Group consecutive 'PERSON' mentions together:
                holding_character = False
                character = None
                for i, token in enumerate(tokens):
                    if token.endswith('/PERSON') and token[0].isupper():
                        if not holding_character:
                            character = token.split('/')[0]
                        else:
                            character += ' ' + token.split('/')[0]
                        holding_character = True
                    else:
                        if character:
                            characters.append(character)
                        holding_character = False
    characters = [char for char in characters if ' ' in char]
    # Compile dictionary of characters by their mention counts:
    for character in characters:
        if character in people:
            people[character] += 1
        else:
            people[character] = 1

    return people

if __name__ == "__main__":  
    chapters = read_file()
    people = extract_people() # Might make sense to just take 2-word people
