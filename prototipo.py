import pandas as pd
from sklearn.metrics.pairwise import euclidean_distances


playlist = pd.read_csv("2000s")
base = pd.read_csv("Basedatos.csv")


categorias = [
    'Danceability', 'Energy', 'Key', 'Loudness', 'Mode',
    'Speechiness', 'Acousticness', 'Instrumentalness',
    'Liveness', 'Valence', 'Tempo'
]
generos = []

# saltar columnas que esten vacías
playlist = playlist.dropna(subset=categorias)
base = base.dropna(subset=categorias)

# Calcula el vector de la playlist
playlistvector = playlist[categorias].mean().values.reshape(1, -1)

# Obtener canciones que no estan en la base de datos
cni = base[~base['Track Name'].isin(playlist['Track Name'])].copy()



