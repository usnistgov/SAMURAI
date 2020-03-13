Creating New Synthetic Apertures
==================================

When using the :method:`samurai.acquisition.SAMURAI_System.SAMURAI_System.csv_sweep`, the inputs are provided as a comma separated value (CSV) file for positions of the robot.
Each of the positions for the robotic positioner is given in a (x,y,z,alpha,beta,gamma) format where x,y,z are the cartesian positions (in mm), and alpha,beta,gamma are the rotation
of the robot (in degrees) about the x,y,z axis respectively.

When using :class:`samurai.acquisition.SAMURAI_System.SAMURAI_System`, the coordinate system of the robot is automatically set as follows:

- The **x-axis** is from the left/right when looking from behind the robot with x=0 aligned with the center of the base of the robot 
- The **y-axis** is down/up when looking from behind the robot with y=0 on the optical table.
        - For other setups, it may be desirable to change this frame of reference or ensure that the positions are built with this offset in mind
- The **z-axis** is in/out when looking from behind the robot which is typically the propogation direction when using a horn antenna.

These axes can be seen with a representation of the robot on an optical table below.

.. image:: ./external_data/table_layout.png
