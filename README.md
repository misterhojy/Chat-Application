# Chat-Application

In your chat application, there will be one server and multiple clients. The clients are the users of the chat
application. All clients must implement the functionality needed to reliably exchange messages. In this
architecture, we will use a central server to keep track of which users are active and how to reach individual
users. The server knows all the clients that are currently active (i.e., can receive and send messages) and how
to reach them (i.e. current address). All message exchanges happen through the server. A client (e.g., Client1)
that wants to send a message to another client (e.g., Client2), first sends the message to the server, which then
sends it to the destined client.

Your job is to write Server and Client code. You can add your own additional utility functions in the
util.py file (if you want).

In this assignment, you will implement a chat application (like messenger) that will allow users to transfer
messages. You will also implement a custom reliable transport protocol on top of UDP. The assignment has the
following two parts:

Part 1: A simple chat application using UDP, which is a transport protocol that does not ensure reliable
communication.

Part 2.1: Extending the chat application in Part 1 to implement sequences and acknowledgements just like
TCP.

Part 2.2: Extending the chat application in Part 2.1 to ensure reliable communication of messages in case of
packet loss.
