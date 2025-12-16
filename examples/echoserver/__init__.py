#  Copyright (c) 2020. Ruud de Jong
#  This file is part of the SlipLib project which is released under the MIT license.
#  See https://github.com/rhjdjong/SlipLib for details.

"""
Echoserver
----------

.. no-index

This directory contains an example server and client application
that demonstrate a basic use-case for Slip-encoded messages.
The example works both for IPv4 and IPv6 sockets.

.. automodule:: echoserver.server
   :no-index:

.. automodule:: echoserver.client
   :no-index:

Usage
+++++

Open a terminal window in the :file:`echoserver` directory
and run the :file:`server.py` script. This will start the server
and print the address on which the server is listening.

.. code:: bash

   $ python server.py
   Slip server listening on localhost, port 59454

Then in another terminal window in the same directory run the :file:`client.py` script
with the port number reported by the server.

.. code:: bash

   $ python client.py 59454
   Connecting to server on port 59454
   Connected to ('127.0.0.1', 59454)
   Message>

You can now enter a message, and the client will print the response from the server
before prompting for the next message.
An empty message stops both the client and the server.

.. code:: bash

   $ python client.py 59454
   Connecting to server on port 59454
   Connected to ('127.0.0.1', 59454)
   Message> hallo
   Response: b'ollah'
   Message> bye
   Response: b'eyb'
   Message>
   $

The server will have printed the following information:

.. code:: bash

   $ python server.py
   Slip server listening on localhost, port 59454
   Incoming connection from ('127.0.0.1', 59458)
   Raw data received: b'hallo\\xc0'
   Decoded data: b'hallo'
   Sending raw data: b'ollah\\xc0'
   Raw data received: b'bye\\xc0'
   Decoded data: b'bye'
   Sending raw data: b'eyb\\xc0'
   Raw data received: b''
   Decoded data: b''
   Closing down
   $

Running on IPv6
+++++++++++++++

By running the server with the argument ``ipv6``,
an IPv6-based connection will be established.

.. list-table::
   :header-rows: 1
   :widths: 50 50

   * - Server
     - Client
   * - .. code:: bash

          $ python server.py ipv6
          Slip server listening on localhost, port 59454
          \u200b
          Incoming connection from ('::1', 59458, 0, 0)
          \u200b
          ...
     - .. code:: bash

          \u200b
          \u200b
          $ python client.py 59454
          Connecting to server on port 59454
          Message>
          ...
"""
