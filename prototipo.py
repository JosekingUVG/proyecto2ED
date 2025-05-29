import pandas as pd
from sklearn.metrics.pairwise import euclidean_distances
import mysql.connector
import math
import networkx as nx

import tkinter as tk
from tkinter import ttk, simpledialog, messagebox, filedialog

# Conexión a la base de datos
cnx = mysql.connector.connect(
    host='localhost',
    user='admin',
    password='123',
    database='login'
)
cursor = cnx.cursor(dictionary=True)

def confirmar(username):
    query = "SELECT * FROM users WHERE username = %s"
    cursor.execute(query, (username,))
    return cursor.fetchone() is not None

def registrar():
    reg_window = tk.Tk()
    reg_window.withdraw()

    username = simpledialog.askstring("Registro", "Nuevo usuario:")
    password = simpledialog.askstring("Registro", "Nueva contraseña:", show="*")

    if not username or not password:
        messagebox.showwarning("Registro Cancelado", "Debes completar ambos campos.")
        return

    if confirmar(username):
        messagebox.showerror("Error", "El usuario ya existe.")
    else:
        cursor.execute("INSERT INTO users (username, password) VALUES (%s, %s)", (username, password))
        cnx.commit()
        messagebox.showinfo("Éxito", f"Usuario '{username}' registrado con éxito.")

def verificar(username, password):
    query = "SELECT * FROM users WHERE username = %s AND password = %s"
    cursor.execute(query, (username, password))
    return cursor.fetchone() is not None

def login():
    login_window = tk.Tk()
    login_window.withdraw()

    while True:
        opcion = messagebox.askquestion("Inicio", "¿Tienes una cuenta?", icon='question')
        if opcion == 'no':
            registrar()
        else:
            break

    for _ in range(3):  # se le da 3 intentos al usuario
        username = simpledialog.askstring("Login", "Usuario:")
        password = simpledialog.askstring("Login", "Contraseña:", show='*')

        if username and password and verificar(username, password):
            messagebox.showinfo("Acceso Concedido", f"¡Bienvenido, {username}!")
            return True
        else:
            messagebox.showerror("Error", "Usuario o contraseña incorrectos.")

    messagebox.showwarning("Acceso Denegado", "Demasiados intentos fallidos.")
    return False

# Verifica el login antes de continuar
if not login():
    cursor.close()
    cnx.close()
    exit()

# Selección del CSV por el usuario
root = tk.Tk()
root.withdraw()
csv_path = filedialog.askopenfilename(title="Selecciona tu playlist CSV", filetypes=[("CSV Files", "*.csv")])
if not csv_path:
    messagebox.showerror("Error", "No seleccionaste ningún archivo CSV.")
    cursor.close()
    cnx.close()
    exit()

# Leer CSV seleccionado
playlist = pd.read_csv(csv_path)

def none(x):
    if isinstance(x, float) and math.isnan(x):
        return None
    if isinstance(x, str) and x.strip() == '':
        return None
    return x

# Cargar datos de la base de datos en un frame
cursor.execute("SELECT * FROM songs")
rows = cursor.fetchall()
base = pd.DataFrame(rows)

# Eliminar canciones repetidas
base = base.drop_duplicates(subset=['TrackName', 'ArtistName'])

# Categorías de análisis
categorias = [
    'Danceability', 'Energy', 'Key', 'Loudness', 'Mode',
    'Speechiness', 'Acousticness', 'Instrumentalness',
    'Liveness', 'Valence', 'Tempo'
]

# Eliminar canciones con datos incompletos
playlist = playlist.dropna(subset=categorias)
base = base.dropna(subset=categorias)

if playlist.empty or base.empty:
    print("No hay suficientes datos para realizar recomendaciones.")
    recommendations = pd.DataFrame()
else:
    # Vector promedio de la playlist
    playlistvector = playlist[categorias].mean().values.reshape(1, -1)

    # Crear conjunto con los nombres de las canciones en la playlist para filtrar
    playlist_names = set(playlist['Track Name'])

    # Filtra canciones que no están en la playlist
    cni = base[~base['TrackName'].isin(playlist_names)].copy()

    # Crear grafo
    G = nx.Graph()
    G.add_node("avg")

    for idx, row in cni.iterrows():
        song_id = idx
        G.add_node(song_id, **row.to_dict())
        distancia = euclidean_distances([row[categorias].values], playlistvector)[0][0]
        G.add_edge("avg", song_id, weight=distancia)

    # Obtener 10 canciones más cercanas
    vecinos = sorted(G["avg"].items(), key=lambda x: x[1]['weight'])[:10]
    recomendations_indices = [song_id for song_id, _ in vecinos]
    recommendations = cni.loc[recomendations_indices]
    recommendations['Distance'] = [G["avg"][i]['weight'] for i in recomendations_indices]

    # Mostrar por consola
    print("Canciones recomendadas:\n")
    for idx, (_, row) in enumerate(recommendations.iterrows(), 1):
        print(f"{idx}. {row['TrackName']} – {row['ArtistName']} ({row['Genres']})")

def obtener_recomendaciones():
    cancion_actual = playlist.iloc[0] if not playlist.empty else None
    return recommendations, cancion_actual

def interfaz():
    recomendaciones, cancion_actual = obtener_recomendaciones()

    root = tk.Tk()
    root.title("Mi Playlist - Estilo Spotify")
    root.geometry("600x600")
    root.configure(bg="#121212")

    titulo = tk.Label(root, text="Recomendador Musical", font=("Helvetica", 20, "bold"), fg="white", bg="#121212")
    titulo.pack(pady=20)

    ttk.Separator(root, orient='horizontal').pack(fill='x', padx=40, pady=10)

    recomendaciones_label = tk.Label(root, text=" Recomendaciones:", font=("Helvetica", 16), fg="#1DB954", bg="#121212")
    recomendaciones_label.pack(pady=10)

    frame = tk.Frame(root, bg="#121212")
    frame.pack()

    if not recomendaciones.empty:
        for idx, row in enumerate(recomendaciones.itertuples(), 1):
            rec = tk.Label(
                frame,
                text=f"{idx}. {row.TrackName} – {row.ArtistName} ({row.Genres})",
                font=("Helvetica", 12),
                fg="white",
                bg="#121212",
                anchor="w",
                justify="left",
                wraplength=550
            )
            rec.pack(anchor="w", padx=20, pady=2)
    else:
        tk.Label(frame, text="No hay recomendaciones.", fg="white", bg="#121212").pack()

    root.mainloop()


interfaz()

# Cierre de conexión
cursor.close()
cnx.close()
