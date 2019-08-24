
# coding: utf-8

# In[1]:


import pandas as pd
import numpy as np
import sys
from itertools import groupby
from IPython.display import display
import os

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

data_folder = '/media/hudson/Elements/data/DiploDatos-aprendizaje-no-supervizado/ml-20m'
movies_path = os.path.join(data_folder, 'movies.csv')
ratings_path = os.path.join(data_folder, 'ratings.csv')

def size(obj):
    return "{0:.2f} MB".format(sys.getsizeof(obj) / (1000 * 1000))


# In[2]:


movies = pd.read_csv(movies_path)
print('movies -- dimensions: {0};   size: {1}'.format(movies.shape, size(movies)))
display(movies.head())


# In[3]:


import matplotlib.pyplot as plt
movies['splitted_genres'] = movies['genres'].str.split('|', n=0, expand=False)
display(movies.head())
# generos = movies['splitted_genres'].unique()
count_by_genre = movies['splitted_genres'].apply(pd.Series).stack().value_counts()
display(count_by_genre)
count_by_genre.plot.bar(figsize=(16, 4))


# In[4]:


# Obtener los dummies sobre un campo que tiene listas dentro
# https://stackoverflow.com/questions/47026585/unhashable-type-list-error-with-get-dumies
# pd.get_dummies(df.categories.apply(pd.Series).stack()).sum(level=0)

dummy_genres = pd.get_dummies(movies['splitted_genres'].apply(pd.Series).stack()).sum(level=0)
movies_with_dummies_genres = pd.concat([movies, dummy_genres], axis=1)
# se quitan las dos ultimas categorías que tiene pocas películas
movies_cleaned = movies_with_dummies_genres.drop(columns=['genres', 'splitted_genres', 'IMAX','(no genres listed)'])
display(movies_cleaned.head())


# In[5]:


ratings = pd.read_csv(ratings_path, usecols = ['userId', 'movieId', 'rating'])
print('ratings -- dimensions: {0};   size: {1}'.format(ratings.shape, size(ratings)))
display(ratings.head())


# In[6]:


# Cuantos ratings hay con cada puntuacion?
# No me interesan los bajos. Entiendo que "comprar" el item es darle un buen rating
count_by_rank = ratings.groupby('rating').size()
display(count_by_rank)
count_by_rank.plot.bar(figsize=(16, 4))


# In[7]:


# voy a tomar solo los ratings > a lo que defino
min_rating_to_count = 5
ratings_good = ratings[ratings['rating'] >= min_rating_to_count]
print('ratings_good -- dimensions: {0};   size: {1}'.format(ratings_good.shape, size(ratings_good)))
display(ratings_good.head())


# In[8]:


# tomo al "userid" como el identificador de transaccion.
# Interpreto que lo cada uusario vio y valoro positivamente es un "compra"
# Quitar el rating que no es necesario
ratings_cleaned = ratings.drop(columns=['rating'])

# identificar las transacciones (IDUSUARIO = [ID_PELI_1, ID_PELI_n, ID_PELI_m, ...])
transactions = ratings_cleaned.groupby('userId')['movieId'].apply(list)
print('------------- Transacciones (solo algunas) -----------------')
print(transactions[:20])


# In[ ]:


from efficient_apriori import apriori

print('Transacciones encontradas: {}'.format(len(transactions)))
# para probar solo con algunos
transactions = transactions[:10]

min_support = 0.1
min_confidence = 0.8
min_lift = 4
itemsets, rules = apriori(transactions, min_support=min_support,  min_confidence=min_confidence)

print(f'------------- RULES Support:{min_support} Confidence:{min_confidence}-----------------')
#rules = filter(lambda rule: len(rule.lhs) == 2 and len(rule.rhs) == 1, rules)
rules=sorted(rules, key=lambda rule: rule.confidence)
selected_rules = []
for rule in rules:
    if rule.lift > min_lift:
        selected_rules.append(rule)
        print(rule) # Prints the rule and its confidence, support, lift, ...

print('FIN')

