import asyncio
import aiocoap
import logging


logging.basicConfig(level=logging.INFO)

# Config

SENSOR_SERVER = '2001:660:5307:3144::9576'


def getUri(resource):
    return f'coap://[{SENSOR_SERVER}]/{resource}'


# Global variables
query_freq_secs = 10


# @asyncio.coroutine
async def query_sensors():
    while True:
        try:
            # yield from asyncio.sleep(query_freq_secs)
            await asyncio.sleep(query_freq_secs)
            print(f"querying sensors at {query_freq_secs} freq")
        except asyncio.CancelledError:
            break


@asyncio.coroutine
def observe_alarm_accel():
    protocol = yield from aiocoap.Context.create_client_context()
    request = aiocoap.Message(code=aiocoap.GET)
    request.set_request_uri(getUri('my_res/alarm_accel'))

    # set observe bit from None to 0
    request.opt.observe = 0

    def observation_callback(response):
        global query_freq_secs
        query_freq_secs = 1 if response.payload == b'1' else 10
        print("[accel] callback: %r" % response.payload)

    try:
        protocol_request = protocol.request(request)
        protocol_request.observation.register_callback(observation_callback)
        response = yield from protocol_request.response
    except Exception as e:
        print("[accel] request failed: %s" % str(e))
    else:
        print("[accel] request ok: %r" % response.payload)

    while True:
        try:
            yield from asyncio.sleep(30)
        except asyncio.CancelledError:
            protocol_request.observation.cancel()
            break


@asyncio.coroutine
def observe_alarm_traffic():
    protocol = yield from aiocoap.Context.create_client_context()
    request = aiocoap.Message(code=aiocoap.GET)
    request.set_request_uri(getUri('my_res/alarm_traffic'))

    # set observe bit from None to 0
    request.opt.observe = 0

    def observation_callback(response):
        print("[traffic] callback: %r" % response.payload)

    try:
        protocol_request = protocol.request(request)
        protocol_request.observation.register_callback(observation_callback)
        response = yield from protocol_request.response
    except Exception as e:
        print("[traffic] request failed: %s" % str(e))
    else:
        print("[traffic] request ok: %r" % response.payload)

    while True:
        try:
            yield from asyncio.sleep(30)
        except asyncio.CancelledError:
            protocol_request.observation.cancel()
            break


# async def main():
event_loop = asyncio.new_event_loop()
asyncio.set_event_loop(event_loop)
event_loop.create_task(query_sensors())
event_loop.create_task(observe_alarm_accel())
event_loop.create_task(observe_alarm_traffic())
asyncio.get_event_loop().run_forever()

# asyncio.run(main())
