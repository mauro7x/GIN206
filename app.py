import asyncio
import aiocoap
import logging
import requests


logging.basicConfig(level=logging.INFO)

# CONFIG ======================================================================

RESOURCE_SERVER = '2001:660:5307:3144::a476'
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


async def get_sensor_data(resource):
    protocol = await aiocoap.Context.create_client_context()
    uri = get_uri(resources[resource]["path"])
    request = aiocoap.Message(code=aiocoap.GET, uri=uri)
    response = await protocol.request(request).response

    return float(response.payload)


# GLOBAL CONFIG ===============================================================


moving = False

resources = {
    "temperature": {
        "path": "my_res/sim_temperature",
        "freq_if_moving": 3,
        "freq_if_stopped": 10
    },
    "rain": {
        "path": "my_res/sim_rain",
        "freq_if_moving": 5,
        "freq_if_stopped": 20
    },
    "light": {
        "path": "my_res/sim_light",
        "freq_if_moving": 1,
        "freq_if_stopped": 5
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
    def log(msg): return print(f"[query-sensor-{resource}] {msg}")

    while True:
        try:
            log(f"Querying...")
            try:
                value = yield from get_sensor_data(resource)
            except Exception as e:
                logging.warning(f"Error while fetching sensor: {e}")
            else:
                post_to_thingsboard(resource, value)
                log(f"Posted to Thingsboard (value: {value})")

            # Sleep
            sleep_time = resources[resource]["freq_if_moving"] if moving else resources[resource]["freq_if_stopped"]
            log(f"Sleeping {sleep_time} secs before next query...")
            yield from asyncio.sleep(sleep_time)
        except asyncio.CancelledError:
            break


@asyncio.coroutine
def observe_alarm(alarm):
    def log(msg): return print(f"[observer-alarm-{alarm}] {msg}")

    protocol = yield from aiocoap.Context.create_client_context()
    request = aiocoap.Message(code=aiocoap.GET)
    request.set_request_uri(get_uri(alarms[alarm]["path"]))

    # set observe bit from None to 0
    request.opt.observe = 0

    try:
        protocol_request = protocol.request(request)
        protocol_request.observation.register_callback(
            alarms[alarm]["callback"])
        response = yield from protocol_request.response
    except Exception as e:
        log("Request failed: %s" % str(e))
    else:
        log("Request ok: %r" % response.payload)
        alarms[alarm]["callback"](response)

    while True:
        try:
            yield from asyncio.sleep(30)
        except asyncio.CancelledError:
            log("Observation cancelled")
            protocol_request.observation.cancel()
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
        observe_alarm("accel"),
        observe_alarm("lights"),
        # observe_alarm("freezing"),
        # observe_alarm("traffic"),
    ]

    # Spawn tasks in the event loop
    for task in tasks:
        event_loop.create_task(task)

    # Run the event loop
    asyncio.get_event_loop().run_forever()
