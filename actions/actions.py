# This files contains your custom actions which can be used to run
# custom Python code.
#
# See this guide on how to implement these action:
# https://rasa.com/docs/rasa/custom-actions


# This is a simple example for a custom action which utters "Hello World!"

from typing import Any, Text, Dict, List

#
from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher

#
#

# i see domain is not working probably rasa_sdk modules were not imported
class ActionSaveConversation(Action):
    def name(self) -> Text:
        return "action_save_conversation"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> List[Dict[Text, Any]]:

        print(tracker.event)

        dispatcher.utter_message(text="All Chats saved")

        return []
