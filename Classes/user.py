# Classe per la gestione degli User
#
# Formato json:
# {
#   userID: "",
#   name: "",
#   surname: "",
#   email: ""
# }

import datetime
import os
import json

##
# User object
##
class User(object):

  def __init__(self, userID, name, surname, email):
    self.userID = userID
    self.name = name
    self.surname = surname
    self.email = email

  def getUserID(self):
    return self.userID

  def getName(self):
    return self.name

  def getSurname(self):
    return self.surname

  def getEmail(self):
    return self.email

  def toDict(self):
    res = {"userID": "{}".format(self.userID),
            "name": "{}".format(self.name),
            "surname": "{}".format(self.surname),
            "email": "{}".format(self.email)
           }
    return res

  def toString(self):
    return "{}".format(self.toDict())

##
# UserManager object
##
class UserManager(object):

  def __init__(self):
    self.users = []
    self.n = 0

    if os.path.exists('Database/users.json'):
      with open('Database/users.json') as f:
        if os.path.getsize('Database/users.json') > 0:
          tmp = dict(json.loads(f.read()))['users']
          for obj in tmp:
            self.users.append(User(obj['userID'],obj['name'],obj['surname'],obj['email']))
          # Mantiene consistenza nella numerazione degli elementi
          if len(self.users):
            self.n = int(self.users[-1].getUserID()) + 1
        else:
          f.close()
          with open('Database/users.json', "w") as f:
            f.write('{"users":[]}')
    else:
      with open('Database/users.json', "w") as f:
        f.write('{"users":[]}')

  # Add user
  def addUser(self, name, surname, email):
    userID = self.n
    user = User(userID, name, surname, email)
    self.users.append(user)
    self.n += 1

    # Store object in users.json
    with open('Database/users.json', "w") as file:
      file.write(json.dumps(self.getUsersForJSon()))
    
    # Ritorno l'id per comunicarlo allo user che si è registrato
    return userID

  # Get single user
  def getSingleUser(self, userID):
    res = self.users[userID].toDict()
    return json.dumps(res)

  # Get all users
  def getUsers(self):
    return json.dumps(self.getUsersForJSon())

  def getUsersForJSon(self):
    listOfUsersAsDicts = []
    for Users in self.users:
      listOfUsersAsDicts.append(Users.toDict())
    res = {"Users": listOfUsersAsDicts}
    return res

  def getNumberOfUsers(self):
    return self.n
  # Remove Users based on timestamp
  # def removeUsers(self, timestamp):

