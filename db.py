import sqlite3
import hashlib

def conectar_bbdd():
    conn = sqlite3.connect("taletable.db")
    conn.execute("PRAGMA foreign_keys = ON")#Para poder hacer ON DELETE CASCADE
    return conn, conn.cursor()


def crear_tablas(conn, cursor):
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS usuarios (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nombre TEXT NOT NULL UNIQUE,
        f_nacimiento DATE NOT NULL
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS cuentos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        id_usuario INTEGER,
        idioma TEXT NOT NULL,
        hash TEXT NOT NULL UNIQUE,           
                   
        FOREIGN KEY (id_usuario)
            REFERENCES usuarios(id)
            ON DELETE CASCADE      
    )
    """)

    conn.commit()

def recuperar_usuario(cursor, nombre):
    sql_select = f"""
        SELECT id FROM usuarios 
        WHERE nombre = ?
        """
    cursor.execute(sql_select, (nombre,))
    fila = cursor.fetchone()

    if fila is None:
        return None
    
    return fila[0]

def crear_usuario(conn, cursor, nombre, f_nacimiento):
    with conn:
        cursor.execute("INSERT INTO usuarios (nombre, f_nacimiento) VALUES (?, ?)", (nombre, f_nacimiento))
        id_usuario = cursor.lastrowid
    return id_usuario


def recuperar_cuento(cursor, id_usuario, hash_cuento):
    sql = """
        SELECT id FROM cuentos
        WHERE id_usuario = ? AND hash = ?
        """
    
    cursor.execute(sql, (id_usuario, hash_cuento))
    resultado = cursor.fetchone()
    if resultado is None:
        return None
    return resultado[0]


def generar_hash_cuento(id_usuario, elementos):
    #Se ordenan los elementos y se pasan a minusculas
    personajes = sorted(str(p).lower() for p in elementos["personajes"])
    objetos = sorted(str(o).lower() for o in elementos["objetos"])
    lugares = sorted(str(l).lower() for l in elementos["lugares"])
    elementos_str = (
        str(id_usuario) + "|" +
        "|".join(personajes) + "|" +
        "|".join(objetos) + "|" +
        "|".join(lugares) + "|" +
        elementos["idioma"].lower()
    )
    
    #Se genera el hash
    return hashlib.sha256(elementos_str.encode("utf-8")).hexdigest()


def crear_cuento(conn, cursor, id_usuario, elementos):  
    hash_cuento = generar_hash_cuento(id_usuario, elementos)
    with conn:
        cursor.execute("INSERT INTO cuentos (id_usuario, idioma, hash) VALUES (?, ?, ?)", (id_usuario, elementos["idioma"], hash_cuento))
        id_cuento = cursor.lastrowid
    #No se hace conn.commit() porque ya se hace automaticamente en el contexto del with
    #Si se genera una excepcion se controla en el codigo que llama a esta funcion
    return id_cuento


def recuperar_cuento(cursor, id_usuario, elementos):
    hash_cuento = generar_hash_cuento(id_usuario, elementos)
    sql = """
    SELECT id FROM cuentos
    WHERE id_usuario = ? AND hash = ?
    """
    cursor.execute(sql, (id_usuario, hash_cuento))
    resultado = cursor.fetchone()
    if resultado is None:
        return None
    return resultado[0]

    
def cuentos_usuario(cursor, id_usuario):
    cursor.execute("SELECT id FROM cuentos WHERE id_usuario = ?", (id_usuario,))
    return cursor.fetchall() #Si no hay ningun cuento devuelve una lista vacia

def cuento_aleatorio(cursor, id_usuario):
    cursor.execute("SELECT id FROM cuentos WHERE id_usuario = ? ORDER BY RANDOM() LIMIT 1", (id_usuario,))
    fila = cursor.fetchone()
    if fila is None:
        return None
    return fila[0]
