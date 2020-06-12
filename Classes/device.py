import threading
import json
import os

class DeviceEncoder(json.JSONEncoder):
    
    def default(self, obj):
        if isinstance(obj, Device):
            return {
                'deviceID': obj.deviceID,
                'resources': obj.resources,
                'rest': obj.rest,
                'mqtt': obj.mqtt
            }
        elif isinstance(obj, list):
            tmp = []
            for d in obj:
                tmp.append(d.__dict__)
            return tmp
        else:
            return "ERRORE"

class DeviceManagerEncoder(json.JSONEncoder):
    
    def default(self, dm):
        if isinstance(dm, DeviceManager):
            return {
                'n': dm.n,
                'devices': DeviceEncoder().default(dm.devices),
                'lock': dm.lock
            }
        else:
            return "ERRORE"

class Device():
    
    def __init__(self, deviceID: str, resources: list, rest="", mqtt= ""):
        self.deviceID = deviceID
        self.resources = resources
        self.rest = rest
        self.mqtt = mqtt

    def getDeviceID(self):
        return self.deviceID

    def getTimestamp(self):
        return self.timestamp

    def addResource(self, resource):
        self.resources.append(resource)

class DeviceManager():
    
    def __init__(self):
        self.n = 0
        self.devices = []
        self.lock = threading.Lock()
        # Scrittura/Lettura da file
        if os.path.exists('Database/devices.json'):
            self.lock.acquire()
            with open('Database/devices.json') as json_file:
                if os.path.getsize('Database/devices.json') > 0:
                    tmp_dict = json.load(json_file)
                    self.n = tmp_dict['n']
                    if tmp_dict['n'] > 0:
                        self.devices = self._translateDevices(tmp_dict['devices'])
                    else:
                        self.devices = tmp_dict['devices']
                else:
                    json_file.close()
                    self.lock.release()
                    self._writeToFile
        else:
            self._saveToFile()
        self.lock.release()

    def _translateDevices(self, devices: list):
        """Translates a list of dict to a list of devices.

        Args:
            devices (list): list of dict

        Returns:
            list: list of devices
        """
        tmp_list = []
        for d in devices:
            tmp_list.append(Device(d['deviceID'],d['resources'],rest=d['rest'],mqtt=d['mqtt']))
        return tmp_list
    
    def _saveToFile(self):
        self.lock.acquire()
        with open('Database/devices.json', "w") as json_file:
                json.dump(self,json_file,cls=DeviceManagerEncoder)
        self.lock.release()
    
    def addDevice(self, resources: list, rest="", mqtt=""):
        """Used to add a device to the list

        Args:
            resources (list): list of resources
            rest (str, optional): rest server. Defaults to "".
            mqtt (str, optional): mqtt topic. Defaults to "".

        Returns:
            str: id of the object created
        """
        self.n += 1
        self.devices.append(Device(str(self.n),resources,rest=rest,mqtt=rest))
        self._saveToFile()
        return str(self.n)
        
    def getSingleDevice(self, deviceID: str):
        """Retrieves a single device from the list by its deviceID.

        Args:
            deviceID (str): deviceID

        Returns:
            str: object rapresentation in json. Returns "{}" if the device does not exists
        """
        for d in self.devices:
            if d.getDeviceID == deviceID:
                return json.dumps(d)
        return ""
    
    def getDevices(self):
        # Forse c'è un problema con quello che ritorna questa funzione
        return json.dumps(self.devices, cls=DeviceEncoder)
    
if __name__ == "__main__":
    dm = DeviceManager()
    d = Device("0",[],rest="rest")
    d.addResource('ciao')
    print(d)
    print(d.__dict__)
    dm.devices[-1].addResource("ciao")
    print(dm.devices[-1])
    print(dm.devices[-1].__dict__)
    print(json.dumps(dm.devices,cls=DeviceEncoder))
    print(json.dumps(dm,cls=DeviceManagerEncoder))
    print(type(dm.devices))
    