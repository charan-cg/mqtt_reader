import logging
import os
import signal
import time
import asyncio
import gmqtt

STOP = asyncio.Event()

def on_connect(client, flags, rc, properties):
    logging.info('[CONNECTED {}]'.format(client._client_id))

def on_message(client, topic, payload, qos, properties):
    logging.info('[RECV MSG {}] TOPIC: {} PAYLOAD: {} QOS: {} PROPERTIES: {}'
                 .format(client._client_id, topic, payload.decode(), qos, properties))

def on_disconnect(client, packet, exc=None):
    logging.info('[DISCONNECTED {}]'.format(client._client_id))

def assign_callbacks_to_client(client):
    client.on_connect = on_connect
    client.on_message = on_message
    client.on_disconnect = on_disconnect

def ask_exit(*args):
    STOP.set()

async def main(broker_host, broker_port):
    sub_client = gmqtt.Client("mqtt_subscriber")
    assign_callbacks_to_client(sub_client)
    await sub_client.connect(broker_host, broker_port)
    
    # Subscribe
    sub_client.subscribe('/events', qos=1)

    pub_client = gmqtt.Client("mqtt_publisher")
    assign_callbacks_to_client(pub_client)
    await pub_client.connect(broker_host, broker_port)

    # Publish 
    pub_client.publish('/events', '{"sensor_value": 20.2}', qos=1)

    await STOP.wait()
    await pub_client.disconnect()
    await sub_client.disconnect()

if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    logging.basicConfig(level=logging.INFO)

    host = os.environ.get('HOST', 'host.docker.internal')
    port = 1883  

    loop.add_signal_handler(signal.SIGINT, ask_exit)
    loop.add_signal_handler(signal.SIGTERM, ask_exit)

    loop.run_until_complete(main(host, port))