# config
sensor_server=$SENSOR_SERVER;
device_token="${DEVICE_TOKEN:-MONITOKEN}"

# sensor_server="2001:660:4403:481::b870";
thingsboard_telemetry="http://mauro.rezel.net:8080/api/v1/$device_token/telemetry"
light_key="light";
temperature_key="temperature";
rain_key="rain";

while :;
do
# insert IPv6 address of sensor CoAP server
light=$(aiocoap-client coap://[$sensor_server]/my_res/sim_light);
temperature=$(aiocoap-client coap://[$sensor_server]/my_res/sim_temperature);
rain=$(aiocoap-client coap://[$sensor_server]/my_res/sim_rain);

curl -X POST -d "{$light_key: $light}" $thingsboard_telemetry --header "Content-Type:application/json";
curl -X POST -d "{$temperature_key: $temperature}" $thingsboard_telemetry --header "Content-Type:application/json";
curl -X POST -d "{$rain_key: $rain}" $thingsboard_telemetry --header "Content-Type:application/json";
sleep 1;
done
