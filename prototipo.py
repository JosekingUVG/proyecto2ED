import pandas as pd
from sklearn.metrics.pairwise import euclidean_distances
import mysql.connector
import math

def none(x):
    if isinstance(x, float) and math.isnan(x):
        return None
    if isinstance(x, str) and x.strip() == '':
        return None
    return x

# Conexión a la base de datos
cnx = mysql.connector.connect(
    host='localhost',
    user='admin',
    password='123',
    database='login'
)
cursor = cnx.cursor(dictionary=True)

# Cargar datos de la base de datos en un frame
cursor.execute("SELECT * FROM songs")
rows = cursor.fetchall()
base = pd.DataFrame(rows)

# Eliminar canciones repetidas
base = base.drop_duplicates(subset=['TrackName', 'ArtistName'])

# Cargar playlist personal
playlist = pd.read_csv("playlist1.csv")

categorias = [
    'Danceability', 'Energy', 'Key', 'Loudness', 'Mode',
    'Speechiness', 'Acousticness', 'Instrumentalness',
    'Liveness', 'Valence', 'Tempo'
]

# Eliminar canciones con datos incompletos
playlist = playlist.dropna(subset=categorias)
base = base.dropna(subset=categorias)

# Verifica si hay datos para continuar
if playlist.empty or base.empty:
    print("No hay suficientes datos para realizar recomendaciones.")
else:
    # Vector promedio de la playlist
    playlistvector = playlist[categorias].mean().values.reshape(1, -1)

    # Crear conjunto con los nombres de las canciones en la playlist para filtrar
    playlist_names = set(playlist['Track Name'])

    # Filtra canciones que no están en la playlist
    cni = base[~base['TrackName'].isin(playlist_names)].copy()

    # Calcula distancia euclidiana
    distances = euclidean_distances(cni[categorias], playlistvector)
    cni['Distance'] = distances

    # Top 10 recomendaciones más cercanas
    recommendations = cni.sort_values(by='Distance').head(10)

    # Mostrar resultados con índice consecutivo
    print("Canciones recomendadas:\n")
    for idx, (_, row) in enumerate(recommendations.iterrows(), 1):
        print(f"{idx}. {row['TrackName']} – {row['ArtistName']} ({row['Genres']})")

# Cierre de conexión
cursor.close()
cnx.close()
