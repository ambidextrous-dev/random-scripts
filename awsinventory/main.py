import boto3
import xlsxwriter


regions = ['us-east-1', 'us-east-2', 'us-west-1', 'us-west-2']
ec2InstanceCollection = []
eipCollection = []
s3Collection = []
sgCollection = []




workbook = xlsxwriter.Workbook('./awsassets.xls')
worksheet = workbook.add_worksheet('EC2 Instances')
sheetHeaders = ['Name', 'Region', 'InstanceId', 'InstanceType', 'KeyName', 'LaunchTime', 'State', 'Platform', 'SecurityGroups']



#Setup sheet headers
row = 0
col = 0
for h in sheetHeaders:
    worksheet.write(row, col, h)
    col += 1


#Loop through regions
for r in regions:

    #AWS Connections
    ec2Client = boto3.client("ec2", region_name=r)
    s3Client = boto3.client("s3", region_name=r)

    #List EC2 instances 
    instanceList = ec2Client.describe_instances()
    for res in instanceList['Reservations']:
        for i in res['Instances']:
            inst = {}
            inst['Region'] = r
            inst['InstanceId'] =  i['InstanceId']
            inst['InstanceType'] = i['InstanceType']
            inst['KeyName'] = i['KeyName']
            inst['LaunchTime'] = i['LaunchTime']
            inst['State'] = i['State']['Name']
            inst['PlatformDetails'] = i['PlatformDetails']
            inst['PrivateDnsName'] = i['PrivateDnsName']
            inst['PrivateIpAddress'] = i['PrivateIpAddress']
            inst['SubnetId'] = i['SubnetId']
            inst['VpcId'] = i['VpcId']
            inst['SecurityGroups'] =[]
            if 'Tags' in i:
                for t in i['Tags']:
                    if 'Key' in t and t['Key'] == 'Name':
                        inst['Name'] = t['Value']
                    else:
                        inst['Name'] = 'notTagged'
            else:
                inst['Name'] = 'notTagged'

            for sg in i['SecurityGroups']:
                inst['SecurityGroups'].append(sg['GroupId'])
            
            ec2InstanceCollection.append(inst)

    #List EIPs for each Region
    eipList = ec2Client.describe_addresses()
    for ip in eipList['Addresses']:
        eipItem = {}
        eipItem['PublicIp'] = ip['PublicIp']
        eipItem['AllocationId'] = ip['AllocationId']
        eipItem['Region'] = r
        if 'AssociationId' in ip:
            eipItem['AssociationId'] = ip['AssociationId']
            eipItem['NetworkInterfaceId'] = ip['NetworkInterfaceId']
            eipItem['PrivateIpAddress'] = ip['PrivateIpAddress']
        if 'InstanceId' in ip:
            eipItem['InstanceId'] = ip['InstanceId']
        eipCollection.append(eipItem)

print(ec2InstanceCollection)   

'''
inst['Region'] = r
            inst['InstanceId'] =  i['InstanceId']
            inst['InstanceType'] = i['InstanceType']
            inst['KeyName'] = i['KeyName']
            inst['LaunchTime'] = i['LaunchTime']
            inst['State'] = i['Monitoring']['State']
            inst['PlatformDetails'] = i['PlatformDetails']
'''




for ec2 in ec2InstanceCollection:
    col = 0
    row += 1
    worksheet.write(row, col, ec2['Name'])
    col +=1
    worksheet.write(row, col, ec2['Region'])
    col +=1 
    worksheet.write(row, col, ec2['InstanceId'])
    col +=1
    worksheet.write(row, col, ec2['InstanceType'])
    col +=1
    worksheet.write(row, col, ec2['KeyName'])
    col +=1
    worksheet.write(row, col, str(ec2['LaunchTime']))
    col +=1
    worksheet.write(row, col, ec2['State'])
    col +=1
    worksheet.write(row, col, ec2['PlatformDetails'])
    col +=1
    sg = ''
    for s in ec2['SecurityGroups']:
        sg += s+'\n'
    worksheet.write(row, col, sg)
    col +=1


print(eipCollection)
#    for eip in eipList
    #List EC2 security groups
#    ec2Client.decsribe


#List S3 Buckets


#Write Workbook
workbook.close()