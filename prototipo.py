from neo4j import GraphDatabase
import tkinter as tk
from tkinter import ttk, messagebox
import mysql.connector

# Configuración de Neo4j
uri = "neo4j+ssc://43e3c12d.databases.neo4j.io"
user = "neo4j"
password = "GpiSXf6J8wwHOvfB6ABPdzSyftY4zNIBVGZIgIrRtmY"
driver = GraphDatabase.driver(uri, auth=(user, password))

# Conexión a MySQL
def conectar_mysql():
    return mysql.connector.connect(
        host="localhost",
        user="admin",
        password="123",  # Cambia esto por la contraseña de tu usuario MySQL
        database="login"
    )

# Login de usuario
def login():
    def verificar_login():
        username = entry_usuario.get()
        password = entry_contrasena.get()
        conn = conectar_mysql()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE username=%s AND password=%s", (username, password))
        resultado = cursor.fetchone()
        conn.close()

        if resultado:
            login_window.destroy()
            launch()
        else:
            messagebox.showerror("Error", "Usuario o contraseña incorrectos.")

    login_window = tk.Tk()
    login_window.title("Iniciar sesión")

    ttk.Label(login_window, text="Usuario:").grid(row=0, column=0, padx=10, pady=10)
    entry_usuario = ttk.Entry(login_window)
    entry_usuario.grid(row=0, column=1)

    ttk.Label(login_window, text="Contraseña:").grid(row=1, column=0, padx=10, pady=10)
    entry_contrasena = ttk.Entry(login_window, show="*")
    entry_contrasena.grid(row=1, column=1)

    ttk.Button(login_window, text="Iniciar sesión", command=verificar_login).grid(row=2, column=0, columnspan=2, pady=10)
    ttk.Button(login_window, text="Registrarse", command=registro).grid(row=3, column=0, columnspan=2, pady=5)

    login_window.mainloop()

# Registro de usuario
def registro():
    def guardar_usuario():
        username = entry_usuario.get()
        password = entry_contrasena.get()

        if not username or not password:
            messagebox.showerror("Error", "Completa todos los campos.")
            return

        conn = conectar_mysql()
        cursor = conn.cursor()
        try:
            cursor.execute("INSERT INTO users (username, password) VALUES (%s, %s)", (username, password))
            conn.commit()
            messagebox.showinfo("Éxito", "Usuario registrado correctamente.")
            registro_window.destroy()
        except mysql.connector.IntegrityError:
            messagebox.showerror("Error", "El usuario ya existe.")
        finally:
            conn.close()

    registro_window = tk.Toplevel()
    registro_window.title("Registrarse")

    ttk.Label(registro_window, text="Nuevo Usuario:").grid(row=0, column=0, padx=10, pady=10)
    entry_usuario = ttk.Entry(registro_window)
    entry_usuario.grid(row=0, column=1)

    ttk.Label(registro_window, text="Contraseña:").grid(row=1, column=0, padx=10, pady=10)
    entry_contrasena = ttk.Entry(registro_window, show="*")
    entry_contrasena.grid(row=1, column=1)

    ttk.Button(registro_window, text="Registrar", command=guardar_usuario).grid(row=2, column=0, columnspan=2, pady=10)

# Obtener los generos disponibles
def genre ():
    query = "MATCH (t:Title) RETURN DISTINCT t.`top genre` AS genre ORDER BY genre"
    with driver.session() as session:
        result = session.run(query)
        return [record["genre"] for record in result if record["genre"]]

# Obtener valores unicos por los generos en el dropdown
def valores_genero(genre):
    query = """
    MATCH (t:Title)
    WHERE t.`top genre` = $genre
    RETURN DISTINCT t.bpm AS bpm, t.dnce AS dnce, t.val AS val
    """
    with driver.session() as session:
        result = session.run(query, genre=genre)
        bpms, dnces, vals = set(), set(), set()
        for record in result:
            if record["bpm"] is not None:
                bpms.add(int(record["bpm"]))
            if record["dnce"] is not None:
                dnces.add(int(record["dnce"]))
            if record["val"] is not None:
                vals.add(int(record["val"]))
        return sorted(bpms), sorted(dnces), sorted(vals)

# Buscar recomendaciones
def recomendaciones1(genre, dance, valence, bpm):
    query = """
    MATCH (t:Title)
    WHERE t.`top genre` = $genre
      AND abs(t.dnce - $dance) <= 30
      AND abs(t.val - $valence) <= 30
      AND abs(t.bpm - $bpm) <= 30
    WITH t, (
        abs(t.dnce - $dance) +
        abs(t.val - $valence) +
        abs(t.bpm - $bpm)
    ) AS distancia
    RETURN t.title AS title
    ORDER BY distancia ASC
    LIMIT 25
    """
    with driver.session() as session:
        results = session.run(query, genre=genre, dance=dance, valence=valence, bpm=bpm)
        return [record["title"] for record in results]

# Actualizar dropdowns al cambiar género
def actualizar_dropdowns(event=None):
    genre = genre_var.get()
    if not genre:
        return
    bpms, dnces, vals = valores_genero(genre)

    bpm_dropdown["values"] = bpms or [0]
    dance_dropdown["values"] = dnces or [0]
    valence_dropdown["values"] = vals or [0]

    if bpms:
        bpm_var.set(bpms[0])
    if dnces:
        dance_var.set(dnces[0])
    if vals:
        valence_var.set(vals[0])

# Buscar canciones al presionar botón
def buscar():
    genre = genre_var.get()
    try:
        dance = int(dance_var.get())
        valence = int(valence_var.get())
        bpm = int(bpm_var.get())
    except ValueError:
        messagebox.showerror("Error", "Selecciona valores válidos.")
        return

    recomendaciones = recomendaciones1 (genre, dance, valence, bpm)
    result_text.delete(1.0, tk.END)
    if recomendaciones:
        result_text.insert(tk.END, "Recomendaciones encontradas:\n\n")
        for title in recomendaciones:
            result_text.insert(tk.END, f"- {title}\n")
    else:
        result_text.insert(tk.END, "No se encontraron recomendaciones para esos parámetros.")

# inicia la aplicación principal
def launch():
    global genre_var, genre_dropdown, dance_var, dance_dropdown
    global valence_var, valence_dropdown, bpm_var, bpm_dropdown, result_text

    root = tk.Tk()
    root.title("Recomendador Musical")

    frame = ttk.Frame(root, padding="10")
    frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

    # Dropdown de género
    ttk.Label(frame, text="Género (top genre):").grid(row=0, column=0, sticky=tk.W)
    genre_var = tk.StringVar()
    genre_dropdown = ttk.Combobox(frame, textvariable=genre_var, state="readonly", width=30)
    genre_dropdown.grid(row=0, column=1)
    genre_dropdown["values"] = genre()
    genre_dropdown.bind("<<ComboboxSelected>>", actualizar_dropdowns)

    # Dropdowns
    ttk.Label(frame, text="Danceability:").grid(row=1, column=0, sticky=tk.W)
    dance_var = tk.StringVar()
    dance_dropdown = ttk.Combobox(frame, textvariable=dance_var, state="readonly", width=30)
    dance_dropdown.grid(row=1, column=1)

    ttk.Label(frame, text="Valence:").grid(row=2, column=0, sticky=tk.W)
    valence_var = tk.StringVar()
    valence_dropdown = ttk.Combobox(frame, textvariable=valence_var, state="readonly", width=30)
    valence_dropdown.grid(row=2, column=1)

    ttk.Label(frame, text="BPM:").grid(row=3, column=0, sticky=tk.W)
    bpm_var = tk.StringVar()
    bpm_dropdown = ttk.Combobox(frame, textvariable=bpm_var, state="readonly", width=30)
    bpm_dropdown.grid(row=3, column=1)

    # Botón de búsqueda
    search_button = ttk.Button(frame, text="Buscar Recomendaciones", command=buscar)
    search_button.grid(row=4, column=0, columnspan=2, pady=10)

    # Área de resultados
    result_text = tk.Text(root, wrap=tk.WORD, height=15, width=60)
    result_text.grid(row=1, column=0, padx=10, pady=10)

    root.mainloop()

# Iniciar con login
login()
