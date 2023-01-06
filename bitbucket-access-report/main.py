import requests
import json
import csv
import os
from requests.auth import HTTPBasicAuth

#common vars
bitbucketUser = "joe"
bitbucketPassword = "joe"
bitbucket_base_url = "https://bitbucket.company.com/rest/api/1.0/"
limit = "1000"

def generate_groupaccess_report():
    response = json.dumps(requests.get(bitbucket_base_url+"groups?limit="+limit, auth=HTTPBasicAuth(bitbucketUser, bitbucketPassword)).json())
    listOfGroups = json.loads(response)

    group_access_file = open('bb_group_access.csv', 'w')
    csvwriter = csv.writer(group_access_file)
    csvwriter.writerow(["Group", "User Name", "Email Address"])

    for group in listOfGroups['values']:
        userlistResponse = json.dumps(requests.get(bitbucket_base_url+"users?group="+group+"&limit="+limit, auth=HTTPBasicAuth(bitbucketUser, bitbucketPassword)).json())
        userlist = json.loads(userlistResponse)
        if bool(userlist['values']):
            for count, value in enumerate(userlist['values']):
                csvwriter.writerow([group, userlist['values'][count]['displayName'],  userlist['values'][count]['emailAddress']])


def generate_repoaccess_report():
    repo_access_file = open('bb_repo_access.csv', 'w')
    csvwriter = csv.writer(repo_access_file)
    csvwriter.writerow(["Project", "Repository", "Group Name", "Permission"])

    listOfProjectsResponse = json.dumps(requests.get(bitbucket_base_url+"projects?limit="+limit, auth=HTTPBasicAuth(bitbucketUser, bitbucketPassword)).json())
    listOfProjects = json.loads(listOfProjectsResponse)

    for project in listOfProjects['values']:
        repoListResponse = json.dumps(requests.get(bitbucket_base_url+"projects/"+project['key']+"/repos?limit="+limit, auth=HTTPBasicAuth(bitbucketUser, bitbucketPassword)).json())
        repoList = json.loads(repoListResponse)
        for repo in repoList['values']:
            repoPermissionListResponse = json.dumps(requests.get(bitbucket_base_url+"projects/"+project['key']+"/repos/"+repo['slug']+"/permissions/groups"+"?limit="+limit, auth=HTTPBasicAuth(bitbucketUser, bitbucketPassword)).json())
            repoPermissionList = json.loads(repoPermissionListResponse)
            if bool(repoPermissionList['values']):
                for count, group in enumerate(repoPermissionList['values']):
                    if bool(group):
                        csvwriter.writerow([project['key'], repo['slug'], group['group']['name'], group['permission']])


def cleanup():
    os.remove('bb_group_access.csv')
    os.remove('bb_repo_access.csv')

cleanup()
generate_groupaccess_report()
generate_repoaccess_report()