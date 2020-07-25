# Classe per la gestione del MessageBroker
#
# Formato json:
# {
#   "url": "",
#   "port": "",
#   "catalogTopic": ""
# }

import datetime
import os
import json

##
# MessageBroker object
##
class MessageBroker(object):

  def __init__(self, url, port, catalogTopic):
    self.url = url
    self.port = port
    self.catalogTopic = catalogTopic

  def getMessageBroker(self):
    return json.dumps(self)

##
# MessageBroker object
##
class MessageBrokerManager(object):

  def __init__(self):
    self.messageBroker = {}
    if os.path.exists('Database/mb.json'):
      with open('Database/mb.json') as file:
        self.messageBroker = dict(json.loads(file.read()))

  # Add message broker
  def addMessageBroker(self, url, port, catalogTopic):
    if self.messageBroker!=False:
      self.messageBroker = MessageBroker(url, port, catalogTopic)
      # Store object in mb.json
      with open('Database/mb.json', "w") as file:
        json.dump(self.messageBroker, file)

  # Get catalog topic
  def getMessageBrokerCatalogTopic(self):
    return self.messageBroker['catalogTopic']

  def getMessageBroker(self):
    return json.dumps(self.messageBroker)