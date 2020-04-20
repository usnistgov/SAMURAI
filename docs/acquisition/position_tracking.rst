:orphan:

Position Tracking With SAMURAI
=====================================

The SAMURAI system at NIST utilizes an Optitrack (add disclaimer) optical tracking system.

- brief on setup (POE, networking, etc)


Using the Motive Software
------------------------------

- open up the motive software

Calibrating with the Motive Software
++++++++++++++++++++++++++++++++++++++++

- Open the Camera Calibration Pane
- Cover the markers
- Get the wand out
- before any markers are in view click start wanding
- wand just around the areas of interest
- once finish click calculate
- lets cameras know where they are with respect to one another

- set the ground plane. Click Ground plane tab under camera calibration
- select 3 points for the origin
- click `Set Ground Plane` button

Creating Rigid bodies
+++++++++++++++++++++++++

- Right select all markers in rigid body
    - Assumes these markers are part of a static object (with respect to one another)

.. note:: make sure to align orientation of rigid bodies correctly using rotation and right click->reset pivot


- All current rigid bodies can be seen under Assets Pane. They can also be renamed here too.

how to use motive (set up rigid bodies, markers, whatnot)


Interface with Python
-----------------------------

Streaming from Motive
++++++++++++++++++++++++++++

- Setup streaming interface from motive in 'Streaming Pane'
- Make sure everyhting is being streamed. Make sure Up Axis is YUp
- This is sending tto the loopback `127.0.0.1` on the computer at port ???
- THis data is constantly streamed.
- This is then recieved in Python with the NatNetClient Class. This shouldn't be necessary to edit

Using the Samurai MotiveInterface
------------------------------------

- imported from 'from samurai.acquisition.instrument_control.SamuraiMotive import MotiveInterface
- instantiate with :code:`mymot = MotiveInterface()`
- query command for measuring :code:`mymot.query('meca_head')`, :code:`mymot.query(50166)`
- get distance command  :code:`mymot.get_distance('meca_head','origin')`
- measure from dictionary/list

 