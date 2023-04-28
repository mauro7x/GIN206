# GIN206 final project

Some of these files might be unused, sorry.

Where to put:
- copy the repository into your home folder (~/)

Setup:
- reserve 2 nodes
- start tunslip
- make one node the border router
- flash the other node with resource-server
- use `lynx -dump http://[BORDER-ROUTER] to learn IPv6 address of the resource server
- `export SENSOR_SERVER=IPV6-ADRESS-OF-RESOURCE-SERVER`
- `sh ./post-sensor-data.sh`
- observe incoming data in Thingsboard
