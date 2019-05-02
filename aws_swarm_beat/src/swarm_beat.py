#!/usr/bin/python

import boto3
import json
import time
import docker
import os
import json_logging, logging, sys
from boto3.dynamodb.conditions import Key, Attr
from datetime import datetime, timedelta

try: # Docker env vars
  dynamo_table_suffix = os.environ['DYNAMO_TABLE']
  env = os.environ['ENV']
  prune_hours = os.environ['PRUNE_AFTER_X_HOURS']
  prune_minutes = os.environ['PRUNE_AFTER_X_MIN']
  heartbeat_interval = os.environ['HEARTBEAT_INTERVAL']
  heartbeat_interval = int(heartbeat_interval)

except: # Local development vars
  dynamo_table_suffix = "eu-west-1-swarm-management"
  env = "dev"
  prune_hours = 0
  prune_minutes = 3
  heartbeat_interval = 10

# Resource
dynamodb = boto3.resource('dynamodb')
dynamodb_table_name_expanded = env + "-" + dynamo_table_suffix
dyn_table = dynamodb.Table(dynamodb_table_name_expanded)
docker_client = docker.DockerClient(base_url='unix://var/run/docker.sock')
docker_api_client = docker.APIClient(base_url='unix://var/run/docker.sock')

# Logging
json_logging.ENABLE_JSON_LOGGING = True
json_logging.COMPONENT_ID = "aws-swarm-overseer"
json_logging.COMPONENT_NAME = "aws-swarm-overseer"
json_logging.init()
logger = logging.getLogger("aws-swarm-overseer")
logger.setLevel(logging.INFO)
logger.addHandler(logging.StreamHandler(sys.stdout))

# Check the health of the swarm
def swarm_healthcheck():
  global current_time

  current_dt = datetime.today()
  current_time = current_dt.strftime('%Y-%m-%d-%H:%M:%S')
  swarm_status = docker_api_client.nodes()

  time.sleep(heartbeat_interval)
  for x in swarm_status:
    swarm_node_id = x['ID']
    swarm_node_state = x['Status']['State']
    swarm_role = x['Spec']['Role']
    swarm_addr = x['Status']['Addr']

    # Rewrite to conform to existing naming convention
    if swarm_role == 'manager':
      swarm_role = 'master'

    if swarm_node_state == 'down':
      swarm_remove_stale_nodes(swarm_addr, swarm_role, swarm_node_id)
    else:
      swarm_record_heartbeat(swarm_addr, swarm_role)
      logger.info(swarm_addr + " recorded heartbeat")

# Record a heartbeat
def swarm_record_heartbeat(address, role):
  dyn_table.update_item(
      Key={
          'node_type': role,
          'ip': address
      },
      UpdateExpression="set heartbeat = :r",
      ExpressionAttributeValues={
          ':r': current_time
      },
      ReturnValues="UPDATED_NEW"
  )

# Query the heartbeat for the offline node
def swarm_remove_stale_nodes(address, role, node_id):

  current_date_delta = datetime.today() - timedelta(hours=prune_hours, minutes=prune_minutes)
  current_date_delta_format = current_date_delta.strftime('%Y-%m-%d-%H:%M:%S')

  swarm_query = dyn_table.query(
  KeyConditionExpression=Key('node_type').eq(role) & Key('ip').eq(address)
  )

  try:
    for x in swarm_query['Items']:
      last_heartbeat = x['heartbeat']

      if last_heartbeat < current_date_delta_format:
        logger.info(address + " has been offline since " + last_heartbeat + " exceeding the limit set at " + current_date_delta_format)
        logger.info(address + " Removing this node from the cluster ...")
        # Remove from the local swarm
        docker_api_client.remove_node(
          node_id = node_id
        )
        # Remove from Dynamodb
        dyn_table.delete_item(
          Key={
            'node_type': role,
            'ip': address
          }
        )
      else:
        logger.info(address + " has been offline since " + last_heartbeat)
  except:
    logger.error(address + " No valid heartbeat recorded for this address.  Its most likely joined the cluster and gone offline before a heartbeat could be recorded")

    # This exeception occurs if this script has been run against a cluster with node with an existing 'down' state
    # Remove the node from dynamo and run docker node rm to remove this error

# Validate whether or not the table exist
def aws_check_swarm_dynamo():
  table_names = [table.name for table in dynamodb.tables.all()]

  if dynamodb_table_name_expanded in table_names:
    logger.info("Connected to " + dynamodb_table_name_expanded)
  else:
    logger.error("The table " + dynamodb_table_name_expanded + " is not ready or created yet")

def main():
  aws_check_swarm_dynamo()
  while True:
    swarm_healthcheck()

main()