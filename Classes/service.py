# Classe per la gestione dei services
#
# Formato json:
# {
#   serviceID: "",
#   description: "",
#   rest: "",
#   mqtt: "",
#   timestamp: ""
# }

import datetime
import os
import json
import threading
import time

##
# Service object
##
class Service(object):
    
  def __init__(self, serviceID, timestamp, description, rest="", mqtt=""):
    self.serviceID = serviceID
    self.description = description
    self.rest = rest
    self.mqtt = mqtt
    self.timestamp = timestamp
    
  def getServiceID(self):
    return self.serviceID

  def getTimestamp(self):
    return self.timestamp

  def updateAtrr(self,timestamp):
    self.timestamp = timestamp
  
  def toDict(self):
    res = {
            "serviceID" : "{}".format(self.serviceID),
            "rest" : "{}".format(self.rest),
            "mqtt" : "{}".format(self.mqtt),
            "description" : "{}".format(self.description),
            "timestamp" : "{}".format(self.timestamp)
          }
    return res

  def toString(self):
    return "{}".format(self.toDict())

##
# ServiceManager object
##
class ServiceManager(object):

  TIMEOUT = 60*60
  tmp = []
  
  def __init__(self):
    self.services = []
    self.n = 0
    # Controllo json
    if os.path.exists('Database/services.json'):
      with open('Database/services.json') as f:
        if os.path.getsize('Database/services.json') > 0:
          tmp = dict(json.loads(f.read()))['services']
          for obj in tmp:
            self.services.append(Service(obj['serviceID'],obj['timestamp'],obj['description'],obj['rest'],obj['mqtt']))
          # Mantiene consistenza nella numerazione degli elementi
          if len(self.services):
            self.n = int(self.services[-1].getServiceID()) + 1
        else:
          f.close()
          with open('Database/services.json', "w") as f:
            f.write('{"services":[]}')
    else:
      with open('Database/services.json', "w") as f:
        f.write('{"services":[]}')
        
    # Thread
    self.lock = threading.Lock()
    self.thread = threading.Thread(target=self.removeServices)
    self.thread.start()
  
  # Stop Execution
  def __del__(self):
    self.thread.join(1)
    self.lock.acquire()
    print(f"{self.getServicesForJSon()}")
    with open('Database/services.json', "w") as file:
      json.dump(self.getServicesForJSon(), file)
    self.lock.release()
    
  # Add service
  def addService(self, timestamp, description, rest="", mqtt=""):
    print("Sto per aggiungere un nuovo servizio")
    serviceID = self.n
    service = Service(serviceID, timestamp, description, rest=rest, mqtt=mqtt)
    self.services.append(service)
    self.n += 1

    # Store object in services.json
    self.lock.acquire()
    with open('Database/services.json', "w") as file:
      json.dump(self.getServicesForJSon(), file)
    self.lock.release()
    
    # Ritorno l'id per comunicarlo al servizio che si è registrato
    return serviceID

  # Get single service
  def getSingleService(self, serviceID):
    for service in self.services:
      if int(service.getServiceID()) == serviceID:
        return json.dumps(service.toDict())      
    return "{}"

  # Get all services
  def getServices(self):
    return json.dumps(self.getServicesForJSon())

  def getServicesForJSon(self):
    listOfServicesAsDicts = []
    for service in self.services:
      listOfServicesAsDicts.append(service.toDict())
    dict = {"services" : listOfServicesAsDicts}
    return dict
  
  # Remove services based on timestamp
  def removeServices(self):
    while True:
      tmp = []
      # Vengono mantenute solo le risorse che non hanno fatto scadere TIMEOUT
      for service in self.services:
        if time.time() - float(service.getTimestamp()) < self.TIMEOUT:
          tmp.append(service)
      self.services = tmp

      self.lock.acquire()
      if os.path.exists('Database/services.json'):
        with open('Database/services.json', "w") as file:
          json.dump(self.getServicesForJSon(), file)
      self.lock.release()
      time.sleep(self.TIMEOUT)
  
  # Update an existing service
  def updateService(self, serviceID, timestamp):
    for service in self.services:
      if service.getServiceID() == serviceID:
        service.updateAtrr(timestamp)
    else:
      return 404

  def getNumberOfServices(self):
    return int(self.n)