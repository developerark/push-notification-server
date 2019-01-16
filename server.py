import socket as sockt
from threading import Thread
import time
from flask import Flask, request, jsonify

class Client:
    def __init__(self, connection, address):
        self.connection = connection
        self.address = address
        self.ID = None

    def send(self, data):
        self.connection.send(data.encode())

    def __str__(self):
        return str(self.connection) + str(self.address) + "=" + str(self.ID)

class Notification:
    def __init__(self, destinationID, sourceID, message):
        self.destinationID = destinationID
        self.sourceID = sourceID
        self.message = message

    def __str__(self):
        return str(self.destinationID) + ", " + str(self.sourceID) + ", " + str(self.message)

class Server:
    clients = []
    flaskApp = Flask(__name__)
    notifications = {}

    def __init__(self):
        # Setup broadcast service
        self.broadcastThread = Thread(target=self.broadcast)
        self.broadcastThread.setDaemon = True
        self.broadcastThread.start()

        # Setup notification registration server
        self.notificationRegistrationServerThread = Thread(target=self.startNotificationRegistrationService, args=('0.0.0.0', '8080',))
        self.notificationRegistrationServerThread.setDaemon = True
        self.notificationRegistrationServerThread.start()

        # Start accepting clients
        self.startAcceptingClients('0.0.0.0', 5000)

    def removeNotificationForClient(self, notification, client):
        notifications = Server.notifications[client.ID].remove(notification)
        if len(notifications) == 0:
            Server.notifications.pop(client.ID, None)

    def removeClient(self, client):
        Server.clients.remove(client)

    def handleNewClient(self, client):
        clientID = client.connection.recv(128)
        client.ID = clientID.decode()
        print("New Client Connected: ", client)

    def startAcceptingClients(self, host, port):
        socket = sockt.socket(sockt.AF_INET, sockt.SOCK_STREAM)
        print("Starting Server...")
        print("Waiting for clients...")
        socket.bind((host, port))
        socket.listen(5)

        while True:
            connection, address = socket.accept()
            client = Client(connection, address)
            Server.clients.append(client)
            thread = Thread(target=self.handleNewClient, args=(client,))
            thread.setDaemon = True
            thread.start()

    def startNotificationRegistrationService(self, host, port):
        self.flaskApp.run(host=host, port=port)

    @flaskApp.route('/register', methods=['POST'])
    def register():
        data = request.get_json()
        notification = Notification(data["destinationID"], data["sourceID"], data["message"])
        try:
            Server.notifications[notification.destinationID].append(notification)
        except Exception as error:
            Server.notifications.update({notification.destinationID: [notification]})
        return str(notification) + " added"

    def broadcast(self):
        while True:
            for client in Server.clients:
                try:
                    notifications = Server.notifications[client.ID]
                except Exception as error:
                    # When there is clients but not notification for them
                    continue

                for notification in notifications:
                    try:
                        client.send(str(notification))
                        notifications.remove(notification)
                    except Exception as error:
                        print(str(error) + ": %s disconnected" % (client.ID))
                        client.connection.close()
                        Server.removeClient(client)
            time.sleep(0.0001)

if __name__ == "__main__":
    server = Server()

