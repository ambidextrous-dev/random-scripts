# This lambda gets invoked via a lifecycle hook at the instance startup and
# attaches a valid ENI with the instance. The list of ENI's are stored in the parameter store

import json
import boto3

def lambda_handler(event, context):
    print("Event: ", event)
    ec2_client = boto3.client("ec2")
    ssm_client = boto3.client("ssm")
    rg_tagging_client = boto3.client("resourcegroupstaggingapi")
    autoscaling_client = boto3.client('autoscaling')

    # Extract instance ID from the EventBridge event
    instance_id = event["detail"]["EC2InstanceId"]
    print("instance_id: ", instance_id)

    # Extract subnet ID from instance
    subnet_id = get_instance_subnet_id(ec2_client, instance_id)
    print(subnet_id)
    
    tag_filters = [
        {
            "Key": "app",
            "Values": ["bridgegate"]
        },
        {
            "Key": "type", "Values": ["eni"]},
        {"Key": "subnet", "Values": [subnet_id]},
    ]

    # Fetch the parameter name
    parameter_name=get_parameter_name(rg_tagging_client, tag_filters)
    print("parameter_name: ", parameter_name)
    
    # Fetch the ENI Value for the parameter store
    eni_ids=get_eni_id(ssm_client, parameter_name)
    print("ENIID: ", eni_ids)
    
    # Attach ENI to instance
    attach_network_interface(ec2_client, instance_id, eni_ids, 1)
    
    # Remove the ENI from the parameter store
    # if eni_status is True:   
    #     print("Deleting parameter from parameter store")   
    #     ssm_client.delete_parameter(Name=parameter_name)   
    
    # Complete the lifecycle hook action to allow the instance to terminate
    asg_name = event['detail']['AutoScalingGroupName']
    lifecycle_hook_name = event['detail']['LifecycleHookName']
    lifecycle_action_token = event['detail']['LifecycleActionToken']
    response = autoscaling_client.complete_lifecycle_action(
        AutoScalingGroupName=asg_name,
        LifecycleHookName=lifecycle_hook_name,
        LifecycleActionToken=lifecycle_action_token,
        LifecycleActionResult='CONTINUE'
    )
    return {"statusCode": 200, "body": "Lifecycle action continued"}

def attach_network_interface(ec2_client, instance_id, network_interface_ids, device_index):
    for network_interface_id in network_interface_ids:
        try:
            print("network interface id: ", network_interface_id)
            response = ec2_client.attach_network_interface(DeviceIndex=device_index, InstanceId=instance_id, NetworkInterfaceId=network_interface_id.strip(),)
            print(response)
            
            if response["ResponseMetadata"]["HTTPStatusCode"] == 200:
                print("Attachment successful")
                break
            else:
                print("Attachment failed trying next network interface id")
                print(response)
        except Exception as e:
            print(e)
            continue
   
def get_instance_subnet_id(ec2_client, instance_id):
    response = ec2_client.describe_instances(InstanceIds=[instance_id]) 
    subnet_id = response["Reservations"][0]["Instances"][0]["SubnetId"]
    return subnet_id 

def get_parameter_name(rg_tagging_client, tag_filters):
    print(tag_filters)
    valid_parameters = rg_tagging_client.get_resources(TagFilters=tag_filters)
    print("valid-parameters: ", valid_parameters)
    parameter_resource_arn = valid_parameters["ResourceTagMappingList"][0]["ResourceARN"]
    parameter_name = "/" + parameter_resource_arn.split(":")[-1].split("/", 1)[1]
    return parameter_name 

def get_eni_id(ssm_client, parameter_name):
    parameter_response = ssm_client.get_parameter(Name=parameter_name, WithDecryption=True)
    eni_ids = parameter_response["Parameter"]["Value"].split(",")
    print(eni_ids)
    return eni_ids