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
    
def generate_barber_queue_data():
  for i in range(0, 5):
    barbers[0]['queue'].append(customers[i])
    update_wait_times(barbers[0]['queue'])
  for i in range(0, 2):
    barbers[1]['queue'].append(customers[i+5])
    update_wait_times(barbers[1]['queue'])
  for i in range(0, 6):
    barbers[2]['queue'].append(customers[i+7])
    update_wait_times(barbers[2]['queue'])
  return barbers

# Function to update wait times for all customers in a barber's queue
def update_wait_times(queue):
  total_wait_time = 0
  for customer in queue:
    customer['waitTime'] = total_wait_time
    total_wait_time += 30

def test_generate_barber_queue_data():
  generate_barber_queue_data()
  for barber in barbers:
    print(f"Barber {barber['fname']} {barber['lname']} (ID: {barber['id']}) has the following queue:")
    for customer in barber['queue']:
      print(f"Customer {customer['fname']} {customer['lname']} (ID: {customer['id']}) has a wait time of {customer['waitTime']} minutes")
    print()
  
if __name__ == '__main__':
  test_generate_barber_queue_data()

