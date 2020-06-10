# Dictionary on file
{
    "token": str   
}

import json
import telebot
from telebot import types

class Credentials():
    def __init__(self, filename):
        self.filename = filename
    
    def getCredentials(self):
        """Retrieves dictionary with bot credentials
        
        Returns:
            dict: credentials
        """
        with open("credentials.txt") as file:
            text = file.read()
            credentials = json.loads(text)
        return credentials

class SmartHomeBot():
    """Class to receive commands and communicate via Telegram to manage your SmartHome Controller
    """
    def __init__(self):
        self.credentials = Credentials("credentials.txt").getCredentials()
        self.bot = telebot.TeleBot(self.credentials["token"])
        
        self.empty_markup = types.ReplyKeyboardRemove()
        
        # Gestione menù principale
        self.welcome_message = "Benvenuto nel Bot di gestione del tuo SmartHome Controller!\nScegli una categoria:"
        self.termostato = "Termostato"
        self.illuminazione = "Illuminazione"
        self.antifurto = "Antifurto"
        
        self.welcome_markup = types.ReplyKeyboardMarkup(row_width=1)
        btn_termostato = types.KeyboardButton(self.termostato)
        btn_illuminazione = types.KeyboardButton(self.illuminazione)
        btn_antifurto = types.KeyboardButton(self.antifurto)
        self.welcome_markup.add(btn_termostato, btn_illuminazione, btn_antifurto)
        
        # Gestione menù termostato
        self.termostato_message = "Inserisci la temperatura che vuoi avere in casa (attualmente {}°):"
        self.termostato_error = "Valore non consentito!"
        self.termostato_success = "Valore impostato correttamente."
        # Gestione handlers
        self._handlers()
        
    def _handlers(self):
        """Private method used to initialize handlers for various commands
        """
        @self.bot.message_handler(commands=['start','help'])
        def send_welcome(message):
            self.bot.send_message(message.chat.id, self.welcome_message, reply_markup=self.welcome_markup)
        
        @self.bot.message_handler(regexp=self.termostato)
        def send_termostato(message):
            # Da ottenere con richieste REST
            res = 24
            self.bot.send_message(message.chat.id, self.termostato_message.format(res), reply_markup=self.empty_markup)
            @self.bot.message_handler()
            def manage_temperature(message):
                try:
                    temp = float(message.text)
                    self.bot.send_message(message.chat.id,self.termostato_success)
                    send_welcome(message)
                except:
                    self.bot.send_message(message.chat.id,self.termostato_error)
                    send_termostato(message)
            
        @self.bot.message_handler(regexp=self.illuminazione)
        def send_termostato(message):
            pass
            
        @self.bot.message_handler(regexp=self.antifurto)
        def send_termostato(message):
            pass
    
    def run(self):
        self.bot.polling()

if __name__ == "__main__":
    bot = SmartHomeBot().run()