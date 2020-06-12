import os
import cherrypy

class FreeBoard(object): 
    """Simpe REST service that enables user to visualize data about his devices conncted to the 
    SmartHome Controller.
    """
    exposed = True

    def GET(self, *uri, **params):
        return open('./freeboard/index.html')

    def POST(self, *uri, **params):
        if uri[0]=="saveDashboard":
            with open('./freeboard/static/dashboard/dashboard.json', "w") as file:
                print(f"{params['json_string']}")
                file.write(params['json_string'])

if __name__ == '__main__': 
    conf = {
        '/': {
        'tools.sessions.on': True,
        'request.dispatch': cherrypy.dispatch.MethodDispatcher(),
        'tools.staticdir.root': os.path.abspath(os.getcwd()) 
        },
        '/freeboard': {
            'tools.staticdir.on': True,
            'tools.staticdir.dir': './freeboard' 
        },
        '/static': {
            'tools.staticdir.on': True,
            'tools.staticdir.dir': './freeboard/static'
        }
    }
    cherrypy.tree.mount(FreeBoard(), '/', conf) 
    cherrypy.engine.start()
    cherrypy.engine.block()