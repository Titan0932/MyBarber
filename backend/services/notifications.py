from flask import Flask, request
import json
import certifi
import paho.mqtt.client as mqtt
from dotenv import load_dotenv
import os
import smtplib

server1 = Flask(__name__)

load_dotenv()

emailObj = {
  "sender" : 'dev0932@outlook.com',
  "message" : ""
}



# Callback on connection
def on_connect(client, userdata, flags, rc):
  print(f'Connected (Result: {rc})')

  # See: https://docs.solace.com/Open-APIs-Protocols/MQTT/MQTT-Topics.htm
  client.subscribe('customerTurn')



# Callback when message is received
def on_message(client, userdata, msg):
  print(f'Message received on topic: {msg.topic}. Message: {msg.payload}')
  eventObj = json.loads(msg.payload)
  notifiedUser = {
    "email": eventObj["email"]
  }
  #  GIve notification
  if(msg.topic == 'customerTurn'):
    try:
      server = smtplib.SMTP('smtp-mail.outlook.com', 587)
      server.starttls()  # Upgrade the connection to a secure one using TLS
      server.login('dev0932@outlook.com', 'outlook!')
      emailObj["message"] = "Dear Customer,\n It's your turn in the queue!! \n - MyBarbers"
      print(emailObj["message"] )
      server.sendmail(emailObj["sender"], notifiedUser["email"], emailObj["message"])
      server.quit()
      print("Successfully sent email")
    except smtplib.SMTPException:
      print("Error: unable to send email")
    except Exception as e:
      print(e)

  # client.publish('notification', payload='HELLO FROM NOTIFICATION SERVER')



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