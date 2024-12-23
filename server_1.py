'''
This module defines the behaviour of server in your Chat Application
'''
import sys
import getopt
import socket
import util


class Server:
    '''
    This is the main Server Class. You will  write Server code inside this class.
    '''
    def __init__(self, dest, port, window):
        self.server_addr = dest
        self.server_port = port
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.settimeout(None)
        self.sock.bind((self.server_addr, self.server_port))

    def handle_join(self, msg, client_addr):
        if len(self.users) == util.MAX_NUM_CLIENTS:
            self.send_error('err_server_full', client_addr)
        elif msg[2] in self.users:
            self.send_error('err_username_unavailable', client_addr)
        else:
            self.users[msg[2]] = client_addr
            print("join:", msg[2])

    def handle_request_users_list(self, client_addr):
        client = list(self.users.keys())[list(self.users.values()).index(client_addr)]  # getting user
        users_list = list(self.users.keys())
        users_list.sort(key=str.lower)  # the user list in ascending order
        number = str(len(users_list))
        users_list.insert(0, number)    # need to insert the amount of clients before listing users

        list_msg = util.make_message("response_users_list", 3, ' '.join(users_list))
        list_packet = util.make_packet("data", 0, list_msg)
        self.sock.sendto(list_packet.encode('utf-8'), client_addr) # send packet to server
        print("request_users_list:", client)

    def handle_disconnect(self, msg):
        del self.users[msg[2]]
        print("disconnected:", msg[2])

    def send_error(self, error_msg, client_addr):
        response = util.make_message(error_msg, 2)
        packet = util.make_packet("data", 0, response)
        self.sock.sendto(packet.encode('utf-8'), client_addr)

    def send_packet(self, message, client_addr):
        client = list(self.users.keys())[list(self.users.values()).index(client_addr)]  # getting user
        # need to get list of the names
        recepients = int(message[2])
        list_users = message[3:(recepients + 3)]    # skipping the first number that shows how many users
        msg = message[(recepients+3):]
        msg = ' '.join(msg) # join the message together

        for user in list_users: # for each user in the list need to send it a message
            if user in self.users.keys():
                # forward the message to the intended users
                user_addr = self.users[user]
                # message is "recepient sender"
                forward_msg = util.make_message("forward_message", 4, (client+ " " +msg))
                forward_packet = util.make_packet("data", 0, forward_msg)
                self.sock.sendto(forward_packet.encode('utf-8'), user_addr)
                print("msg:", client)

            else:
                print("msg:", client)
                print(f"msg: {client} to non-existent user {user}")

    def start(self):
        self.users = {}  # User dictionary
        while True:
            client_packet, client_addr = self.sock.recvfrom(1024) # receive from socket
            client_packet = client_packet.decode('utf-8')            
            msg_type, seqno, data, checksum = util.parse_packet(client_packet)
            msg = data.split()
            match msg[0]:
                case "join":
                    self.handle_join(msg, client_addr)
                case "request_users_list":
                    self.handle_request_users_list(client_addr)
                case "disconnect":
                    self.handle_disconnect(msg)
                case "send_message":
                    self.send_packet(msg, client_addr)
                case _:
                    client = list(self.users.keys())[list(self.users.values()).index(client_addr)]
                    self.send_error('err_unknown_message', client_addr)
                    print(f"disconnected: {client} sent unknown command")

# Do not change below part of code

if __name__ == "__main__":
    def helper():
        '''
        This function is just for the sake of our module completion
        '''
        print("Server")
        print("-p PORT | --port=PORT The server port, defaults to 15000")
        print("-a ADDRESS | --address=ADDRESS The server ip or hostname, defaults to localhost")
        print("-w WINDOW | --window=WINDOW The window size, default is 3")
        print("-h | --help Print this help")

    try:
        OPTS, ARGS = getopt.getopt(sys.argv[1:],
                                   "p:a:w", ["port=", "address=","window="])
    except getopt.GetoptError:
        helper()
        exit()

    PORT = 15000
    DEST = "localhost"
    WINDOW = 3

    for o, a in OPTS:
        if o in ("-p", "--port="):
            PORT = int(a)
        elif o in ("-a", "--address="):
            DEST = a
        elif o in ("-w", "--window="):
            WINDOW = a

    SERVER = Server(DEST, PORT,WINDOW)
    try:
        SERVER.start()
    except (KeyboardInterrupt, SystemExit):
        exit()
