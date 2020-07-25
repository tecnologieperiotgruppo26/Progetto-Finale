# Dictionary on file
# {
#     "token": str   
# }

import json
import telebot
import requests
from telebot import types

class Credentials():
    def __init__(self, filename):
        self.filename = filename
    
    def getCredentials(self):
        """Retrieves dictionary with bot credentials
        
        Returns:
            dict: credentials
        """
        # Credentials.txt viene omesso in quanto contiene le chiavi private per Telegrams
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
        print("Bot avviato...")
        
        # Variabili
        self.server = "localhost:8080"
        self.serviceID = -1
        self.temp = -1
        self.luci = ""
        self.ant = ""
        
        # Callbacks
        self._WELC = "/start"
        self._TERM = "/termostato"
        self._ILL = "/illuminazione"
        self._ANT = "/antifurto"
        self._TEMP_PLUS = "/tempplus"
        self._TEMP_MINUS = "/tempminus"
        self._ILL_ON = "/luciON"
        self._ILL_OFF = "/luciOFF"
        self._ANT_ON = "/antifurtoON"
        self._ANT_OFF = "/antifurtoOFF"
        
        # Descrizioni
        self.main_menu_message = "Seleziona un servizio:"
        self.termostato_message = "Modifica la temperatura della casa (attualmente {}):"
        self.illuminazione_message = "Lo stato attuale delle luci è {}.\nCambiarlo o uscrire:"
        self.antifurto_message = "Lo stato attuale dell'antifurto è {}.\nCambiarlo o uscrire:"
        
        # WELCOME
        @self.bot.message_handler(commands=['start','help'])
        def _send_welcome(message):
            self.bot.send_message(message.chat.id,self.main_menu_message,reply_markup=self._main_menu_markup())
            self.bot.delete_message(message.chat.id,message.message_id)
            
        @self.bot.callback_query_handler(lambda query: query.data == self._WELC)
        def _send_welcome(call):
            self.bot.answer_callback_query(call.id)
            self.bot.send_message(call.from_user.id,self.main_menu_message,reply_markup=self._main_menu_markup())
            self.bot.delete_message(call.message.chat.id,call.message.message_id)
        
        # TERMOSTATO
        @self.bot.callback_query_handler(lambda query: query.data == self._TERM)
        def _termostato_menu(call):
            self.bot.answer_callback_query(call.id)
            # Per ora l'id è statico, si può implementare una seleizione del singolo dispositivo con un menu
            deviceID = 0
            self.temp = self._getTemperatura(deviceID)
            self.bot.send_message(call.from_user.id,self.termostato_message.format(self.temp),reply_markup=self._termostato_menu_markup())
            self.bot.delete_message(call.message.chat.id,call.message.message_id)
            
        @self.bot.callback_query_handler(lambda query: query.data == self._TEMP_PLUS)
        def _temp_plus(call):
            self.bot.answer_callback_query(call.id)
            self.temp +=1
            self._setTemperatura(self.temp)
            self.bot.send_message(call.from_user.id,self.termostato_message.format(self.temp),reply_markup=self._termostato_menu_markup())
            self.bot.delete_message(call.message.chat.id,call.message.message_id)
            
        @self.bot.callback_query_handler(lambda query: query.data == self._TEMP_MINUS)
        def _temp_minus(call):
            self.bot.answer_callback_query(call.id)
            self.temp -=1
            self._setTemperatura(self.temp)
            self.bot.send_message(call.from_user.id,self.termostato_message.format(self.temp),reply_markup=self._termostato_menu_markup())
            self.bot.delete_message(call.message.chat.id,call.message.message_id)
        
        # ILLUMINAZIONE
        @self.bot.callback_query_handler(lambda query: query.data == self._ILL)
        def _illuminaizione_menu(call):
            self.bot.answer_callback_query(call.id)
            # Per ora l'id è statico, si può implementare una selezione del singolo dispositivo con un menu
            deviceID = 0
            self.luci = self._getLuci(deviceID)
            self.bot.send_message(call.from_user.id,self.illuminazione_message.format(self.luci),reply_markup=self._illuminazione_menu_markup())
            self.bot.delete_message(call.message.chat.id,call.message.message_id)
    
        @self.bot.callback_query_handler(lambda query: query.data == self._ILL_ON)
        def _illuminaizione_menu(call):
            self.bot.answer_callback_query(call.id)
            self.luci = "ON"
            self._setLuci(1)
            self.bot.send_message(call.from_user.id,self.illuminazione_message.format(self.luci),reply_markup=self._illuminazione_menu_markup())
            self.bot.delete_message(call.message.chat.id,call.message.message_id)
        
        @self.bot.callback_query_handler(lambda query: query.data == self._ILL_OFF)
        def _illuminazione_menu(call):
            self.bot.answer_callback_query(call.id)
            self._setLuci(0)
            self.bot.send_message(call.from_user.id,self.illuminazione_message.format(self.luci),reply_markup=self._illuminazione_menu_markup())
            self.bot.delete_message(call.message.chat.id,call.message.message_id)
            
        # ANTIFURTO
        @self.bot.callback_query_handler(lambda query: query.data == self._ANT)
        def _antifurto_menu(call):
            self.bot.answer_callback_query(call.id)
            # Per ora l'id è statico, si può implementare una seleizione del singolo dispositivo con un menu
            deviceID = 0
            self.ant = self._getAntifurto(deviceID)
            self.bot.send_message(call.from_user.id,self.antifurto_message.format(self.ant),reply_markup=self._antifurto_menu_markup())
            self.bot.delete_message(call.message.chat.id,call.message.message_id)
    
        @self.bot.callback_query_handler(lambda query: query.data == self._ANT_ON)
        def _antifurto_menu(call):
            self.bot.answer_callback_query(call.id)
            self.ant = "ON"
            self._setAntifurto(1)
            self.bot.send_message(call.from_user.id,self.antifurto_message.format(self.ant),reply_markup=self._antifurto_menu_markup())
            self.bot.delete_message(call.message.chat.id,call.message.message_id)
        
        @self.bot.callback_query_handler(lambda query: query.data == self._ANT_OFF)
        def _antifurto_menu(call):
            self.bot.answer_callback_query(call.id)
            self.ant = "OFF"
            self._setAntifurto(0)
            self.bot.send_message(call.from_user.id,self.antifurto_message.format(self.ant),reply_markup=self._antifurto_menu_markup())
            self.bot.delete_message(call.message.chat.id,call.message.message_id)
        
        # Registrazione al catalog
        res = requests.post(f"{server}/devices/new")
        self.serviceID = json.loads(res.text)      
            
    def _main_menu_markup(self):
        # Menù principale
        keyboard = [types.InlineKeyboardButton('Termostato', callback_data=self._TERM),
                    types.InlineKeyboardButton('Illuminazione', callback_data=self._ILL),
                    types.InlineKeyboardButton('Antifurto', callback_data=self._ANT)]
        menu = types.InlineKeyboardMarkup()
        for k in keyboard:
            menu.row(k)
        return menu
    
    def _termostato_menu_markup(self):
        keyboard = [types.InlineKeyboardButton('+', callback_data=self._TEMP_PLUS),
                    types.InlineKeyboardButton('-', callback_data=self._TEMP_MINUS),
                    types.InlineKeyboardButton('Esci', callback_data=self._WELC)]
        menu = menu = types.InlineKeyboardMarkup()
        for k in keyboard:
            menu.row(k)
        return menu
    
    def _illuminazione_menu_markup(self):
        keyboard = [types.InlineKeyboardButton('ON', callback_data=self._ILL_ON),
                    types.InlineKeyboardButton('OFF', callback_data=self._ILL_OFF),
                    types.InlineKeyboardButton('Esci', callback_data=self._WELC)]
        menu = menu = types.InlineKeyboardMarkup()
        for k in keyboard:
            menu.row(k)
        return menu
    
    def _antifurto_menu_markup(self):
        keyboard = [types.InlineKeyboardButton('ON', callback_data=self._ANT_ON),
                    types.InlineKeyboardButton('OFF', callback_data=self._ANT_OFF),
                    types.InlineKeyboardButton('Esci', callback_data=self._WELC)]
        menu = menu = types.InlineKeyboardMarkup()
        for k in keyboard:
            menu.row(k)
        return menu
    
    def _getTemperatura(self,deviceID):
        res = requests.get(f"{self.server}/temperature")
        return res
            
    def _getLuci(self,deviceID):
        res = requests.get(f"{self.server}/light")
        if res==1:
            return "ON"
        elif res==0:
            return "OFF"
        else:
            return "NaN"
    
    def _getAntifurto(self,deviceID):
        res = requests.get(f"{self.server}/antifurto")
        if res==1:
            return "ON"
        elif res==0:
            return "OFF"
        else:
            return "NaN"
    
    def _setTemperatura(self,val):
        payload = {'tmp': val}
        requests.post(f"{self.server}/settemperature", data=payload)
        
    def _setLuci(self,val):
        if val==1:
            requests.post(f"{self.server}/luciON")
        elif val==0:
            requests.post(f"{self.server}/luciOFF")
    
    def _setAntifurto(self,val):
        payload = {'val': val}
        requests.post(f"{self.server}/setantifurto", data=payload)
    
    def _segnaleAntifurto(self,deviceID):
        # Mqtt subscriber agli eventi dell'antifurto da implementare come thread a sè che ascolta
        pass
    
    def run(self):
        self.bot.polling()

if __name__ == "__main__":
    bot = SmartHomeBot().run()