import asyncio
import aiocoap
import logging
import requests


logging.basicConfig(level=logging.INFO)

# CONFIG ======================================================================

RESOURCE_SERVER = '2001:660:5307:3144::1662'
DEVICE_TOKEN = "MONITOKEN"
THINGSBOARD_HEADERS = {'Content-Type': 'application/json'}


# AUX FUNCTIONS ===============================================================


def get_thingsboard_uri(device):
    return f"http://mauro.rezel.net:8080/api/v1/{device}/telemetry"


def get_uri(resource):
    return f'coap://[{RESOURCE_SERVER}]/{resource}'


def post_to_thingsboard(resource_key, value, device=DEVICE_TOKEN):
    try:
        r = requests.post(get_thingsboard_uri(device), json={resource_key: value},
                          headers=THINGSBOARD_HEADERS)
        r.raise_for_status()
    except requests.exceptions.HTTPError as err:
        logging.warn(f"Error while posting data to Thingsboard: {err}")


async def get_sensor_data(protocol, resource):
    uri = get_uri(resources[resource]["path"])
    request = aiocoap.Message(code=aiocoap.GET, uri=uri)
    response = await protocol.request(request).response

    return float(response.payload)


# GLOBAL CONFIG ===============================================================


moving = False

resources = {
    "temperature": {
        "path": "my_res/sim_temperature",
        "freq_if_moving": 1,
        "freq_if_stopped": 10
    },
    "rain": {
        "path": "my_res/sim_rain",
        "freq_if_moving": 1,
        "freq_if_stopped": 10
    },
    "light": {
        "path": "my_res/sim_light",
        "freq_if_moving": 1,
        "freq_if_stopped": 10
    }
}


def accel_alarm_cb(response):
    global moving
    moving = bool(int(response.payload))
    print(f"Moving changed to: {moving}")


def generic_alarm_cb_factory(alarm_key):
    def cb(response):
        status = int(response.payload)
        print(f"Alarm \"{alarm_key}\" changed to: {status}")
        post_to_thingsboard(alarm_key, status)

    return cb


alarms = {
    "accel": {
        "path": "my_res/alarm_accel",
        "callback":  accel_alarm_cb
    },
    "lights": {
        "path": "my_res/alarm_lights",
        "callback":  generic_alarm_cb_factory("light_alarm")
    },
    "freezing": {
        "path": "my_res/alarm_freezing",
        "callback":  generic_alarm_cb_factory("temperature_alarm")
    },
    "traffic": {
        "path": "my_res/alarm_traffic",
        "callback":  generic_alarm_cb_factory("traffic_alarm")
    },
}


# COROUTINES ==================================================================


@asyncio.coroutine
def query_sensor(resource):
    def log(msg): return logging.debug(f"[query-sensor-{resource}] {msg}")
    protocol = yield from aiocoap.Context.create_client_context()

    while True:
        try:
            log(f"Querying...")
            try:
                value = yield from get_sensor_data(protocol, resource)
            except Exception as e:
                logging.warning(f"Error while fetching sensor: {e}")
            else:
                post_to_thingsboard(resource, value)
                log(f"Posted to Thingsboard (value: {value})")

            # Sleep
            sleep_time = resources[resource]["freq_if_moving"] if moving else resources[resource]["freq_if_stopped"]
            # log(f"Sleeping {sleep_time} secs before next query...")
            yield from asyncio.sleep(sleep_time)
        except asyncio.CancelledError:
            break


@asyncio.coroutine
def observe_alarms():
    protocol = yield from aiocoap.Context.create_client_context()

    # Accel
    alarm_keys = ["accel", "lights", "traffic", "freezing"]
    reqs = []

    for alarm_key in alarm_keys:
        req = aiocoap.Message(code=aiocoap.GET)
        req.set_request_uri(get_uri(alarms[alarm_key]["path"]))
        req.opt.observe = 0

        try:
            protocol_request = protocol.request(req)
            protocol_request.observation.register_callback(
                alarms[alarm_key]["callback"])
            reqs.append(protocol_request)
            response = yield from protocol_request.response
        except Exception as e:
            print("Request failed: %s" % str(e))
        else:
            alarms[alarm_key]["callback"](response)

    while True:
        try:
            yield from asyncio.sleep(30)
        except asyncio.CancelledError:
            for protocol_req in reqs:
                protocol_req.observation.cancel()
            break


if __name__ == "__main__":
    # Initialize event loop
    event_loop = asyncio.new_event_loop()
    asyncio.set_event_loop(event_loop)

    # Define tasks
    tasks = [
        query_sensor("light"),
        query_sensor("rain"),
        query_sensor("temperature"),
        observe_alarms()
    ]

    # Spawn tasks in the event loop
    for task in tasks:
        event_loop.create_task(task)

    # Run the event loop
    asyncio.get_event_loop().run_forever()
