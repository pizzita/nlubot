import os
from flask import Flask, request
import json
import rasa

import os

def get_latest_model_path():
    models_directory = "/models"
    latest_model = max(os.listdir(models_directory))
    latest_model_path = os.path.join(models_directory, latest_model, "tar.gz")
    return latest_model_path

# Crear una instancia de la aplicación Flask
app = Flask(__name__)

# Crear una instancia del bot de Rasa
bot = get_latest_model_path()
# Definir la ruta de la API para procesar solicitudes de usuarios
@app.route('/webhook', methods=['POST'])
def webhook():
    # Obtener el mensaje del usuario desde la solicitud POST
    message = request.json['message']

    # Procesar el mensaje con el bot de Rasa
    response = bot.process_message(message)

    # Enviar la respuesta del bot al usuario
    return json.dumps(response)

# Configurar el servidor Flask para que escuche en el puerto 5000
if __name__ == 'main':
    app.run(port=5005)