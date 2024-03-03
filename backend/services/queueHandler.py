from flask import Flask, request
import json
import certifi
import paho.mqtt.client as mqtt
from dotenv import load_dotenv
import os
import json
from backend.services.utils import initialize_barber_queue_data, load_json_data, write_json_data

queueHandler = Flask(__name__)

load_dotenv()

# load mock data
initialize_barber_queue_data()
barbers = load_json_data(os.path.join('data', 'barbers.json'))
customers = load_json_data(os.path.join('data', 'customers.json'))

# Callback on connection
def on_connect(client, userdata, flags, rc):
  print(f'Connected (Result: {rc})')
  client.subscribe('enqueueRequest')
  client.subscribe('dequeueRequest')

# Callback when message is received
def on_message(client, userdata, msg):
  print(f'Message received on topic: {msg.topic}. Message: {msg.payload}')
  event = json.loads(msg.payload)
  if msg.topic == 'enqueueRequest':
    handle_enqueue_request(client, event)
  else:
    handle_dequeue_request(client, event)
  client.publish(f'queueUpdate', payload=json.dumps(barbers))

# add customer to queue
def add_to_queue(customer, barberID):
  if customer not in customers:
    customers.append(customer)
    write_json_data(os.path.join('data', 'customers.json'), customers)
  for barber in barbers:
    if barber['id'] == barberID:
      barber['queue'].append(customer)
      write_json_data(os.path.join('data', 'barbers.json'), barbers)
      return
    
def remove_from_queue(customerID, barberID):
  customers.pop(-1)
  for barber in barbers:
    if barber['id'] == barberID:
      barber['queue'] = [customer for customer in barber['queue'] if customer['id'] != customerID]
      write_json_data(os.path.join('data', 'barbers.json'), barbers)
      write_json_data(os.path.join('data', 'customers.json'), customers)
      return
    
def get_queue_position(barberID, customerID):
  print("barberssss", barbers)
  print("customer", customerID)
  for barber in barbers:
    if barber['id'] == barberID:
      queue = barber['queue']
      for i in range(len(queue)):
        if queue[i]['id'] == customerID:
          return i
  return -1

def handle_enqueue_request(client, event):
  customerID = event['customerID']
  barberID = event['barberID']

  for customer in customers:
    if customer['id'] == customerID:
      return
  add_to_queue(customer, barberID)
  responseMsg = json.dumps({"queuePos": get_queue_position(barberID, customerID)})
  client.publish(f'enqueueResponse/{customerID}', payload=responseMsg)


def handle_dequeue_request(client, event):
  customerID = event['customerID']
  barberID = event['barberID']
  for customer in customers:
    if customer['id'] == customerID:
      remove_from_queue(customerID, barberID)
      responseMsg = json.dumps({"message": "You are removed from queue"})
      client.publish(f'dequeueResponse/{customerID}', payload=responseMsg)
      return
  
client = mqtt.Client(transport='websockets')
client.on_connect = on_connect
client.on_message = on_message
client.tls_set(ca_certs=certifi.where())
password = os.getenv('MQTT_PASSWORD')
client.username_pw_set('solace-cloud-client', password)
client.connect('mr-connection-0k3m0vpogo3.messaging.solace.cloud', port=8443)
client.loop_forever()