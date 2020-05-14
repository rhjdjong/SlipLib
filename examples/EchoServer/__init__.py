#  Copyright (c) 2020. Ruud de Jong
#  This file is part of the SlipLib project which is released under the MIT license.
#  See https://github.com/rhjdjong/SlipLib for details.

"""
EchoServer
----------

This directory contains an example Server and Client application
that demonstrate a basic use-case for Slip-encoded messages.

.. automodule:: examples.EchoServer.Server

.. automodule:: examples.EchoServer.Client

Usage
+++++

Open a terminal window in the :file:`EchoServer` directory
and run the :file:`Server.py` script. This will start the server
and print the address on which the server is listening

.. code:: bash

   $ python Server.py
   Slip server listening on ('127.0.0.1', 59454)

Then in another terminal window in the same directory run the :file:`Client.py` script
with the address reported by the server

.. code:: bash

   $ python Client.py 127.0.0.1 59454
   Connecting to 127.0.0.1, port 59454
   Message>

You can now enter a message, and the client will print the response from the server
before prompting for the next message.
An empty message stops both the client and the server.

.. code:: bash

   $ python Client.py 127.0.0.1 59454
   Connecting to 127.0.0.1, port 59454
   Message> hallo
   b'ollah'
   Message> bye
   b'eyb'
   Message>
   $

The server will have printed the following information:

.. code:: bash

   $ python Server.py
   Slip server listening on ('127.0.0.1', 59454)
   raw data received: b'\\xc0hallo\\xc0'
   decoded data: b'hallo'
   sending raw data: b'\\xc0ollah\\xc0'
   raw data received: b'\\xc0bye\\xc0'
   decoded data: b'bye'
   sending raw data: b'\\xc0eyb\\xc0'
   raw data received: b''
   decoded data: b''
   closing down
   $

"""