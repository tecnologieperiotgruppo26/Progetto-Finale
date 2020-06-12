import threading
import json
import os

class DeviceEncoder(json.JSONEncoder):
    
    def default(self, d):
        if isinstance(d, Device):
            return (d.deviceID,d.resources,d.rest,d.mqtt)
        else:
            return ""

class DeviceManagerEncoder(json.JSONEncoder):
    
    def default(self, dm):
        if isinstance(dm, DeviceManager):
            return (dm.n, dm.devices)
        else:
            return ""

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
        self.lock.acquire()
        if os.path.exists('Database/devices.json'):
            with open('Database/devices.json') as json_file:
                tmp_dict = json.load(json_file)
                self.n = tmp_dict['n']
                if tmp_dict['n'] > 0:
                    self.devices = self._translateDevices(tmp_dict['devices'])
                else:
                    self.devices = tmp_dict['devices']
            self.lock.release()
        else:
            with open('Database/devices.json', "w") as json_file:
                json.dump(self.__dict__,json_file,cls=DeviceManagerEncoder)
        self.lock.release()

    def _translateDevices(self, devices: list):
        tmp_list = []
        for d in devices:
            tmp_list.append(Device(d['deviceID'],d['resources'],rest=d['rest'],mqtt=d['mqtt']))
        return tmp_list
    
if __name__ == "__main__":
    dm = DeviceManager()
    d = Device("0",[],rest="rest")
    d.addResource("ciao")
    print(d)
    print(d.__dict__)
    dm.devices[-1].addResource("ciao")
    print(dm.devices[-1])
    print(dm.devices[-1].__dict__)
    