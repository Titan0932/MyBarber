import json
import os

# Load JSON data from files
def load_json_data(filepath):
  with open(filepath, 'r') as file:
    return json.load(file)
  
customers_filepath = os.path.join('data', 'customers.json')
barbers_filepath = os.path.join('data', 'barbers.json')
customers = load_json_data(customers_filepath)
barbers = load_json_data(barbers_filepath)
    
def write_json_data(filepath, data):
  with open(filepath, 'w') as file:
    json.dump(data, file)

def initialize_barber_queue_data():
  for barber in barbers:
    barber['queue'] = []
  for i in range(0, 5):
    barbers[0]['queue'].append(customers[i])
  for i in range(0, 2):
    barbers[1]['queue'].append(customers[i+5])
  for i in range(0, 6):
    barbers[2]['queue'].append(customers[i+7])
  for i in range (0, 3):
    barbers[3]['queue'].append(customers[i+13])
  for i in range (0, 4):
    barbers[4]['queue'].append(customers[i+16])
  for i in range (0, 1):
    barbers[5]['queue'].append(customers[i+20])
  for i in range (0, 0):
    barbers[6]['queue'].append(customers[i+21])
  write_json_data(barbers_filepath, barbers)

def test_generate_barber_queue_data():
  initialize_barber_queue_data()
  for barber in barbers:
    print(f"Barber {barber['fname']} {barber['lname']} (ID: {barber['id']}) has the following queue:")
    for customer in barber['queue']:
      print(f"Customer {customer['fname']} {customer['lname']} ID: {customer['id']}")
    print()
  
if __name__ == '__main__':
  test_generate_barber_queue_data()

