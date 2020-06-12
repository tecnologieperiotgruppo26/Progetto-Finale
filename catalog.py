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
    
    def GET(self, *uri, **params):
        flag = self._isUriMultiple(uri)
        if uri[0] == "devices" and flag:
            if isIDvalid(uri[1]): # deviceID
                if int(uri[1]) < self.deviceManager.getNumberOfDevices():
                    return self.deviceManager.getSingleDevice(int(uri[1]))
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
    
    