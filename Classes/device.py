# Classe per la gestione dei Devices
#
# Formato json:
# {
#   deviceID: "",
#   rest: "",
#   mqtt: ""
#   resources: [],
#   timestamp: ""
# }

import datetime
import os
import json
import threading
import time

##
# Device object
##
class Device(object):

  def __init__(self, deviceID, timestamp, resources, rest="", mqtt=""):
    self.deviceID = deviceID
    self.rest = rest
    self.mqtt = mqtt
    self.resources = resources
    self.timestamp = timestamp

  def updateAtrr(self,timestamp):
    self.timestamp = timestamp

  def getDeviceID(self):
    return self.deviceID

  def getTimestamp(self):
    return self.timestamp

  def addResource(self, resource):
    self.resources.append(resource)

  """
  la funzione toDict serve a riportare correttamente tutti i parametri della classe device
  per essere serializzata meglio dal json    
  """
  def toDict(self):
    rest = {"deviceID" : "{}".format(self.deviceID),
            "rest" : "{}".format(self.rest),
            "mqtt" : "{}".format(self.mqtt),
            "resources" : self.resources,
            "timestamp" : "{}".format(self.timestamp)
            }
    return rest

  def toString(self):
    return "{}".format(self.toDict())

##
# DeviceManager object
##
class DeviceManager(object):

  # Tempo in minuti prima dell'eleminazione se il timestamp non viene aggiornato
  TIMEOUT = 60*60   #prova, da reimpostare a 2
  tmp=[]

  def __init__(self):
    self.devices = []
    self.n = 0
    self.antifurto = 0
    # Controllo json
    if os.path.exists('Database/devices.json'):
      with open('Database/devices.json') as f:
        if os.path.getsize('Database/devices.json') > 0:
          tmp = json.loads(f.read())['devices']
          for obj in tmp:
            self.devices.append(Device(obj['deviceID'],obj['timestamp'],obj['resources'],obj['rest'],obj['mqtt']))
          # Mantiene consistenza nella numerazione degli elementi
          if len(self.devices):
            self.n = int(self.devices[-1].getDeviceID()) + 1
        else:
          f.close()
          with open('Database/devices.json', "w") as f:
            f.write('{"devices":[]}')
    else:
      with open('Database/devices.json', "w") as f:
        f.write('{"devices":[]}')

    # Thread
    self.lock = threading.Lock()
    self.thread = threading.Thread(target=self.removeDevices)
    self.thread.start()

  # Stop Execution
  def __del__(self):
    self.thread.join(1)
    self.lock.acquire()
    print(f"{self.getDevicesForJson()}")
    with open('Database/devices.json', "w") as file:
      json.dump(self.getDevicesForJson(), file) 
    self.lock.release()

  # Add device
  def addDevice(self, timestamp, resources, rest="", mqtt=""):
    print("Sto per aggiungere un nuovo device")
    deviceID = self.n
    device = Device(deviceID, timestamp, resources, rest=rest, mqtt=mqtt)
    self.devices.append(device)
    self.n += 1

    # Store object in devices.json
    self.lock.acquire()
    print(json.dumps(self.getDevicesForJson()))
    with open('Database/devices.json', "w") as file:
      json.dump(self.getDevicesForJson(), file)#      json.dump(self.devices, file)
    self.lock.release()
    
    # Ritorno l'id per comunicarlo al dispositivo che si è registrato
    return deviceID

  # Get single device
  def getSingleDevice(self, deviceID):
    for device in self.devices:
      if int(device.getDeviceID()) == deviceID:
        return json.dumps(device.toDict())      #return json.dumps(device)  implemento il dict
    return "{}"

  # Get all devices
  def getDevices(self):
    return json.dumps(self.getDevicesForJson())     #return json.dumps(self.devices), implemento json

  """
  getDeviceForJSon ritorna un dizionario con la lista di tutti i devices impostati come dict
  per essere trasformati in json
  quindi un dizionario che comprende una lista di dizionari. json controllato con jsonlint
  """
  def getDevicesForJson(self):
    listOfDevicesAsDicts = []
    for device in self.devices:
      listOfDevicesAsDicts.append(device.toDict())
    res = {"devices" : listOfDevicesAsDicts}
    return res

  # Remove devices based on timestamp
  def removeDevices(self):
    while True:
      tmp = []
      # Vengono mantenute solo le risorse che non hanno fatte scadere TIMEOUT
      for device in self.devices:
        if time.time() - float(device.getTimestamp()) < self.TIMEOUT:
          tmp.append(device)
      self.devices = tmp

      self.lock.acquire()
      print("Sono nella removeDevices")
      if os.path.exists('Database/devices.json'):
        with open('Database/devices.json', "w") as file:
          json.dump(self.getDevicesForJson(), file)#      json.dump(self.devices, file)
      self.lock.release()
      time.sleep(self.TIMEOUT)

  # Update an existin device
  def updateDevice(self, deviceID, timestamp, resource = ""): # per altre info basta aggiungere altri argomenti al metodo
    print("Sono entrato nella funzione update")
    for device in self.devices:
      if int(device.getDeviceID()) == int(deviceID):
        print("MI TROVO NELLA UPDATEDEVICE")
        device.updateAtrr(time.time())
        device.addResource(dict(resource))
        self.lock.acquire()
        with open('Database/devices.json', "w") as file:
          json.dump(self.getDevicesForJson(), file)  # json.dump(self.devices, file)
        self.lock.release()
      # else:
      #   # Da definire come si vuole gestire, ma dal momento che siamo su mqtt penso si possa
      #   # lasciare al caso l'avvenuta conferma
      #   return 404

  def getNumberOfDevices(self):
    return int(self.n)

  def getTemperature(self):
    temperature = 0
    for device in self.devices:
      if device.resources[-1]["n"] == "temperature" or device.resources[-1]["n"] == "tmp":
        temperature = device.resources[-1]["v"]
    return temperature

  def getAverageTemperature(self):
    temperature = 0
    cnt = 0
    for device in self.devices:
      if device.resources[-1]["n"] == "temperature" or device.resources[-1]["n"] == "tmp":
        for x in range(0, len(device.resources)):
          if device.resources[-1]["n"] == "temperature" or device.resources[-1]["n"] == "tmp":
            temperature += device.resources[x]["v"]
            cnt += 1
    return temperature/cnt

  def getLighting(self):
    light = 2
    for device in self.devices:
      if device.resources[-1]["n"] == "led":
        light = device.resources[-1]["v"]
    if light == 0:
      return 0
    elif light == 1:
      return 1
    else:
      return -1

  def getHeating(self):
    heat = 256
    for device in self.devices:
      if device.resources[-1]["n"] == "heat":
        heat = device.resources[-1]["v"]
    if heat == 0:
      return heat
    elif heat in range(1, 255):
      return heat
    else:
      return -1

  def getCooling(self):
    fan = 256
    for device in self.devices:
      if device.resources[-1]["n"] == "fan":
        fan = device.resources[-1]["v"]
    if fan == 0:
      return 0
    elif fan in range(1, 255):
      return fan
    else:
      return -1

  def getPresence(self):
    presence = 2
    for device in self.devices:
      if device.resources[-1]["n"] == "pres":
        presence = device.resources[-1]["v"]
    if presence == 0:
      return 0
    elif presence == 1:
      return 1
    else:
      return -1

  def setAntifurto(self, valore):
    self.antifurto = valore

  def getAntifurto(self):
    return self.antifurto