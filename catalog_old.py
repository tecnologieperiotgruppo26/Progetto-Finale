import cherrypy
from Classes.messagebroker import *
from Classes.device import *
from Classes.user import *
from Classes.service import *
from Classes.MQTT import *

class Catalog():
    """Simple class that handles devices and services, make them able to speak via json in an 
    API-fashion way
    """
    exposed = True
    
    def __init__(self):
        self.deviceManager = DeviceManager()
    
    
    def GET(self, *uri, **params):
        # Offre solo la possibilità di vedere la lista di risorse o la singola risorsa
        flag = self._isUriMultiple(uri)
        if uri[0] == "devices" and flag:
            # Devices
            if isIDvalid(uri[1]): # deviceID
                res = self.deviceManager.getSingleDevice(uri[1])
                    if res != "":
                        return res
                    else:
                        raise cherrypy.HTTPError(404, "Bad Request!")
            else:
                raise cherrypy.HTTPError(404, "Bad Request!")
        elif uri[0] == "devices":
            return self.deviceManager.getDevices()
        else:
            pass
    
    def POST(self, *uri, **params):
        # Offre solo la possibilità di registrare nuove risorse
        flag = isUriMultiple(uri)
        # Devices
        if uri[0]=="devices" and flag:
            if uri[1]=="new":
                serviceID = self.deviceManager.addDevice(params['resources'],rest=params['rest'],mqtt=params['mqtt'])
                return json.dumps(serviceID)
            else:
                raise cherrypy.HTTPError(404, "Bad Request!")
        else:
            raise cherrypy.HTTPError(404, "Bad Request!")
            
    def _isIDvalid(string):
        """Method that verifies if ID is an integer

        Args:
            string (str): the ID to evaluate

        Returns:
            bool: represent whether or not the id si valid
        """
        try:
            int(string):
            return True
        except:
            return False
        
    def _isUriMultiple(uri):
        """Method that verifies is Uri has multiple fields 

        Args:
            uri (str): uri to evaluate

        Returns:
            bool: represents whether or not uri has multiple fields
        """
        if len(uri) > 1:
            return True
        return False

if __name__ == '__main__': 
  conf = {
    '/': {
      'tools.sessions.on': True,
      'request.dispatch': cherrypy.dispatch.MethodDispatcher(),
      'tools.staticdir.root': os.path.abspath(os.getcwd()) 
    }
  }
  cherrypy.tree.mount(Catalog(), '/', conf) 
  cherrypy.engine.start()
  cherrypy.engine.stop()
    