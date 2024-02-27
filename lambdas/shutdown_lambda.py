# This lambda gets invoked via a lifecycle hook at the instance termination, 
# detaches a valid ENI with the instance and then stores the value in the parameter store.

import json
import boto3

def lambda_handler(event, context):
    print("Event: ", event)
    
    ssm_client = boto3.client('ssm')
    ec2_client = boto3.client('ec2')
    autoscaling_client = boto3.client('autoscaling')
    
    #Extract instance ID from the EventBridge event
    instance_id = event['detail']['EC2InstanceId']
    print("instance_id: ",instance_id)
    
    #Fetch the ENI ID   
    parameter_data=extract_parameter_data(ec2_client, instance_id)
    print("Parameters: ", parameter_data)
    
    #Store the ENI in the parameter store
    create_parameter_with_tags(ssm_client, parameter_data)
    
    #Detach the Network Interface
    detach_network_interface(ec2_client, parameter_data)
    
    # Complete the lifecycle hook action to allow the instance to terminate
    asg_name = event['detail']['AutoScalingGroupName']
    lifecycle_hook_name = event['detail']['LifecycleHookName']
    lifecycle_action_token = event['detail']['LifecycleActionToken']
    response = autoscaling_client.complete_lifecycle_action(
        AutoScalingGroupName=asg_name,
        LifecycleHookName=lifecycle_hook_name,
        LifecycleActionToken=lifecycle_action_token,
        LifecycleActionResult='CONTINUE')
    
    return {'statusCode': 200,'body': 'Lifecycle action continued'}

def extract_parameter_data(ec2_client, instance_id):
    response = ec2_client.describe_instances(InstanceIds=[instance_id])
    print("describe_instances: ", response)
    secondary_enis ={}
    reservations = response['Reservations']
    for reservation in reservations:
        instances = reservation['Instances'] 
        for instance in instances:
            availability_zone = instance['Placement']['AvailabilityZone']
            network_interfaces = instance.get('NetworkInterfaces', [])
            for network_interface in network_interfaces:
                if network_interface['Attachment']['DeviceIndex'] != 0:
                    # Exclude primary ENI                   
                    subnet_id = network_interface['SubnetId']
                    eni_id = network_interface['NetworkInterfaceId']
                    attachment_id = network_interface['Attachment']['AttachmentId']
                    secondary_enis = {
                        'SubnetId': subnet_id,
                        'NetworkInterfaceId': eni_id,
                        'AvailabilityZone': availability_zone,
                        'AttachmentId': attachment_id
                    }
                    
                    return secondary_enis

def create_parameter_with_tags(ssm_client, parameter_data):
    if 'NetworkInterfaceId' in parameter_data and parameter_data['NetworkInterfaceId'] is not None:
        tags = [
            { 'Key': 'app',
             'Value': 'bridgegate'
            }, 
            {'Key': 'type', 
             'Value': 'eni'
            }, 
            {'Key': 'subnet',
              'Value': parameter_data['SubnetId']
            }]
        
        # Create the parameter       
        response = ssm_client.put_parameter(
            Name='/bridgegate/eni/'+parameter_data['AvailabilityZone'],
            Value=parameter_data['NetworkInterfaceId'],
            Type='String',
            Tags=tags) 
        print(response)
        
        if response["ResponseMetadata"]["HTTPStatusCode"] == 200:
            print("Parameter Creation successful")
            return True
        else:
            print("Parameter Creation failed")
            return False
    else:
        return False
    
def detach_network_interface(ec2_client, parameter_data):
    if 'AttachmentId' in parameter_data and parameter_data['AttachmentId'] is not None:
        response = ec2_client.detach_network_interface(
            AttachmentId = parameter_data['AttachmentId'],
            Force=True)
        print(response)
        
        if response["ResponseMetadata"]["HTTPStatusCode"] == 200:
            print("Network Interface Detach successful")
            return True
        else:
            print("Network Interface Detach failed")
            return False
    else:
        return False