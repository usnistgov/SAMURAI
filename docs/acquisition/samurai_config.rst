
.. _hardware-config:

System Hardware Configuration
==============================

(PICTURE OF SETUP)

Meca 500 6 axis positioner
-------------------------------

Small 6 axis positioner.

- `Mecademic Website <https://www.mecademic.com/products/Meca500-small-robot-arm>`_
- `Meca500 R3 User Manual <https://www.mecademic.com/Documentation/Meca500-R3-User-Manual.pdf>`_
- `Meca500 R3 Programming Manual <https://www.mecademic.com/Documentation/Meca500-R3-Programming-Manual.pdf>`_

Keysight PNA-X (N5245A)
----------------------------

10MHz to 50GHz VNA. Ports are 2.4mm Male typically with 2.4mm F-F connector savers on them.

- `N5245A Datasheet <https://literature.cdn.keysight.com/litweb/pdf/N5245-90008.pdf>`_

Antennas
--------------

- Sage-millimeter 17dBi WR-28 Horn antenna  
   - `17 dBi WR-28 Sage Horn Datasheet <https://www.sagemillimeter.com/content/datasheets/SAR-1725-28-S2.pdf>`_

- Sage-millimeter 23dBi WR-28 Horn antenna  
   - `23 dBi WR-28 Sage Horn Datasheet <https://www.sagemillimeter.com/content/datasheets/SAR-2309-28-S2.pdf>`_


Cables
------------

- Junkosha 2.4mm (M-M) 3m Cables (MWX251)
- Junkosha 2.4mm (M-M) 0.25m Cables (MWX251)

.. seealso:: http://www.junkosha.co.jp/english/products/cable/c03.html

Adapters
-------------

- Sage-millimeter 2.4mm to WR-28 right angle adapters
   - `WR-28 to 2.4mm Female Adapter Datasheet <https://www.sagemillimeter.com/content/datasheets/SWC-282F-R1.pdf>`_
   - `WR-28 to 2.4mm Male Adapter Datasheet <https://www.sagemillimeter.com/content/datasheets/SWC-282M-R1.pdf>`_

- Sage-millimeter K (2.92mm) to WR-28 right angle adapters
   - `WR-28 to K Female Adapter Datasheet <https://www.sagemillimeter.com/content/datasheets/SWC-28KF-R1.pdf>`_
   - `WR-28 to K Male Adapter Datasheet <https://www.sagemillimeter.com/content/datasheets/SWC-28KM-R1.pdf>`_

Antenna Mounts
-------------------------

Custom mounts for antennas were also designed to attach a section of 2" WR-waveguide to the Meca500 robot. These mounts are designed with a number
of constrictions in mind such as:

- Ability to calibrate at WR-28
- Repeatability of measurements
- Ability to test cable drift (change antenna/standards without unmounting)

These mounts are typically 3D printed with plastic, and 3 steel ball bearings are attached to provide a kinematic connection between the robot 
mount and the waveguide mount. This mount also provides an absorber plate to attach absorber directly behind the antenna. These mounts were 
created in a horn antenna and open ended waveguide configuration.

Networking
--------------

Currently, the samurai system is run over a custom local network run through a simple network switch. This connects to the VNA, Meca500 Robot arm, and eventually cameras.

Remote PNA-X control
------------------------

A remote Keyboard, Video, Mouse box is used. This allows a keyboard, monitor, and a mouse to be placed far away from our VNA and a single CAT-5 cable (ethernet) to be run between the two. This comprises of a small box with 2 usb ports and a VGA connection. This box is then connected directly via a CAT-5 Cable near the VNA with a usb-B output and a second VGA connection. These two boxes provide remote control over the VNA
.. NOTE: This is not connected to the local network. These two boxes are only connected to one another and cannot be run over a network. They simply translate the usb and VGA info and transmit over a CAT-5 cable.

IP and VISA Addresses
------------------------

- PNA-X 
   - IP Address   = `192.168.0.2 <http://192.168.0.2>`_
   - VISA Address = 'TCPIP0::10.0.0.2::inst0::INSTR'

- Meca500
   - IP Address   = `192.168.0.5 <http://192.168.0.5>`_ 
   - VISA Address = Could not get VISA to work correctly! Connect using sockets.

- IP Webcam 
   - IP Address   = `192.168.0.11 <http://192.168.0.11>`_ 
   - Username: `admin` -- Password: `123456`
   - A live stream will show up if you go to the above address and login
   - A VLC stream has higher latency but can be connected by the following steps:
      #. Open VideoLAN (VLC with the construction cone icon)
      #. Select `Media->Open Network Stream...`
      #. Enter :code:`rtsp://admin:123456@192.168.0.11:554/cam1/mpeg4` and click connect
      #. To take a snapshot click `Video->Take Snapshot`. This will save a snapshot to the users `Pictures` folder from which it can then be renamed and copied
         - The VLC stream has not always been reliable and may freeze. For this reason it is recommended to use the web interface except when taking snapshots of the setup

- Computer 
   - IP Address   = `192.168.0.1 <http://192.168.0.1>`_ 
   - Setting Network adapter settings for local network:
      #. Go to `Control Panel->Network and Internet->Network Connections`
      #. Right click on the network controller for the local network and select `Properties` (admin status required)
      #. Click on `TCP/IPv4` and then click `Properties`
      #. Click the radio button for `Use the following IP address` and type in the following parameters
         - IP address = 192.168.0.1
         - subnet mask = 255.255.255.0
         - Default gateway = DO NOT POPULATE
      #. Then click `OK` and `Close` to close out of the properties menu. You should now be able to access items on the local network.
- Network Switch
   - IP Address   = `192.168.0.239 <http://192.168.0.239>`_ 
   - Password is `password` 

- Optitrack Cameras
   - These IP addresses are unkown to the user

.. warning:: It is possible at some point in time The optitrack IP addresses may conflict with one of the other devices on the network. 
	If so change the IP of whatever device is conflicting to something new. This may take some trial and error.
