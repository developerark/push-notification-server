import socket 
import argparse

parser = argparse.ArgumentParser()
parser.add_argument("id", type=str, help="client identifier")
args = parser.parse_args()

def createConnection(host, port):
    try:
        sockt = socket.socket()
        sockt.connect((host, port))
        sockt.send(args.id.encode())
        
    except Exception as error:
        print(error)
        exit()

    while True:
        response = sockt.recv(1014)
        print(response.decode())

if __name__ == "__main__":
    createConnection('127.0.0.1', 5000)