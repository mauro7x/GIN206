# Code for Fit IoT-LAB devices

### post-to-thingsboard.*
Example of how to make a POST to Thingsboard.

##### Setup

- reserve two nodes
- start tunslip
- flash one node with border router
- flash other node with post-to-thingsboard
- observe data in thingsboard and logging to the node's terminal

If you want to make changes and recompile, the easiest is to copy post-to-thingsboard.c to the 04-er-rest-example directory 
(for me, located at `~/iot-lab/parts/contiki/examples/iotlab/04-er-rest-example`),
update the Makefile there and compile using `make TARGET=iotlab-m3`.

