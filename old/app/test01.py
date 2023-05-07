import logging
import asyncio

from aiocoap import *

logging.basicConfig(level=logging.INFO)

# Config

SENSOR_SERVER = '2001:660:5307:3144::9576'


def getUri(resource):
    return f'coap://[{SENSOR_SERVER}]/{resource}'


async def main():
    protocol = await Context.create_client_context()

    uri = getUri('my_res/alarm_accel')
    print(uri)
    request = Message(code=GET, uri=uri)

    try:
        response = await protocol.request(request).response
    except Exception as e:
        print('Failed to fetch resource:')
        print(e)
    else:
        print('Result: %s\n%r' % (response.code, response.payload))


if __name__ == "__main__":
    asyncio.run(main())
