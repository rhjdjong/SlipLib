#  Copyright (c) 2020. Ruud de Jong
#  This file is part of the SlipLib project which is released under the MIT license.
#  See https://github.com/rhjdjong/SlipLib for details.

"""
echoserver
----------

This directory contains an example Server and Client application
that demonstrate a basic use-case for Slip-encoded messages.

.. automodule:: examples.echoserver.server

.. automodule:: examples.echoserver.client

Usage
+++++

Open a terminal window in the :file:`echoserver` directory
and run the :file:`server.py` script. This will start the server
and print the address on which the server is listening

.. code:: bash

   $ python server.py
   Slip server listening on ('127.0.0.1', 59454)

Then in another terminal window in the same directory run the :file:`client.py` script
with the address reported by the server

.. code:: bash

   $ python client.py 127.0.0.1 59454
   Connecting to 127.0.0.1, port 59454
   Message>

You can now enter a message, and the client will print the response from the server
before prompting for the next message.
An empty message stops both the client and the server.

.. code:: bash

   $ python client.py 127.0.0.1 59454
   Connecting to 127.0.0.1, port 59454
   Message> hallo
   Response: b'ollah'
   Message> bye
   Response: b'eyb'
   Message>
   $

The server will have printed the following information:

.. code:: bash

   $ python server.py
   Slip server listening on ('127.0.0.1', 59454)
   Raw data received: b'\\xc0hallo\\xc0'
   Decoded data: b'hallo'
   Sending raw data: b'\\xc0ollah\\xc0'
   Raw data received: b'\\xc0bye\\xc0'
   Decoded data: b'bye'
   Sending raw data: b'\\xc0eyb\\xc0'
   Raw data received: b''
   Decoded data: b''
   Closing down
   $
"""
