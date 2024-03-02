from flask import Flask, request
import json
import certifi
import paho.mqtt.client as mqtt
from dotenv import load_dotenv
import os
import json
from backend.services.utils import generate_barber_queue_data, load_json_data

queueHandler = Flask(__name__)

load_dotenv()

# load mock data
barbers = generate_barber_queue_data()
customers = load_json_data(os.path.join('data', 'customers.json'))

# Callback on connection
def on_connect(client, userdata, flags, rc):
  print(f'Connected (Result: {rc})')
  client.subscribe('queueRequest')

# Callback when message is received
def on_message(client, userdata, msg):
  print(f'Message received on topic: {msg.topic}. Message: {msg.payload}')
  event = json.loads(msg.payload)
  customerID = event['customerID']
  for customer in customers:
    if customer['customerID'] == customerID:
      return
  barberID = event['barberID']
  del event['barberID']
  customer = event
  add_to_queue(event, barberID)
  # print("customer: ", customer)

  responseMsg = json.dumps({"waitTime": customer['waitTime'], "queuePos": get_queue_position(barberID, customerID)})

  client.publish(f'{customerID}/queueUpdate', payload=responseMsg)

# add customer to queue
def add_to_queue(customer, barberID):
  customers.append(customer)
  for barber in barbers:
    if barber['barberID'] == barberID:
      last_wait_time = barber['queue'][-1]['waitTime']
      customer['waitTime'] = last_wait_time + 30 # constant so far
      barber['queue'].append(customer)
      return

    
def get_queue_position(barberID, customerID):
  for barber in barbers:
    if barber['barberID'] == barberID:
      queue = barber['queue']
      for i in range(len(queue)):
        if queue[i]['customerID'] == customerID:
          return i
  return -1

client = mqtt.Client(transport='websockets')
client.on_connect = on_connect
client.on_message = on_message
client.tls_set(ca_certs=certifi.where())
password = os.getenv('MQTT_PASSWORD')
client.username_pw_set('solace-cloud-client', password)
client.connect('mr-connection-0k3m0vpogo3.messaging.solace.cloud', port=8443)
client.loop_forever()