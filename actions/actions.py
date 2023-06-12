# This files contains your custom actions which can be used to run
# custom Python code.
#
# See this guide on how to implement these action:
# https://rasa.com/docs/rasa/custom-actions

# This is a simple example for a custom action which utters "Hello World!"
import datetime as dt
import os 
import requests 
import re
import json

from typing import Any, Text, Dict, List, Union
from rasa_sdk import Action, Tracker
from dotenv import load_dotenv
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.events import SlotSet
from rasa_sdk.events import AllSlotsReset
from nltk.corpus import stopwords
from datetime import datetime, time, timedelta

class ActionDefaultFallback(Action):
    def name(self) -> Text:
        return "action_default_fallback"

    def run(
    self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict
    ) -> List[Dict[Text, Any]]:

        dispatcher.utter_message(template="utter_fallback") # respond with utterance
        return []

class ActionShowTime(Action):
    
    def name(self) -> Text:
        return "action_show_time"

    def run(self, dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        hora_actual = dt.datetime.now().time()

        hours = hora_actual.strftime("%H:%M:%S")

        dispatcher.utter_message(text="La hora actualmente es: "+f"{hours}")

        return []

class ActionAskWeather(Action):

    def get_action_before_action_listen(self, tracker: Tracker):
        latest_actions = []
        for e in tracker.events:
            if e['event'] == 'action':
                latest_actions.append(e)

        if len(latest_actions) > 1:
            return latest_actions[-3]['name']
        else:
            return None

    def name(self) -> Text:
        return "action_ask_weather"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        # consultamos la API https://openweathermap.org/current
        user_input = tracker.latest_message['text']
        user_input_v2 = user_input.split()
        if len(tracker.latest_message['entities']) == 0:
            dispatcher.utter_message(text="Creo que te hace falta el lugar, podrías formular tu solicitud de nuevo?")
        else:
            if len(user_input_v2) == 1:
                dispatcher.utter_message(text="Lo siento no entendí, podrías formular tu solicitud de nuevo?")
            else:
                city_name = tracker.get_slot('canton')
                regex_climate = r"\b(s[oó]l|ll[oó]viendo|calor|fr[ií]o|soleado|temperatura|clima|clim[aá]tico)\b"
                match_climate = re.search(regex_climate, user_input)
                intent = tracker.latest_message['intent'].get('name')

                if city_name is None: # if match_climate:
                    # send a default message to the user
                    dispatcher.utter_message(text="Lo siento no entendí, podrías formular tu solicitud de nuevo?")
                else:
                    action_name = self.get_action_before_action_listen(tracker)
                    print(action_name)
                    if match_climate or action_name == "action_ask_weather":
                        load_dotenv()
                        api_key = os.getenv("WEATHER_API_KEY")
                        state_code = ''
                        country_code = 'EC'
                        lang = 'es'
                        units = 'metric'
                    
                        payload = { 'q': f'{city_name},{state_code},{country_code}', 
                            'appid': api_key,
                            'lang': lang,
                            'units': units
                            }

                        r = requests.get(
                                    'http://api.openweathermap.org/data/2.5/weather?',
                                    params=payload
                                    )
                        response = r.json()

                        if response.get('sys', {}).get('country') != 'EC':
                            message = 'La ciudad no existe o no se encuentra en los límites de Manabí'
                        elif response.get('cod') == 200:
                            T_max = response['main']['temp_max']
                            T_min = response['main']['temp_min']
                            weather = response['weather'][0]['description']
                            message = f"Según mi informacion, en el cantón {city_name}"
                            message += f" tendremos un clima con {weather}, "
                            message += f"y una temperatura entre {T_min} y {T_max} °C."
                        else:
                            message = 'Lo siento, no encontré información disponible.'
                        dispatcher.utter_message(text=message)

                    else:   
                        dispatcher.utter_message(text="Lo siento no sé de que estas hablando, podrías reformular tu solicitud?") 

                        # Lo siento no entendí, podrías formular tu solicitud de nuevo?"
                        

                return [SlotSet("canton", city_name)]

class ActionAskTeacher(Action):

    def name(self) -> Text:
        return "action_ask_teacher"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        name = tracker.get_slot('nombre')
        name = name.upper()

        # Consultar la API para obtener la respuesta
        r = requests.get('http://localhost:57032/api/reserva')
        response = r.json()

        conteo_nombres = 0  # Inicializar el conteo en 0
        aulas_disponibles = []
        decode = {
        'Monday': 'Lunes',
        'Tuesday': 'Martes',
        'Wednesday': 'Miércoles',
        'Thursday': 'Jueves',
        'Friday': 'Viernes',
        'Saturday': 'Sábado',
        'Sunday': 'Domingo'
        }

        # Recorrer la lista de respuestas
        for respuesta in response:
            value = respuesta['ConfiguracionReserva']
            if isinstance(value, dict) and 'Nombres' in value:
                nombres = value['Nombres']
                if nombres == name:  # Comparar el nombre extraído con los nombres de la respuesta
                    conteo_nombres += 1
                    dia_reserva = value.get('FechaReserva')
                    hora_inicio = value.get('HoraInicio')
                    hora_fin = value.get('HoraFin')
                    apellido = value.get('Apellido')
                    aula = value.get('Aula')
                    if dia_reserva and hora_inicio and hora_fin and aula :
                        aulas_disponibles.append({'FechaReserva':dia_reserva, 'HoraInicio': hora_inicio, 'HoraFin': hora_fin, 'Aula': aula})

        # Construir la respuesta con el conteo de nombres y la lista de aulas disponibles
        respuesta_final = f"Docente {name.capitalize()} {apellido.capitalize()} tiene resevada {conteo_nombres} Aulas.\n\n"
        if conteo_nombres > 0:
            respuesta_final += f"Laboratorios reservador por {name.capitalize()} {apellido.capitalize()}:\n\n"
            for aula_disponible in aulas_disponibles:
                
                dia_reserva = decode.get(aula_disponible['FechaReserva'])
                hora_inicio = aula_disponible['HoraInicio']
                hora_fin = aula_disponible['HoraFin']
                aula = aula_disponible['Aula']
                respuesta_final += f"\nAula: {aula}\nDia: {dia_reserva}\nHora de inicio: {hora_inicio}\nHora de fin: {hora_fin}\n\n"
                # respuesta_final += "\n"

        # Enviar la respuesta al usuario
        dispatcher.utter_message(text=respuesta_final)

        return [AllSlotsReset()]

class ActionAskRoom(Action):

    def name(self) -> Text:
        return "action_ask_room"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        room = tracker.get_slot('aula')
        # Consultar la API para obtener la respuesta
        r = requests.get('http://localhost:57032/api/reserva')
        response = r.json()

        conteo_aula = 0  # Inicializar el conteo en 0
        aulas_disponibles = []
        # Recorrer la lista de respuestas
        for respuesta in response:
            value = respuesta['ConfiguracionReserva']
            if isinstance(value, dict) and 'Aula' in value:
                aulas = value['Aula'].strip()
                if aulas == room:  # Comparar el nombre extraído con los nombres de la respuesta
                    conteo_aula += 1
                    dia_reserva = value.get('FechaReserva')
                    hora_inicio = value.get('HoraInicio')
                    hora_fin = value.get('HoraFin')
                    name = value.get('Nombres')
                    apellido = value.get('Apellido')
                    if dia_reserva and hora_inicio and hora_fin and name and apellido :
                        aulas_disponibles.append({'FechaReserva':dia_reserva, 'HoraInicio': hora_inicio, 'HoraFin': hora_fin, 'Nombres': name, 'Apellido': apellido})

        # Construir la respuesta con el conteo de nombres y la lista de aulas disponibles
        respuesta_final = f"El {room} ha sido reservado {conteo_aula} veces.\n\n"
        if conteo_aula > 0:
            # respuesta_final += f"Laboratorios reservador por {name.capitalize()} {apellido.capitalize()}:\n\n"
            for aula_disponible in aulas_disponibles:
                
                dia_reserva = aula_disponible['FechaReserva']
                hora_inicio = aula_disponible['HoraInicio']
                hora_fin = aula_disponible['HoraFin']
                name = aula_disponible['Nombres']
                apellido = aula_disponible['Apellido']
                respuesta_final += f"\n El {room}\n fue reservado por: {name.capitalize()} {apellido.capitalize()}\n el dia: {dia_reserva}\n a las {hora_inicio}\n y finaliza el: {hora_fin}\n\n"

        # Enviar la respuesta al usuario
        dispatcher.utter_message(text=respuesta_final)

        return [AllSlotsReset()]

class ActionAskTimeRoom(Action):
    def name(self) -> Text:
        return "action_ask_time_room"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
            
        aula = tracker.get_slot('aula')
        tiempo = tracker.get_slot('tiempo')
        # Aquí puedes llamar a tu API de reserva de aulas y obtener la información de reservas
        ## Formato de hora: "horas:minutos:segundos"
        # Por ahora, asumamos que tenemos una respuesta de la API en forma de un JSON
        r = requests.get('http://localhost:57032/api/reserva')
        response = r.json()
        
        # Buscamos si hay una reserva para el aula y tiempo solicitados
        reservas_aula = []
        for reserva in response:
            aula_reserva = reserva["ConfiguracionReserva"]["Aula"].strip()
            hora_inicio_str = reserva["ConfiguracionReserva"]["HoraInicio"]
            hora_fin_str = reserva["ConfiguracionReserva"]["HoraFin"]
            nombre_reserva = f"{reserva['ConfiguracionReserva']['Nombres']} {reserva['ConfiguracionReserva']['Apellido']}"
            hora_inicio = datetime.strptime(hora_inicio_str, "%H:%M:%S").time()
            hora_fin = datetime.strptime(hora_fin_str, "%H:%M:%S").time()

            if aula_reserva == aula:
                reservas_aula.append({"HoraInicio": hora_inicio, "HoraFin": hora_fin, "Nombres": nombre_reserva})

        # Verificamos si el aula está disponible en el tiempo solicitado
        disponible = True
        reservas_previas = []
        tiempo_datetime = datetime.strptime(tiempo, "%H:%M:%S").time()
        nombre_reserva = ""
        for reserva in reservas_aula:
            hora_inicio = reserva["HoraInicio"]
            hora_fin = reserva["HoraFin"]
            if (hora_inicio <= tiempo_datetime < hora_fin):
                disponible = False
                reservas_previas.append(reserva)
        
        if disponible:
            respuesta = f"El aula {aula} está disponible en el tiempo solicitado."
        else:
            respuesta = f"El aula {aula} está ocupada en el tiempo solicitado por:"
            for reserva in reservas_previas:
                nombre_reserva = reserva["Nombres"]
                hora_inicio = reserva["HoraInicio"]
                hora_fin = reserva["HoraFin"]
                respuesta += f"\n- {nombre_reserva}, reservado de {hora_inicio.strftime('%H:%M')} a {hora_fin.strftime('%H:%M')}"

        dispatcher.utter_message(text=respuesta)
        
        return [SlotSet("aula", aula), SlotSet("tiempo", tiempo)]

class ActionDayTime(Action):
    def name(self) -> Text:
        return "action_day_time"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        # Obtener los valores de las entidades "dia" y "tiempo" del tracker
        dia = tracker.get_slot('dia')
        tiempo = tracker.get_slot('tiempo')
        
        # Obtener el día actual si no se especificó un día en la pregunta
        if not dia:
            ahora = datetime.now()
            dia_actual = ahora.strftime("%A")
        else:
            dia_actual = dia
        
        # Obtener la hora actual si no se especificó un tiempo en la pregunta
        if not tiempo:
            ahora = datetime.now()
            hora_actual = ahora.strftime("%H:%M:%S")
        else:
            hora_actual = tiempo
        
        # Obtener todas las reservas del JSON (aquí puedes reemplazarlo por tu lógica de llamada a la API)
        r = requests.get('http://localhost:57032/api/reserva')
        response = r.json()
        
        # Verificar la disponibilidad de todas las aulas en el día y hora especificados
        aulas_disponibles = set()
        proximas_reservas = []
        
        decode = {
        'Monday': 'Lunes',
        'Tuesday': 'Martes',
        'Wednesday': 'Miercoles',
        'Thursday': 'Jueves',
        'Friday': 'Viernes',
        'Saturday': 'Sabado',
        'Sunday': 'Domingo'
        }
        print(hora_actual)
        for reserva in response:
            dia_reserva = decode.get(reserva["ConfiguracionReserva"]["FechaReserva"])
            hora_inicio_reserva = reserva["ConfiguracionReserva"]["HoraInicio"]
            hora_fin_reserva = reserva["ConfiguracionReserva"]["HoraFin"]
            aula_reserva = reserva["ConfiguracionReserva"]["Aula"].strip()

            if dia_actual.lower() == dia_reserva.lower():
                if not (hora_inicio_reserva <= hora_actual < hora_fin_reserva):
                    aulas_disponibles.add(aula_reserva)
                    print (aulas_disponibles)
            if dia_actual.lower() <= dia_reserva.lower() and hora_inicio_reserva >= hora_actual:
                proximas_reservas.append({"aula": aula_reserva, "hora_inicio": hora_inicio_reserva, "hora_fin": hora_fin_reserva})
        
        # Generar la respuesta en base a la disponibilidad de las aulas y las próximas reservas
        respuesta = ""
        tiempo = datetime.strptime(tiempo, "%H:%M:%S").time()
        if len(aulas_disponibles) > 0:
            respuesta += f"Las siguientes aulas están disponibles {dia_actual} a las {hora_actual}: {', '.join(aulas_disponibles)}\n"
        else:
            respuesta += f"No hay aulas disponibles {dia_actual} a las {hora_actual}.\n"
        
        if len(proximas_reservas) > 0:
            respuesta += "Las próximas reservas son:\n"
            for reserva in proximas_reservas:
                aula = reserva["aula"]
                hora_inicio = reserva["hora_inicio"]
                hora_fin = reserva["hora_fin"]
                respuesta += f"- Aula {aula}: de {hora_inicio} a {hora_fin}\n"
        else:
            respuesta += "No hay próximas reservas.\n"
        
        dispatcher.utter_message(text=respuesta)
        
        return []


