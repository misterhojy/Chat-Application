'''
This module defines the behaviour of a client in your Chat Application
'''
import sys
import getopt
import socket
import random
from threading import Thread
import os
import util
import signal
'''
Write your code inside this class. 
In the start() function, you will read user-input and act accordingly.
receive_handler() function is running another thread and you have to listen 
for incoming messages in this function.
'''

class Client:
    '''
    This is the main Client Class. 
    '''
    def __init__(self, username, dest, port, window_size):
        self.server_addr = dest
        self.server_port = port
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.settimeout(None)
        self.sock.bind(('', random.randint(10000, 40000)))
        self.name = username
        self.thread = True

    def start(self):
        '''
        Main Loop is here
        Start by sending the server a JOIN message. 
        Use make_message() and make_util() functions from util.py to make your first join packet
        Waits for userinput and then process it
        '''
        # when the function is started, send the join message to the server
        join_msg = util.make_message("join", 1, self.name) # first create the join message
        join_packet = util.make_packet("data", 0, join_msg) # create the message packet to send
        self.sock.sendto(join_packet.encode('utf-8'),(self.server_addr, self.server_port)) # send packet to server

        # continue to ask for user input unless disconnected
        while self.thread:
        # while True:
            client_input = input()
            client_input = client_input.split()
            match client_input[0]:
                case "help":
                    util.help()
                case "quit":
                    # send a disconnect packet to server
                    disc_msg = util.make_message("disconnect", 1, self.name)
                    disc_packet = util.make_packet("data", 0, disc_msg)
                    self.sock.sendto(disc_packet.encode('utf-8'), (self.server_addr, self.server_port))
                    print("quitting")
                    sys.exit()
                case "list":
                    list_msg = util.make_message("request_users_list", 2) # list msg
                    list_packet = util.make_packet("data", 0, list_msg)
                    self.sock.sendto(list_packet.encode('utf-8'), (self.server_addr, self.server_port))
                case "msg":
                    self.handle_send_message(client_input)
                case _:
                    # none of the right commands
                    err_msg = util.make_message(client_input[0], 2) # err_unknown_message message
                    err_packet = util.make_packet("data", 0, err_msg)
                    self.sock.sendto(err_packet.encode('utf-8'), (self.server_addr, self.server_port)) # send packet to server
                    print("incorrect userinput format")
        sys.exit()


    def receive_handler(self):
        '''
        Waits for a message from server and process it accordingly
        '''
        while True: # main loop for receiving messages from server
            server_packet, server_addr = self.sock.recvfrom(1024) # receive from socket
            server_packet = server_packet.decode('utf-8')
            
            msg_type, seqno, data, checksum = util.parse_packet(server_packet)  # parse information from packet
            msg = data.split()
            match msg[0]:
                case "err_server_full":
                    print("disconnected: server full")
                    # os.kill(os.getpid(), signal.SIGINT)
                    self.thread = False
                    break

                case "err_username_unavailable":
                    print("disconnected: username not available")
                    # os.kill(os.getpid(), signal.SIGINT)
                    self.thread = False
                    break

                case "response_users_list":
                    users = msg[3:]     # skip the first number that indicates how many users
                    print("list:", ' '.join(users))

                case "forward_message":
                    print(f"msg: {msg[2]}: {' '.join(msg[3:])}")

                case "err_unknown_message":
                    print("disconnected: server received an unknown command")
                    # os.kill(os.getpid(), signal.SIGINT)
                    self.thread = False
                    break

    def handle_send_message(self, client_input):
        if len(client_input) < 4:
            util.help()
            return

        if client_input[1].isdigit():
            number_of_recipients = int(client_input[1])
            if len(client_input) < number_of_recipients + 2:
                util.help()
                return

            recipients = client_input[2:number_of_recipients + 2]
            recipients.insert(0, str(number_of_recipients))
            message = client_input[number_of_recipients + 2:]
            message = recipients + message
            message = ' '.join(message)

            send_msg = util.make_message("send_message", 4, message)
            send_packet = util.make_packet("data", 0, send_msg)
            self.sock.sendto(send_packet.encode('utf-8'), (self.server_addr, self.server_port))
        else:
            util.help()

# def signal_handler(signal, frame):
#     sys.exit()

# Do not change below part of code
if __name__ == "__main__":
    def helper():
        '''
        This function is just for the sake of our Client module completion
        '''
        print("Client")
        print("-u username | --user=username The username of Client")
        print("-p PORT | --port=PORT The server port, defaults to 15000")
        print("-a ADDRESS | --address=ADDRESS The server ip or hostname, defaults to localhost")
        print("-w WINDOW_SIZE | --window=WINDOW_SIZE The window_size, defaults to 3")
        print("-h | --help Print this help")
    try:
        OPTS, ARGS = getopt.getopt(sys.argv[1:],
                                   "u:p:a:w", ["user=", "port=", "address=","window="])
    except getopt.error:
        helper()
        exit(1)

    PORT = 15000
    DEST = "localhost"
    USER_NAME = None
    WINDOW_SIZE = 3
    for o, a in OPTS:
        if o in ("-u", "--user="):
            USER_NAME = a
        elif o in ("-p", "--port="):
            PORT = int(a)
        elif o in ("-a", "--address="):
            DEST = a
        elif o in ("-w", "--window="):
            WINDOW_SIZE = a

    if USER_NAME is None:
        print("Missing Username.")
        helper()
        exit(1)

    S = Client(USER_NAME, DEST, PORT, WINDOW_SIZE)
    # signal.signal(signal.SIGINT, signal_handler)

    try:
        # Start receiving Messages
        T = Thread(target=S.receive_handler)
        T.daemon = True
        T.start()
        # Start Client
        S.start()
    except (KeyboardInterrupt, SystemExit):
        sys.exit()
