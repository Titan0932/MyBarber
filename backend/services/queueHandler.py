from flask import Flask, request
import json
import certifi
import paho.mqtt.client as mqtt
from dotenv import load_dotenv
import os
import json

server1 = Flask(__name__)

load_dotenv()


# Callback on connection
def on_connect(client, userdata, flags, rc):
  print(f'Connected (Result: {rc})')

  # See: https://docs.solace.com/Open-APIs-Protocols/MQTT/MQTT-Topics.htm
  client.subscribe('queue')
  


# Callback when message is received
def on_message(client, userdata, msg):
  print(f'Message received on topic: {msg.topic}. Message: {msg.payload}')
  event = json.loads(msg.payload)
  # find the di
  responseMsg = json.dumps({"waitTime":10, "queuePos":5})
  # once added to queue, send event to a topic
  client.publish('queueManaged', payload= responseMsg)
#   manage queue


# Set the transport for the client as below
client = mqtt.Client(transport='websockets')

client.on_connect = on_connect
client.on_message = on_message

# Required if using TLS endpoint (mqtts, wss, ssl), remove if using plaintext
# Use Mozilla's CA bundle
client.tls_set(ca_certs=certifi.where())

# Retrieve password
password = os.getenv('MQTT_PASSWORD')
client.username_pw_set('solace-cloud-client', password)

client.connect('mr-connection-0k3m0vpogo3.messaging.solace.cloud', port=8443)

client.loop_forever()