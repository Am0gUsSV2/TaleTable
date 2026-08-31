import ast

def read_tag(arduino):
    linea = arduino.readline().decode('utf-8', errors='replace').strip()
    if linea:
        print(f"Línea recibida (string): {linea}")
        objeto_dict = ast.literal_eval(linea)
        if isinstance(objeto_dict, dict):
            return objeto_dict
        
    return None