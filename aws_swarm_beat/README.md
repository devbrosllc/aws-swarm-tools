# aws-swarm-beat

## Introduction

A swarm heartbeat/garbage manager for removal of down nodes within a cluster

## Assumptions 

This container is to be used in conjuction with a terraform plan.  Terraform would ideally pass through ENV, ROLE, DYNAMO_TABLE and the REGION 

## Requirements
### Python
Python with appropriate packages installed via pip
* Python 2.7
* Pip
 * docker
 * boto3

### Docker
Alternatively Docker can be used with compose
* Docker
* Docker compose

### AWS

* EC2 with a instance role that has permission to read/write to the relevant DynamoDB
* NOTE: If AWS_ACCESS_KEY_ID & AWS_SECRET_ACCESS_KEY are omit, Boto will default to checking for a IAM role: https://boto3.amazonaws.com/v1/documentation/api/latest/guide/configuration.html

### DynamoDB (Required)

* A DynamoDB instance that conforms with the ENV+

If running the python script locally, please set the following environment vars with a valid attribute:

## Attributes

* ENV=                    * REQUIRED: The environment: dev/ci/staging/prod
* DYNAMO_TABLE=           * REQUIRED: Suffix table name, this is prefixed with the environment
* PRUNE_AFTER_X_HOURS     * OPTIONAL: How many hours before removing a node from the swarm & dynamo. Used in conjunction with PRUNE_AFTER_X_MIN. default: 0
* PRUNE_AFTER_X_MIN       * OPTIONAL: How many minutes before removing a node from the swarm & dynamo. Used in conjunction with PRUNE_AFTER_X_HOURS. default: 3
* HEARTBEAT_INTERVAL      * OPTIONAL: How frequently in to record a heartbeat. Note* This needs to be more frequent than the prune timer. default: 10 seconds
* AWS_ACCESS_KEY=         * OPTIONAL: A key with access to DyanmoDB in the specified region
* AWS_SECRET_ACCESS_KEY=  * OPTIONAL: A access key with access to DynamoDB in the specified region
* AWS_DEFAULT_REGION=     * REQUIRED: A valid AWS region that hosts DynamoDB


## Commands

```docker-compose up --build```

```python src/swarm_init.py```

## Local development

* Run the ../scripts/set_local_env.sh to define your local env vars
* Run the ../scripts/create_dynamo_db.py to create a dynamodb *NOTE: This will use your default AWS credentials from AWSCLI