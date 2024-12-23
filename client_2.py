'''
This module defines the behaviour of a client in your Chat Application
'''
import sys
import getopt
import socket
import random
from threading import Thread
import os
import threading
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
        self.sock.settimeout(.5)
        self.sock.bind(('', random.randint(10000, 40000)))
        self.name = username
        self.thread = True
        self.seqno = 0
        self.ack_received = threading.Event()
        #5 + len(packets-1)
        #[1,2,3,4,5]

    def start(self):
        '''
        Main Loop is here
        Start by sending the server a JOIN message. 
        Use make_message() and make_util() functions from util.py to make your first join packet
        Waits for userinput and then process it
        '''
        # when the function is started, send the join message to the server
        # need  while loop to continously send packet just incase if it does not send
        packet = self.create_se("start")
        self.send_packet(packet)
        segments = self.segment_message("join", 1, self.name)   # break message to send into segments
        for segment in segments:
            self.send_packet(segment) # send packet to server
        packet = self.create_se("end")
        self.send_packet(packet)

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
                    packet = self.create_se("start")
                    self.send_packet(packet)
                    quit_segments = self.segment_message("disconnect", 1, self.name)
                    for segment in quit_segments:
                        self.send_packet(segment) # send packet to server
                    packet = self.create_se("end")
                    self.send_packet(packet)
                    print("quitting")
                    sys.exit()
                case "list":
                    packet = self.create_se("start")
                    self.send_packet(packet)
                    list_segments = self.segment_message("request_users_list", 2)
                    for segment in list_segments:
                        # print(segment)
                        self.send_packet(segment) # send packet to server
                    packet = self.create_se("end")
                    self.send_packet(packet)
                case "msg":
                    self.handle_send_message(client_input)
                case _:
                    # none of the right commands
                    packet = self.create_se("start")
                    self.send_packet(packet)
                    err_segments = self.segment_message(client_input[0], 2)
                    for segment in err_segments:
                        # print(segment)
                        self.send_packet(segment) # send packet to server
                    packet = self.create_se("end")
                    self.send_packet(packet)
                    print("incorrect userinput format")
        sys.exit()


    def receive_handler(self):
        '''
        Waits for a message from server and process it accordingly
        '''
        while True: # main loop for receiving messages from server
            try:
                server_packet, server_addr = self.sock.recvfrom(1024) # receive from socket
                server_packet = server_packet.decode('utf-8')

                msg_type, seqno, data, checksum = util.parse_packet(server_packet)  # parse information from packet
                msg = data.split()
                if not msg:
                    if (msg_type == "ack"):
                        print("received an ACK, move to next packet")
                        self.sock.settimeout(None)
                        self.ack_received.set()  # Signal that an ACK has been received

                else:
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

            except Exception as e:
                # print(f"Error receiving data: {e}")
                break

    # def insert_command_into_message(self, message, command, chunk_size=1400):
    #     # Ensure the message is long enough to require the insertion of the command
    #     pieces = []
    #     for start in range(0, len(message), chunk_size):
    #         end = start + chunk_size
    #         # Append the chunk followed by the command, except for the last chunk
    #         if end < len(message):
    #             pieces.append(message[start:end] + command + " ")
    #         else:
    #             pieces.append(message[start:end])  # Do not add command after the last piece
    #     return ''.join(pieces)
    
    # given large message, and starting seq no
    # break large message into chunks, each chunk turns into a data packet with increasing seq no
    # return array of packets
    def segment_message(self, msg_type, mesg_format, message=None): 
        packets = []
        if (message):
            # need to get the e.g msg 2 client client on each packet
            if (msg_type == "send_message"):
                pieces = message.split()
                command = pieces[0:int(pieces[0])+1]    # get the command that need to be in every packet
                command = ' '.join(command)
                full_command = command + " "
                command_length = len(full_command)
                max_message_length_first = util.CHUNK_SIZE
                max_message_length_others = util.CHUNK_SIZE - command_length

                first_segment = message[:max_message_length_first]
                remaining_message = message[max_message_length_first:]
                segments = [first_segment] + [
                    remaining_message[i:i + max_message_length_others]
                    for i in range(0, len(remaining_message), max_message_length_others)
                ]
                for index, segment in enumerate(segments):
                    if index == 0:
                        full_segment = segment
                    else:
                        full_segment = full_command + segment

                    msg = util.make_message(msg_type, mesg_format, full_segment)
                    packet = util.make_packet("data", self.seqno, msg)
                    
                    packets.append(packet)
                    self.seqno += 1
            else:
                segments = [message[i:i+util.CHUNK_SIZE] for i in range(0, len(message), util.CHUNK_SIZE)]
                for segment in segments:
                    msg = util.make_message(msg_type, mesg_format, segment)
                    packet = util.make_packet("data", self.seqno, msg)
                    
                    packets.append(packet)
                    self.seqno +=1
        else:
            msg = util.make_message(msg_type, mesg_format)
            packet = util.make_packet("data", self.seqno, msg)
            packets.append(packet)
            self.seqno +=1
        return packets


    def create_se(self, type):
        packet = util.make_packet(type, self.seqno, "") # send/end packet
        self.seqno += 1
        return packet

    def send_packet(self, data):
        """ Attempt to send a packet and wait for an ACK. """
        self.ack_received.clear()  # Reset the ACK event before sending
        self.sock.settimeout(.5)

        while not self.ack_received.is_set():
            try:
                print("INSEND", data)
                self.sock.sendto(data.encode('utf-8'), (self.server_addr, self.server_port))
                print("Packet sent, waiting for ACK...")
                self.ack_received.wait(timeout=0.5)  # Wait for the ACK event to be set

            except Exception as e:
                print(f"Failed to send data: {e}")

            if not self.ack_received.is_set():
                print("No ACK received, resending...")
                continue  # Resend the packet if ACK wasn't receive

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

            packet = self.create_se("start")
            self.send_packet(packet)
            segments = self.segment_message("send_message", 4, message)
            for segment in segments:
                self.send_packet(segment) # send packet to server
            packet = self.create_se("end")
            self.send_packet(packet)
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
