import pandas as pd
import numpy as np
import sys
from itertools import groupby
import os
import csv
from efficient_apriori import apriori

import argparse
parser = argparse.ArgumentParser()
parser.add_argument("--min_support", type=float, help="Min support", required=True)
parser.add_argument("--max_length", type=int, default=2, help="Max length")
parser.add_argument("--min_confidence", type=float, help="Min confidence", required=True)
parser.add_argument("--min_lift", type=int, default=4, help="Min lift to count")
parser.add_argument("--truncate_transactions", type=int, default=0, help="truncate total transactions (for local test)")
parser.add_argument("--data_folder", type=str, help="data folder", required=True)

args = parser.parse_args()

# Descripcion de los datos:
# head movies.csv:
"""
    movieId,title,genres
    1,Toy Story (1995),Adventure|Animation|Children|Comedy|Fantasy
    2,Jumanji (1995),Adventure|Children|Fantasy
    3,Grumpier Old Men (1995),Comedy|Romance
    4,Waiting to Exhale (1995),Comedy|Drama|Romance
    5,Father of the Bride Part II (1995),Comedy
    6,Heat (1995),Action|Crime|Thriller
    7,Sabrina (1995),Comedy|Romance
    8,Tom and Huck (1995),Adventure|Children
    9,Sudden Death (1995),Action
"""

# head ratings.csv
"""
    userId,movieId,rating,timestamp
    1,2,3.5,1112486027
    1,29,3.5,1112484676
    1,32,3.5,1112484819
    1,47,3.5,1112484727
    1,50,3.5,1112484580
    1,112,3.5,1094785740
    1,151,4.0,1094785734
    1,223,4.0,1112485573
    1,253,4.0,1112484940
"""

# mi computer data_folder = '/media/hudson/Elements/data/DiploDatos-aprendizaje-no-supervizado/ml-20m'
# CCAD computer data_folder = 'ml-20m'
data_folder = args.data_folder

movies_path = os.path.join(data_folder, 'movies.csv')
ratings_path = os.path.join(data_folder, 'ratings.csv')

def size(obj):
    return "{0:.2f} MB".format(sys.getsizeof(obj) / (1000 * 1000))

movies = pd.read_csv(movies_path)
print('movies -- dimensions: {0};   size: {1}'.format(movies.shape, size(movies)))
print(movies.head())

movies_cleaned = movies.drop(columns=['genres'])
print(movies_cleaned.head())

ratings = pd.read_csv(ratings_path, usecols = ['userId', 'movieId', 'rating'])
print('ratings -- dimensions: {0};   size: {1}'.format(ratings.shape, size(ratings)))
print(ratings.head())

# Cuantos ratings hay con cada puntuacion?
# No me interesan los bajos. Entiendo que "comprar" el item es darle un buen rating
count_by_rank = ratings.groupby('rating').size()
print(count_by_rank)

# voy a tomar solo los ratings > a lo que defino
min_rating_to_count = 5
ratings_good = ratings[ratings['rating'] >= min_rating_to_count]
print('ratings_good -- dimensions: {0};   size: {1}'.format(ratings_good.shape, size(ratings_good)))
print(ratings_good.head())

# tomo al "userid" como el identificador de transaccion.
# Interpreto que lo cada uusario vio y valoro positivamente es un "compra"
# Quitar el rating que no es necesario
ratings_cleaned = ratings.drop(columns=['rating']).sort_values(by=['userId', 'movieId'])
transactions = ratings_cleaned.values.tolist()
if args.truncate_transactions > 0:
    print('******\n******\nTRUNCATE TRANSACTIONS TO {}******\n******\n'.format(args.truncate_transactions))
    transactions = transactions[:args.truncate_transactions]
print('First transaction: {}'.format(transactions[0]))

print('Transacciones encontradas: {}'.format(len(transactions)))

def gen_transactions():
    for t in transactions:
        yield t

itemsets, rules = apriori(gen_transactions(),
                          max_length=args.max_length,
                          min_support=args.min_support,
                          min_confidence=args.min_confidence,
                          # verbosity=2
                          )

print(f'------------- RULES Support:{args.min_support} Confidence:{args.min_confidence}-----------------')
#rules = filter(lambda rule: len(rule.lhs) == 2 and len(rule.rhs) == 1, rules)
print('Ordenando ..')
rules = sorted(rules, key=lambda rule: rule.lift, reverse=True)

def get_movie_title(movieId):
    flt = movies['movieId'] == movieId
    rows = movies[flt]
    return list(rows['title'])[0]

selected_rules = []
for rule in rules:
    if rule.lift > args.min_lift:
        jrule = {
            'izq': rule.lhs[0],
            'izq_title': get_movie_title(rule.lhs[0]),
            'der': rule.rhs[0],
            'der_title': get_movie_title(rule.rhs[0]),
            'conf': round(rule.confidence, 2),
            'supp': round(rule.support, 2),
            'lift': round(rule.lift, 2),
            'conv': round(rule.conviction, 2)
        }
        selected_rules.append(jrule)
        if len(selected_rules) < 20:
            print(rule) # Prints the rule and its confidence, support, lift, ...

if len(selected_rules) == 0:
    raise Exception('NO SE ENCONTRARON REGLAS!')

print('Reglas encontradas: {}'.format(len(selected_rules)))

f = open('rules.csv', 'w')
fieldnames = selected_rules[0].keys()
writer = csv.DictWriter(f, fieldnames=fieldnames)
writer.writeheader()
for jrule in selected_rules:
    writer.writerow(jrule)
f.close()

# ver que peliculas son 
f = open('summary.txt', 'w')
for jrule in selected_rules:
    
    txt = ('Con una coinfianza de {} (y lift {}) '
            'a los que le gusto la película "{}" '
            'les gusto tambien "{}"\n'.format(jrule['conf'],
                                          jrule['lift'],
                                          jrule['izq_title'],
                                          jrule['der_title'],
                                          ))
    f.write(txt)
    if len(selected_rules) < 20:
        print(txt)

f.close()