import os
import re
import itertools

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
    pattern = r"[\w \"\',\.]+ father [\w \"\',\.]+"
    for root, dirs, files in os.walk(path):
        for f in files:
            with open(path + f, 'r') as infile:
                text = infile.read()
                examples.append(re.findall(pattern, text))
    return examples
    

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

def remove_duplicates(families):
    for family in families:
        # Very domain specific, learned after looking over extracted names.
        if 'House' in families[family]:
            families[family].remove('House')
        for member1 in families[family]:
            for member2 in families[family]:
                if member1 in member2 and member1 != member2:
                    families[family].remove(member2)
                    break
    return families

def potential_relations(families):
    relations = {}
    for family in remove_duplicates(families):
        relations[family] = list(itertools.combinations(families[family], 2))
    return relations

def find_relation(relation):
    path = os.getcwd() + '/data/chapters/'
    relations = ['father', 'mother', 'son', 'daughter', 'brother', 'sister']
    results = []
    for root, dirs, files in os.walk(path):
        for f in files:
            with open(path + f, 'r') as infile:
                paragraphs = infile.readlines()
                for paragraph in paragraphs:
                    if (relation[0].lower() in paragraph.lower() and
                        relation[1].lower() in paragraph.lower()):
                        for r in relations:
                            if (' ' + r + ' ' in paragraph or
                                ' ' + r + 's' in paragraph or
                                ' ' + r + "'" in paragraph):
                                results.append(r)
    if results:
        return compute_confidence(results)
    else:
        return ('no relation')

def compute_confidence(relations):
    """
    For each potential relation, calculate the confidence that the relation
    holds by dividing the number of mentions of that relationship by the total
    number of relationship mentions.
    """
    num_rels = float(len(relations))
    parent_child = relations.count('father') + relations.count('mother') + \
                   relations.count('son') + relations.count('daughter')
    sibling = relations.count('brother') + relations.count('sister')
    listing = (('parent_child', parent_child), ('sibling', sibling))
    # Return listing sorted by descending frequency of relations:
    listing = sorted(listing, key=lambda x: x[1])
    listing.reverse()
    return listing
    
def find_relations(relations):
    for family in relations:
        for i, relation in enumerate(relations[family]):
            relations[family][i] = (relation, find_relation(relation))
    return relations

def group_siblings(relations, family):
    sibling_contenders = []
    for relation in relations[family]:
        try:
            total_rels = float(sum([rel[1] for rel in relation[1]]))
            if relation[1][0][0] == 'sibling' and relation[1][0][1] > 2:
                sibling_contenders.append(relation)
        except IndexError:
            pass
    return sibling_contenders

def is_equivalence_class(relations):
    """
    Takes in a list of tuples signifying a relation, returns true if they form
    an equivalence class, false otherwise.
    """
    # Get the set of all characters mentioned in the relations:
    total = set()
    for rel in relations:
        total.update(set(rel))
    # Determine whether the set of combinations of these is equivalent to the
    # set of relations provided.
    combos = set([frozenset(c) for c in itertools.combinations(list(total), 2)])
    relations = set([frozenset(r) for r in relations])
    return combos == relations

def get_rel_counts(relations):
    counts = dict()
    for rel in relations:
        for name in rel:
            if name not in counts:
                counts[name] = 1
            else:
                counts[name] += 1
    return counts
        

def get_equivalence_classes(relations):
    """
    Takes in a list of tuples signifying a relation, checks which of them form
    an equivalence class.
    """
    print "Getting equivalence classes"
    if is_equivalence_class(relations):
        return relations
    accepts = []
    rejects = []
    # While the set of relations does not form an equivalence class, keep
    # removing the least frequently occurring character until it is one.
    while not is_equivalence_class(relations):
        counts = get_rel_counts(relations)
        least_frequent = sorted(counts, key=counts.get)[0]
        print "Removing", least_frequent
        # Put tuples with the least frequent character's name in rejects,
        # remove it from relations:
        rejects.extend([rel for rel in relations if least_frequent in rel])
        relations = [rel for rel in relations if rel not in rejects]
        print "rejects:", rejects
        if relations and is_equivalence_class(relations):
            accepts.append(relations)
            # Remove the names from 'accepts' in rejects:
            accepted = set()
            for rel in relations:
                accepted.update(set(rel))
            if not accepted:
                break
            relations = [rel for rel in rejects if rel[0] not in accepted and
                         rel[1] not in accepted]
            print "relations:", relations
    return accepts, relations
    

if __name__ == "__main__":  
    families = extract_families()
    relations = potential_relations(families)
    relations = find_relations(relations)
    siblings = group_siblings(relations, 'Stark')
    eqs, rejects = get_equivalence_classes([s[0] for s in siblings])
