#!/usr/bin/python

import boto3
import json
import time
import docker
import requests
import random
import os
from boto3.dynamodb.conditions import Key, Attr

# Vars to push through
dynamo_table_suffix = os.environ['DYNAMO_TABLE']
env = os.environ['ENV']
role = os.environ['ROLE']

swarm_active_master_ips = []
swarm_active_nodes = []

# Resource
dynamodb = boto3.resource('dynamodb')
dynamodb_table_name_expanded = env + "-" + dynamo_table_suffix
dyn_table = dynamodb.Table(dynamodb_table_name_expanded)
docker_client = docker.DockerClient(base_url='unix://var/run/docker.sock')
docker_api_client = docker.APIClient(base_url='unix://var/run/docker.sock')

# Create a swarm
def swarm_create_cluster():
  
  docker_client.swarm.init(
      advertise_addr='eth0',
      force_new_cluster=False
  )
  print "Swarm created"

  # Locally store the tokens and write then to dyanmo
  service = docker_api_client.inspect_swarm()
  global swarm_master_token
  global swarm_worker_token
  swarm_master_token = service['JoinTokens']['Manager']
  swarm_worker_token = service['JoinTokens']['Worker']
  aws_swarm_write_type()


# Join an existing cluster
def swarm_join_cluster(swarm_active_master_ips, token):

  # Pass a list of masters and attempt to connect
  print "Joining the existing cluster as a " + role
  docker_client.swarm.join(
      remote_addrs=swarm_active_master_ips, 
      join_token=token,
      listen_addr='0.0.0.0:5000', advertise_addr='eth0:5000'
  )
  aws_swarm_write_type()


# Validate whether or not the table exist
def aws_check_swarm_dynamo():
  table_names = [table.name for table in dynamodb.tables.all()]

  if dynamodb_table_name_expanded in table_names:
      print dynamodb_table_name_expanded + " Exists!"
  else:
      print('Table is not ready, or not created')

# Gather data from Dynamo
def aws_swarm_precheck():
  global swarm_query
  global swarm_master_token
  global swarm_worker_token

  # Check the master details
  swarm_query = dyn_table.query(
  KeyConditionExpression=Key('node_type').eq('master')
  )

  # Check the worker details, reduce reads by limiting this to workers
  if role == 'worker':
    swarm_worker_query = dyn_table.query(
    KeyConditionExpression=Key('node_type').eq('worker')
    )
    for sq_worker in swarm_worker_query['Items']:
      swarm_active_nodes.append(sq_worker['node_name'])

  #print (json.dumps(swarm_query, indent=4, sort_keys=True))
  
  for sq_all in swarm_query['Items']:
    swarm_active_master_ips.append(sq_all['ip'] + ":2377")
    swarm_active_nodes.append(sq_all['node_name'])
    swarm_master_token=sq_all['manager_token']
    swarm_worker_token=sq_all['worker_token']

  # Evaluate whether in the list of roles whether or not my name is registered
  if local_node_name in swarm_active_nodes:
    print local_node_name + " I'm already registered as a " + role
  else:
    print "Not found, lets register"
    aws_swarm_registration(role)

# Evaluate what to register as
def aws_swarm_registration(role):

  # Create a cluster if its empty
  if swarm_query['Items'] == []:
    if role == 'master':
      print "Empty cluster found - creating a new swarm"
      swarm_create_cluster()
    elif role == 'worker':
      print "No swarm masters currently active - waiting for something to become active"
    else:
      print "Invalid role specified - Please ensure you have set the role correctly"
      quit()

  # Join a cluster as another master token
  elif role == 'master':
    swarm_join_cluster(swarm_active_master_ips, swarm_master_token)

  # Join the cluster as a worker token
  elif role == 'worker':
    swarm_join_cluster(swarm_active_master_ips, swarm_worker_token)

  # No correct role
  else:
    print "Invalid role specified - Please ensure you have set the role correctly"
    quit()

# Work out locals
def local_whoami():
  global local_address
  global local_node_name

  # Get our AWS IP, Nodename
  try:
    local_address = requests.get('http://169.254.169.254/latest/meta-data/local-ipv4', verify=False, timeout=1)
    local_node_name = requests.get('http://169.254.169.254/latest/meta-data/instance-id', verify=False, timeout=1)
    local_address = local_address.text
    local_node_name = local_node_name.text
  except: 
    local_address='127.0.0.1'
    local_node_name='localhost'

# Write node info to dynamo
def aws_swarm_write_type():

  if role == 'master':
    dyn_table.put_item(
        Item={
        'ip': local_address,
        'node_type': role,
        'node_name': local_node_name,
        'manager_token': swarm_master_token,
        'worker_token': swarm_worker_token
          }
        )
    print "Added " + local_address + " to DynamoDB"

  else:
    dyn_table.put_item(
      Item={
      'ip': local_address,
      'node_type': role,
      'node_name': local_node_name
        }
      )
    print "Added " + local_address + " to DynamoDB"

def main():
  # Hacky sleep to avoid a rare race condition between multi masters
  # This shouldn't be an issue as EC2 rarely creates to instances within
  # the exact second, this offset just increases that probability
  time.sleep(random.randint(0,5))
  local_whoami()
  aws_check_swarm_dynamo()
  aws_swarm_precheck()

main()


# whoami
  # Master = 
    # check for swarm, if there is one, join with master token, else
      # create a new swarm
        # publish master IP address
        # publish master and worker tokens

  # Worker =
    # check for swarm, loop waiting for token
      # join as worker with worker key
    


    #  430         salt_return = {}
#   431         salt_return.update({'Error': 'Make sure all args are passed [availability, node_name, role, node_id, version]'})
