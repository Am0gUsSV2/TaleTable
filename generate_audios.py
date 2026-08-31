import json
import os
from gtts import gTTS

def generate_audios(json_file, output_folder):
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
        print(f"Directorio creado: {output_folder}")

    with open(json_file, 'r', encoding='utf-8') as f:
        data = json.load(f)

    for key, value in data.items():
        if isinstance(value, dict):
            for sub_key, text in value.items():
                filename = f"{key}_{sub_key}.mp3"
                filepath = os.path.join(output_folder, filename)
                print(f"Generando: {filename}...")
                tts = gTTS(text=text, lang='es')
                tts.save(filepath)
        else:
            filename = f"{key}.mp3"
            filepath = os.path.join(output_folder, filename)
            print(f"Generando: {filename}...")
            tts = gTTS(text=value, lang='es')
            tts.save(filepath)

if __name__ == "__main__":
    with open("config.json", "r", encoding="utf-8") as f:
        config_dict = json.load(f)

    SYSTEM_AUDIOS_FOLDER = config_dict["system_audios_folder"]
    JSON_PATH = f'{SYSTEM_AUDIOS_FOLDER}/audios.json'
    
    generate_audios(JSON_PATH, SYSTEM_AUDIOS_FOLDER)
    print("Audios generados exitosamente")
