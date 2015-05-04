import os
import re
import copy
import json
import nltk
import itertools


######################
# GET NAMED ENTITIES #
######################

def get_characters():
    """
    Iterate through each chapter in search of tokens tagged 'PERSON' by the
    Standford CoreNLP NER system.
    """
    # Iterate through each chapter:
    path = os.getcwd() + '/data/ner_tagged/'
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
                        
    # Return the set of characters with two names:
    return set([char for char in characters if ' ' in char])


def extract_titles():
    """
    Guess which "first names" might actually be titles by counting how many
    times they appear, return a list of these titles.
    """
    names = get_characters()
    first_names = [name.split()[0] for name in names]
    counts = dict()
    for name in first_names:
        if name in counts:
            counts[name] += 1
        else:
            counts[name] = 1

    return [name for name in counts if counts[name] > 4]


def get_families():
    """
    With the list of extracted character names, compile a list of family names
    and then group characters by family.
    """
    # Get list of characters and find the list of family names:
    people = list(get_characters())
    people = [person.split() for person in people]
    titles = extract_titles()
    surnames = [name[-1] for name in people]
    surnames = set([name for name in surnames if surnames.count(name) > 1])

    # Populate a dict keyed on families with lists of first names as values
    families = {}
    for surname in surnames:
        for name in people:
            if name[-1] == surname and name[-2] not in titles:
                if surname not in families:
                    # Use -2 instead of 0 to avoid titles
                    families[surname] = [name[-2]]
                else:
                    families[surname].append(name[-2])
    for family in families:
        families[family] = list(set(families[family]))
    return families

def remove_duplicates(families):
    """
    Some names are nicknames, with shortened versions of the first name. We
    can remove some duplicates by looking for the names of family members that
    are fully contained within the names of other family members.
    """
    for family in families:
        # Very domain specific, learned after looking over extracted names.
        if 'House' in families[family]:
            families[family].remove('House')
        for member1 in families[family]:
            for member2 in families[family]:
                if member1 in member2 and member1 != member2:
                    families[family].remove(member1)
                    break
    return families


#################
# GET RELATIONS #
#################

def potential_relations(families):
    """
    Compute a list of all the possible combinations of characters within a
    family to later guess the relationships of.
    """
    relations = {}
    for family in remove_duplicates(families):
        relations[family] = list(itertools.combinations(families[family], 2))
    return relations

    
def find_relations(relations):
    """
    Iterate through each relation in each family, and get the probabilities
    for each relationship.
    """
    for family in relations:
        for i, relation in enumerate(relations[family]):
            relations[family][i] = (relation, get_relation_counts(relation))
    return relations


def get_relation_counts(relation):
    """
    Given a potential relation of two characters, search through the text
    looking for instances of a relationship term co-occurring in the same
    paragraph with those two characters.
    """
    # Iterate through each chapter:
    name1, name2 = relation
    path = os.getcwd() + '/data/chapters/'
    relations = ['father', 'mother', 'son', 'daughter', 'brother', 'sister']
    results = []
    for root, dirs, files in os.walk(path):
        for f in files:
            with open(path + f, 'r') as infile:
                paragraphs = infile.readlines()
                for paragraph in paragraphs:
                    text = paragraph.lower()
                    # If both names and a relationship term appear in the
                    # paragraph, append the relationship to the results:
                    if name1.lower() in text and name2.lower() in text:
                        for r in relations:
                            if (' ' + r + ' ' in paragraph or
                                ' ' + r + 's' in paragraph or
                                ' ' + r + "'" in paragraph):
                                results.append(r)
    if results:
        return score_relationship(results)
    # If none were found, assume no relationship:
    else:
        return ([('no_rel', 0)])


def score_relationship(relations):
    """
    For each potential relation, count the number of times a relationship word
    appears, group these mentions by super-relationship (e.g. brother, sister ->
    sibling), and return the most commonly occurring relationship.
    """
    parent_child_relations = ['father', 'mother', 'son', 'daughter']
    sibling_relations = ['brother', 'sister']
    parent_child = sum([relations.count(rel) for rel in parent_child_relations])
    sibling = sum([relations.count(rel) for rel in sibling_relations])

    # Return listing sorted by descending frequency of relations:
    listing = (('parent_child', parent_child), ('sibling', sibling))
    listing = sorted(listing, key=lambda x: x[1])
    listing.reverse()
    return listing


############################
# APPLY GLOBAL CONSTRAINTS #
############################

def get_rel_counts(relations):
    """
    A helper function to count the number times certain names appear in a
    relation list.
    """
    counts = dict()
    for rel in relations:
        for name in rel:
            if name not in counts:
                counts[name] = 1
            else:
                counts[name] += 1
    return counts


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


def get_potential_siblings(relations):
    """
    Given the set of all relations, a family name, and the relationship we're
    interested in, return a list of all the relations in that family whose
    most likely relationship is the one being queried.
    """
    contenders = []
    for relation in relations:
        try:
            if relation[1][0][0] == 'sibling' and relation[1][0][1] > 2:
                contenders.append(relation[0])
        except IndexError:
            pass
    return contenders
        

def get_siblings(relations):
    """
    Takes in a list of tuples signifying a relation, returns a set of names
    that comprise the largest equivalence class within that list.
    """
    relations = get_potential_siblings(relations)
    siblings = set()
    original_list = copy.deepcopy(relations)
    if not is_equivalence_class(relations):
        # While the set of relations does not form an equivalence class, keep
        # removing the least frequently occurring character until it is one.
        while not is_equivalence_class(relations):
            counts = get_rel_counts(relations)
            least_frequent = sorted(counts, key=counts.get)[0]
            relations = [rel for rel in relations if least_frequent not in rel]
    siblings = set()
    for rel in relations:
        siblings.update(set(rel))
    return siblings


def sibling_constraint(relations, siblings):
    """
    Given a group of confirmed siblings, reset the relationships so that no
    other character can be a sibling of that group.
    """
    for i, ((name1, name2), possibilities) in enumerate(relations):
        # If the relationship signified is a sibling relationship, but one
        # character is in the set of confirmed siblings and the other isn't:
        if possibilities[0][0] == 'sibling':
            if ((name1 in siblings and name2 not in siblings) or
                (name2 in siblings and name1 not in siblings)):
                new_relation = [(name1, name2)]
                # If the counts for the first and second possiblities are equal
                # of the second possibility has a count of 0, assign 'no_rel':
                if (possibilities[1][1] == possibilities[0][1] or
                    possibilities[1][1] == 0):
                    new_relation.append([('no_rel', 0), possibilities[0]])
                # Otherwise swap the first two possibilities:
                else:
                    new_relation.append([possibilities[1], possibilities[0]])
                relations[i] = new_relation
    return relations


def parent_constraint(relations, siblings):
    """
    Given a group of confirmed siblings, find the two most likely parents for
    that group of siblings, and reset the relationships accordingly.
    """
    # Among the list of confirmed siblings, find the characters most commonly
    # guessed as being the parents of those siblings:
    counts = {}
    potential_parents = [r for r in relations if r[1][0][0] == 'parent_child'
                         and (r[0][0] in siblings or r[0][1] in siblings)]
    for (name1, name2), possibilities in potential_parents:
        parent = name1 if name1 not in siblings else name2
        count = possibilities[0][1]
        if parent in counts:
            counts[parent] += count
        else:
            counts[parent] = count
    parents = sorted(counts, key=counts.get, reverse=True)[:2]

    for i, ((name1, name2), possibilities) in enumerate(relations):
        # If one character is in the set of confirmed siblings and the other is
        # one of the 2 most likely parents, change relationship to parent_child
        if ((name1 in parents and name2 in siblings) or
            (name2 in parents and name1 in siblings)):
            relations[i] = ((name1, name2), [('parent_child', counts[parents[0]])])
        # If one character is in the set of confirmed siblings and the other is
        # not one of the 2 most likely parents, but the current predition is
        # parent_child, change it to 'no_rel'
        elif (((name1 in siblings and name2 not in parents) or
               (name2 in siblings and name1 not in parents)) and
               possibilities[0][0] == 'parent_child'):
            relations[i] = ((name1, name2), [('no_rel', 0)])
    return relations
        

def apply_global_constraints(relations):
    """
    Iterate through relations applying global constraints.
    """
    for family in relations:
        rels = relations[family]
        siblings = get_siblings(rels)
        if siblings:
            relations[family] = sibling_constraint(rels, siblings)
            relations[family] = parent_constraint(relations[family], siblings)
    return relations


##############
# EVALUATION #
##############

def evaluate(relations):
    with open(os.getcwd() + '/data/gold_standard.json', 'r') as infile:
        gs = json.load(infile)
        
    # Make sure the relations are sorted in the same order as the gold standard:
    for fam in relations:
        relations[fam] = sorted([(a, b, c) for ((a, b), c) in relations[fam]],
                                key=lambda element: (element[0], element[1]))
        
    tp, tn, fp, fn = 0., 0., 0., 0.
    
    for family in gs:
        gs_rels = gs[family]
        rels = relations[family]
        for i, (rel1, rel2, relationship) in enumerate(rels):
            if relationship[0][0] == gs_rels[i][2]:
                if gs_rels[i][2] == 'no_rel':
                    tn += 1
                else:
                    tp += 1
            else:
                if relationship[0][0] == 'no_rel':
                    fn += 1
                else:
                    fp += 1
                    
    precision = tp / (tp + fp)
    recall = tp / (tp + fn)
    f1 = 2 * (precision * recall) / (precision + recall)
    print "precision:", precision
    print "recall:", recall
    print "f1:", f1   
  

if __name__ == "__main__":  
    families = get_families()
    relations = potential_relations(families)
    relations = find_relations(relations)    
    new_relations = apply_global_constraints(relations)
    evaluate(new_relations)   
