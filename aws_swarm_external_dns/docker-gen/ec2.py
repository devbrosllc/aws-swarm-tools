#!/usr/bin/python

import boto3
import json
import time

# Vars to parameterize
r53_managed_domain = "google.com"
elb_tag="swarm-dns"

boto_elb = boto3.client('elb')
boto_r53 = boto3.client('route53')
domain_list = []

##
######### LOAD BALANCERS

def find_load_balancers():
  # Define globals
  global lb_short_name
  global lb_long_name
  # Query AWS for load balancers
  lb_describe = boto_elb.describe_load_balancers()
  for names in lb_describe['LoadBalancerDescriptions']:
    #print "INFO: Found " + names['LoadBalancerName']
    lb_short_name = names['LoadBalancerName']
    lb_long_name = names['CanonicalHostedZoneName']
    find_load_balancer_tags(lb_short_name, lb_long_name)


# Find the valid load balancer
def find_load_balancer_tags(lb_short_name, lb_long_name):
  global valid_lb_long_name
  lb_tags = boto_elb.describe_tags(LoadBalancerNames=[lb_short_name])

  for lb_describe_tags in lb_tags['TagDescriptions']:
    if any(data['Key'] == elb_tag for data in lb_describe_tags['Tags']):
      print "[INFO] Found the load balancer [" + lb_long_name + "] with the tag " + "[" + elb_tag + "]"
      valid_lb_long_name = lb_long_name
      # Set a flag if we find a valid load balancer with the correct tag

##
######### RECORDS
def find_r53_hosted_zone():
  # Define global
  global hostedzone_id
  response = boto_r53.list_hosted_zones_by_name(
      #DNSName=r53_managed_domain,
      MaxItems='5'
  )
  for x in response['HostedZones']:
    print x['Id']
    print x['Name']
  #print(json.dumps(response, indent=4, sort_keys=True))
  hostedzone_stripped = response['HostedZones'][0]['Id']
  hostedzone_id = hostedzone_stripped
  #print "[INFO] HostedZoneID " +  r53_managed_domain + " -> " + hostedzone_stripped.strip('/hostedzone/')

def create_r53_hosted_zone(domain):
  # Validate the name against the domain to avoid invalid upsets
  domain_stripped = domain.strip('\n') 
  if r53_managed_domain in domain:
    batch = {
      'Changes': [
        {
          'Action': 'UPSERT',
          'ResourceRecordSet' : {
            'Name' : domain_stripped + ".",
            'Type' : 'CNAME',
            'TTL' : 120,
            'ResourceRecords' : [{'Value': lb_long_name}]
          }
        }
      ]
    }
    boto_r53.change_resource_record_sets(HostedZoneId=hostedzone_id, ChangeBatch=batch)
    print "[INFO] Created " + domain_stripped + " -> " + lb_long_name
  else:
    print "[ERROR] " + domain_stripped + " is not valid, NO RECORD WILL BE CREATED.  Please check your domain name matches the R53_MANAGED_DOMAIN of this container"

##
######### FILE MANAGEMENT

def read_routes():
  # Write the dockergen file to a list
  route_file = open("routes.txt", "r")
  for entry in route_file:
      domain_list.append(entry)
  route_file.close

## Iterate over each domain and call its validation/creation
def assign_domains():
  for gen_domain in domain_list:
    create_r53_hosted_zone(gen_domain)


# def main():
#   read_routes()
#   find_load_balancers()
#   find_r53_hosted_zone()
#   assign_domains()

# main()

find_load_balancers()
find_r53_hosted_zone()