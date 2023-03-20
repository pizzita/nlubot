# This files contains your custom actions which can be used to run
# custom Python code.
#
# See this guide on how to implement these action:
# https://rasa.com/docs/rasa/custom-actions


# This is a simple example for a custom action which utters "Hello World!"
import datetime as dt
import os 
import requests 

from typing import Any, Text, Dict, List
from rasa_sdk import Action, Tracker
from dotenv import load_dotenv
#from rasa_sdk_events import SlotSet 
from rasa_sdk.executor import CollectingDispatcher

class ActionSessionStart(Action):

    def name(self) -> Text:
        return "action_session_start"

    async def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> List[Dict[Text, Any]]:

        dispatcher.utter_message(text="Que gusto saludarte, mi función principal es brindar soporte, puedes:\n -Preguntarme por la hora o el clima\n -Preguntarme por la disponibilidad de laboratorios")

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

    def name(self) -> Text:
        return "action_ask_weather"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        # consultamos la API https://openweathermap.org/current
        
        city_name = tracker.get_slot('canton')
        if city_name is None:
            # send a default message to the user
            dispatcher.utter_message(text="Lo siento no tengo inforamcion del clima de esa cuidad")
        else:
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

            if response.get('cod') == 200:
                T_max = response['main']['temp_max']
                T_min = response['main']['temp_min']
                weather = response['weather'][0]['description']
                message = f"Según mi informacion, en el Cantón: {city_name}"
                message += f" tendremos un clima con: {weather}, "
                message += f"Con temperatura entre {T_min} y {T_max} grados Celsius."
            else:
                message = 'Lo siento, no encontré información disponible.'
            dispatcher.utter_message(text=message)

        return []





