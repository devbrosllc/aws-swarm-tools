#!/usr/bin/python

import boto3
import json
import time

dynamo_table = os.environ['DYNAMO_TABLE']
env = os.environ['ENV']

dynamodb = boto3.client('dynamodb')
dynamodb_table_name = env + "-" + dynamo_table

def aws_create_dynamodb():
  # Lookup existing tables
  existing_tables = dynamodb.list_tables()['TableNames']
  if dynamodb_table_name not in existing_tables:
    dynamodb.create_table(
        TableName=dynamodb_table_name,
        KeySchema=[
            {
                'AttributeName': 'node_type',
                'KeyType': 'HASH'
            },
            {
                'AttributeName': 'ip',
                'KeyType': 'RANGE'
            }
        ],
        AttributeDefinitions=[
            {
                'AttributeName': 'node_type',
                'AttributeType': 'S'
            },
            {
                'AttributeName': 'ip',
                'AttributeType': 'S'
            },

        ],
        ProvisionedThroughput={
            'ReadCapacityUnits': 1,
            'WriteCapacityUnits': 1
        }
    )

  else:
    print "INFO: The dynamoDB table " + dynamodb_table_name + " already exists"
