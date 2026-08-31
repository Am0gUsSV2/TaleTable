import serial
import time
import google.generativeai as genai
import os
import random
from gtts import gTTS
from read import read_tag
from db import cuento_aleatorio, recuperar_cuento, crear_cuento, recuperar_usuario,crear_usuario, crear_tablas, conectar_bbdd
from pathlib import Path
import shutil
import subprocess
import json


def introducir_elementos(nombre_usuario, tipo, max_elementos, arduino):
    i = 0
    insert = False
    elementos_a_devolver = set()
    while i < max_elementos:
        subprocess.run(["mpg123", f"{SYSTEM_AUDIOS_FOLDER}/1_{tipo}.mp3"])
        print(f"Introduce la ficha de {tipo}, si quieres dejar de introducir elementos pon la ficha de continuar") #1 AUDIO
        objeto_dict = None
        try:
            while not objeto_dict:
                objeto_dict = read_tag(arduino)
                time.sleep(1)

            clave, valor = list(objeto_dict.items())[0]
            print(f"Clave extraída: {clave}, Valor extraído: {valor}")
            #Comprobacion de que la etiqueta que se esta poniendo es del tipo que se pide
            if clave == tipo:                       
                before_length = len(elementos_a_devolver)
                elementos_a_devolver.add(valor)
                after_length = len(elementos_a_devolver)

                if before_length < after_length: #Comprobacion de si se ha aniadido algo nuevo y si es asi se avanza el contador
                    subprocess.run(["mpg123", f"{SYSTEM_AUDIOS_FOLDER}/19.mp3"])
                    print(f"Añadido nuevo elemento del tipo {tipo} con valor {valor}") #19 AUDIO
                    i = i+1
                else:
                    subprocess.run(["mpg123", f"{SYSTEM_AUDIOS_FOLDER}/2.mp3"])
                    print("La ficha introducida ya habia sido registrada anteriormente") #2 AUDIO
            
            elif clave == "nombre" and tipo == "personajes":
                if valor != nombre_usuario:
                    subprocess.run(["mpg123", f"{SYSTEM_AUDIOS_FOLDER}/3.mp3"])
                    print("Esa no es tu ficha! Asegurate de poner tu ficha si quieres se parte del cuento")#3 AUDIO
                elif not insert:
                    subprocess.run(["mpg123", f"{SYSTEM_AUDIOS_FOLDER}/4.mp3"])
                    print("Vaya, parece que quieres ser parte del cuento!") #4 AUDIO
                    elementos_a_devolver.add(valor)
                    insert = True
                    i = i + 1
                else:
                    subprocess.run(["mpg123", f"{SYSTEM_AUDIOS_FOLDER}/5.mp3"])
                    print("Ya eres parte del cuento!") #5 AUDIO
            
            elif clave == "comando" and valor == "continuar":
                subprocess.run(["mpg123", f"{SYSTEM_AUDIOS_FOLDER}/6.mp3"])
                print("continuando") #6 AUDIO
                return elementos_a_devolver
            
            else:
                subprocess.run(["mpg123", f"{SYSTEM_AUDIOS_FOLDER}/7_{tipo}.mp3"])
                print(f"Advertencia: La ficha introducida no es del tipo {tipo}") #7 AUDIO
        
        except (ValueError, SyntaxError):
            print(f"[DEBUG] Error: La línea no tiene un formato de diccionario válido.")
    
    return elementos_a_devolver

try:
    #Cargar el json de configuracion
    #Si el fichero no existe produce excepcion
    with open("config.json", "r", encoding="utf-8") as f:
        config_dict = json.load(f)

    PUERTO = config_dict["puerto"]
    BAUDIOS = config_dict["baudios"]
    TIMEOUT = config_dict["timeout"]
    MAX_PERSONAJES = config_dict["max_personajes"]
    MAX_OBJETOS = config_dict["max_objetos"]
    MAX_LUGARES = config_dict["max_lugares"]
    IDIOMA_DEFAULT = config_dict["idioma_default"]
    MAX_INTENTOS_LOGIN = config_dict["intentos_login"]
    SYSTEM_AUDIOS_FOLDER = config_dict["system_audios_folder"]

    arduino = None
    #Se borran los cuentos si la base de datos no existe
    if not Path("taletable.db").is_file():
        shutil.rmtree("Tales", ignore_errors=True)

    # Conexion a la base de datos
    conn, cursor = conectar_bbdd()

    # Crear tablas
    crear_tablas(conn, cursor)

    # configuracion API gemini
    api_key = os.environ["GEMINI_API_KEY"]
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-2.5-flash')  

    # Conectar y leer del Arduino
    print(f"Conectando al puerto {PUERTO} a {BAUDIOS} baudios...")
    arduino = serial.Serial(PUERTO, BAUDIOS, timeout=TIMEOUT)
    time.sleep(2)
    print("[DEBUG] Arduino conectado. Esperando datos...\nPresiona Ctrl+C para salir.\n")
    i = 0
    elementos = {"personajes": set(), "objetos": set(), "lugares": set(), "idioma": None}
    
    #Login del usuario
    logged = False
    new_user = False
    id_usuario = False
    subprocess.run(["mpg123", f"{SYSTEM_AUDIOS_FOLDER}/bienvenida.mp3"])
    print("bienvenida") # bienvenida AUDIO
    subprocess.run(["mpg123", f"{SYSTEM_AUDIOS_FOLDER}/inicio.mp3"])
    print("inicio") # inicio AUDIO
    subprocess.run(["mpg123", f"{SYSTEM_AUDIOS_FOLDER}/8.mp3"])
    print("Introduce la ficha del usuario:") #8 AUDIO
    i = 0
    #LOGIN DEL USUARIO
    while not logged and i < MAX_INTENTOS_LOGIN:
        try:
            user_dict = None
            while not user_dict:
                user_dict = read_tag(arduino)
                time.sleep(1)
            print("pasado la lectura de usuario")

            if user_dict:
                #comprobar que la ficha introducida es una de usuario
                if "nombre" not in user_dict or "f_nacimiento" not in user_dict:
                    subprocess.run(["mpg123", f"{SYSTEM_AUDIOS_FOLDER}/9.mp3"])
                    print("La ficha introducida no es de un usuario, asegurate de que pones tu ficha") #9 AUDIO
                else:
                    try:
                        id_usuario = recuperar_usuario(cursor, user_dict["nombre"])
                        if id_usuario is None:
                            id_usuario = crear_usuario(conn, cursor, user_dict["nombre"], user_dict["f_nacimiento"])
                            subprocess.run(["mpg123", f"{SYSTEM_AUDIOS_FOLDER}/10.mp3"])
                            print("Hola usuario creado!") #10 AUDIO
                        else:
                            subprocess.run(["mpg123", f"{SYSTEM_AUDIOS_FOLDER}/11.mp3"])
                            print("Hola usuario existente!") #11 AUDIO
                        logged = True
                    except Exception as e:
                        print(f"Ocurrió un error al crear el usuario: {e}")
                        subprocess.run(["mpg123", f"{SYSTEM_AUDIOS_FOLDER}/12.mp3"])
                        print("Hubo un error al crear tu usuario, intentalo de nuevo") #12 AUDIO

        except (ValueError, SyntaxError):
            print(f"Error: La línea recibida no tiene un formato de diccionario válido.")

        i = i + 1
    
    if i == MAX_INTENTOS_LOGIN:
        raise Exception("[DEBUG] Numero maximo de intentos de login excedidos")
    
    subprocess.run(["mpg123", f"{SYSTEM_AUDIOS_FOLDER}/solicitar_tutorial.mp3"])
    print("Introduce la ficha de tutorial si quieres escucharlo, sino la de continuar") # solicitar_tutorial AUDIO

    #TUTORIAL
    continuar = None
    while continuar == None:
        try:
            objeto_dict = None
            while not objeto_dict:
                objeto_dict = read_tag(arduino)
                time.sleep(1)

        except (ValueError, SyntaxError):
            print(f"[DEBUG] Error: La línea no tiene un formato de diccionario válido.")
            subprocess.run(["mpg123", f"{SYSTEM_AUDIOS_FOLDER}/14.mp3"])
            print("Eso no es una ficha valida, intentalo de nuevo") #14 AUDIO

        clave, valor = list(objeto_dict.items())[0]
        if clave == "comando":
            if valor == "tutorial":
                #Si la ficha es de tutorial
                continuar = True
                subprocess.run(["mpg123", f"{SYSTEM_AUDIOS_FOLDER}/tutorial.mp3"])
                print("TUTORIAL TaleTable es...") # tutorial AUDIO
            elif valor == "continuar":
                #Si la ficha es de continuar
                continuar = True
        else:
            #Si es otra ficha
            subprocess.run(["mpg123", f"{SYSTEM_AUDIOS_FOLDER}/ficha_desconocida_tutorial.mp3"])
            print("La ficha introducida no es de tutorial o de continuar, intentalo de nuevo") #ficha_desconocida_tutorial AUDIO 

    #ALEATORIO O CONTINUAR
    subprocess.run(["mpg123", f"{SYSTEM_AUDIOS_FOLDER}/13.mp3"])
    print("Si quieres escuchar algun cuento tuyo de forma aleatoria es momento de poner la ficha, sino pon la de continuar")#13 AUDIO
    rand = None
    while rand == None:
        try:
            objeto_dict = None
            while not objeto_dict:
                objeto_dict = read_tag(arduino)
                time.sleep(1)

        except (ValueError, SyntaxError):
            print(f"[DEBUG] Error: La línea no tiene un formato de diccionario válido.")
            subprocess.run(["mpg123", f"{SYSTEM_AUDIOS_FOLDER}/14.mp3"])
            print("Eso no es una ficha valida, intentalo de nuevo") #14 AUDIO

        clave, valor = list(objeto_dict.items())[0]
        if clave == "comando":
            if valor == "aleatorio":
                rand = True
            elif valor == "continuar":
                rand = False
        else:
            subprocess.run(["mpg123", f"{SYSTEM_AUDIOS_FOLDER}/15.mp3"])
            print("La ficha introducida no es de cuento aleatorio o de continuar, intentalo de nuevo") #15 AUDIO

    if rand:
        id_cuento = cuento_aleatorio(cursor, id_usuario)
        if id_cuento is None:
            subprocess.run(["mpg123", f"{SYSTEM_AUDIOS_FOLDER}/16.mp3"])
            print("Vaya, parece que no tienes cuentos para elegir!") #16 AUDIO
            raise Exception("[DEBUG] El usuario no tiene cuentos para elegir uno aleatorio")

    else:  
        #Introduccion de personajes
        for tipo, max_elementos in [("personajes", MAX_PERSONAJES), ("objetos", MAX_OBJETOS), ("lugares", MAX_LUGARES), ("idioma", 1)]:
            elementos[tipo] = introducir_elementos(user_dict["nombre"], tipo=tipo, max_elementos=max_elementos, arduino=arduino)
            
        # Introduccion de valores por defecto en caso de que el usuario no introduzca valores de algun campo
        for clave, valor in elementos.items():
            if not valor:

                if clave == "personajes":
                        personajes = random.sample(config_dict["personajes_default"], MAX_PERSONAJES) # obtener x elementos del set sin repeticion https://www.geeksforgeeks.org/python/randomly-select-elements-from-list-without-repetition-in-python/
                        elementos[clave].update(personajes)

                elif clave == "objetos":
                        objetos = random.sample(config_dict["objetos_default"], MAX_OBJETOS)
                        elementos[clave].update(objetos)

                elif clave == "lugares":
                        lugares = random.sample(config_dict["lugares_default"], MAX_LUGARES)
                        elementos[clave].update(lugares)

                elif clave == "idioma":
                        elementos[clave] = IDIOMA_DEFAULT

        try:
            id_cuento = recuperar_cuento(cursor, id_usuario, elementos)
        except Exception as e:
            print(f"[DEBUG] Ocurrió un error al crear el cuento: {e}") 
            subprocess.run(["mpg123", f"{SYSTEM_AUDIOS_FOLDER}/error_crear_recuperar_cuento.mp3"])
            print("Hubo un error al crear tu cuento, intentalo de nuevo") #error_crear_recuperar_cuento AUDIO   
                
        if id_cuento is None:
            # Generar el cuento infantil
            if user_dict["nombre"] in elementos["personajes"]:
                # prompt si el usuario es protagonista del cuento
                prompt = (
                    f"Escribe un cuento infantil mágico, entretenido y con un final feliz. "
                    f"La estructura debe ser clásica: una introducción que presente el mundo, una pequeña aventura o reto, y un desenlace con una moraleja positiva. "
                    f"Utiliza un vocabulario sencillo, frases cortas y fluidas, y un tono muy cariñoso. "
                    f"Los personajes de la historia son: {', '.join(elementos['personajes'])}. "
                    f"Los objetos clave que deben aparecer son: {', '.join(elementos['objetos'])}. "
                    f"Los lugares donde transcurre la aventura son: {', '.join(elementos['lugares'])}. "
                    f"El protagonista absoluto y héroe de la historia es {user_dict['nombre']}. "
                    f"Ten en cuenta que {user_dict['nombre']} nació el {user_dict['f_nacimiento']}, así que adapta el nivel del cuento a su edad aproximada. "
                    f"El idioma del cuento debe ser {elementos['idioma']}. "
                    f"REGLA ESTRICTA DE FORMATO: Devuelve ÚNICAMENTE el cuento en texto plano. No uses negritas, ni asteriscos, ni caracteres especiales. "
                    f"No incluyas saludos, ni encabezados, ni confirmaciones tuyas. La primera línea debe ser el título del cuento y luego un salto de línea."
                )

            else:
                # prompt si el usuario no es personaje del cuento
                prompt = (
                    f"Escribe un cuento infantil mágico, entretenido y con un final feliz. "
                    f"La estructura debe ser clásica: una introducción que presente el mundo, una pequeña aventura o reto, y un desenlace con una moraleja positiva. "
                    f"Utiliza un vocabulario sencillo, frases cortas y fluidas, y un tono muy cariñoso. "
                    f"Los personajes principales de la historia son: {', '.join(elementos['personajes'])}. "
                    f"Los objetos clave que deben aparecer son: {', '.join(elementos['objetos'])}. "
                    f"Los lugares donde transcurre la aventura son: {', '.join(elementos['lugares'])}. "
                    f"Ten en cuenta que la persona a la que va dirigido el cuento nació el {user_dict['f_nacimiento']}, así que adapta el nivel del cuento a su edad aproximada. "
                    f"El idioma del cuento debe ser {elementos['idioma']}. "
                    f"REGLA ESTRICTA DE FORMATO: Devuelve ÚNICAMENTE el cuento en texto plano. No uses negritas, ni asteriscos, ni caracteres especiales. "
                    f"No incluyas saludos, ni encabezados, ni confirmaciones tuyas. La primera línea debe ser el título del cuento y luego un salto de línea."
                )

            try:
                print("Generando cuento") #20 AUDIO
                subprocess.run(["mpg123", f"{SYSTEM_AUDIOS_FOLDER}/20.mp3"])

                response = model.generate_content(prompt)
                print("----- Cuento infantil -----")
                cuento_texto = response.text
                print(cuento_texto)
                print("---------------------------")

            except Exception as e:
                raise e

            ruta = Path(f"Tales/{user_dict["nombre"]}/Texto")
            ruta.mkdir(parents=True, exist_ok=True) #Crea la ruta, sus carpetas intermedias y no da error si ya existe

            id_cuento = crear_cuento(conn, cursor, id_usuario, elementos)
            archivo = ruta / f"{id_cuento}.txt"
            archivo.write_text(cuento_texto, encoding="utf-8")

            print("[DEBUG] Texto del cuento guardado correctamente")

            # Generacion del audio del cuento mediante el texto devuelto por Gemini con gTTS https://www.geeksforgeeks.org/python/convert-text-speech-python/
            print("[DEBUG] Generando cuento en audio...")
            cuento_audio = gTTS(text=cuento_texto, lang=elementos["idioma"], slow=False)
            
            ruta = f"Tales/{user_dict["nombre"]}/Audio"
            path = Path(ruta)
            path.mkdir(parents=True, exist_ok=True) #Crea la ruta, sus carpetas intermedias y no da error si ya existe
            #Se guarda el audio
            cuento_audio.save(f"{ruta}/{id_cuento}.mp3")
            print("[DEBUG] Audio del cuento guardado correctamente")

        else:
            print("[DEBUG] El cuento ya existe")

    subprocess.run(["mpg123", f"{SYSTEM_AUDIOS_FOLDER}/17.mp3"])
    print("Ya tenemos el cuento listo! Ahora vamos a escucharlo!") #17 AUDIO
    ruta_audio = f"Tales/{user_dict["nombre"]}/Audio/{id_cuento}.mp3" #Se coge el audio, ya sea recien creado o que ya existiese
    subprocess.run(["mpg123", ruta_audio])
    subprocess.run(["mpg123", f"{SYSTEM_AUDIOS_FOLDER}/18.mp3"])
    print("Que aventura tan divertida! Espero que te haya gustado! Hasta la proxima!") #18 AUDIO

# Excepciones de gemini
except KeyError:
    print("[DEBUG] Error: La variable de entorno GEMINI_API_KEY no está configurada.")
    print("[DEBUG] Por favor, configura la variable de entorno")
    exit()


# Excepciones del JSON
except FileNotFoundError:
    print("[DEBUG] No se encontro el fichero json con la configuracion")

except json.JSONDecodeError:
    print("[DEBUG] El JSON de los elementos default está mal formado")


except serial.SerialException as e:
    print(f"[DEBUG] Error al acceder al puerto serie: {e}")

except KeyboardInterrupt:
    print("[DEBUG] Lectura interrumpida por el usuario.")

except Exception as e:
    print(f"[DEBUG] Ocurrió un error inesperado: {e}")

finally:
    if arduino and arduino.is_open:
        arduino.close()
        print("[DEBUG] Puerto cerrado.") 