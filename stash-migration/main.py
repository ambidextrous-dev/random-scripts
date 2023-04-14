import requests
import git
import stashy
import urllib3
from stashy.errors import NotFoundException

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# stash information
STASH_URL = "https://stash.company.com/"
STASH_USERNAME = "username"
STASH_PASSWORD = "CHANGEME"

# bitbucket information
BITBUCKET_URL = "https://bitbucket.company.com/"
BITBUCKET_USERNAME = "username"
BITBUCKET_PASSWORD = "CHANGEME"

BB_BASE_URL = "https://bitbucket.company.com"

def getBitBucket():
    try:
        return stashy.connect(BITBUCKET_URL, BITBUCKET_USERNAME, BITBUCKET_PASSWORD)
    except:
        print("Unable to connect to BitBucket. Check URL and credentials")


def getStash():
    try:
        return stashy.connect(STASH_URL, STASH_USERNAME, STASH_PASSWORD)
    except:
        print("Unable to connect to Stash. Check URL and credentials")


def createBitBucketProjectIfNotExists(project_key, project_name):
    bitbucket = getBitBucket()
    bb_key = project_key
    try:
        bitbucket.projects.get(project_key)
        print("Stash Project already present in BitBucket, retrying with appending chars")
        bb_key = createBitBucketProjectIfNotExists(
            "ST" + project_key, "STASH_"+project_name)
    except NotFoundException:
        print("Stash Project not present in BitBucket, creating")
        response = bitbucket.projects.create(project_key, project_name)
        bb_key = response['key']
    finally:
        return bb_key

def populateBitBucketRepo(stash_repo, stash_repo_url, bb_repo_url):
    localRepo = git.Repo.clone_from(stash_repo_url, './' + stash_repo['name'])
    remoteBranches = localRepo.remote().fetch()
    
    # pull all the branches
    for r in remoteBranches:
        print(r.name)
        if str(r.name) != 'origin/HEAD':
            # select the branch
            localGit = git.Git('./' + stash_repo['name'])
            localGit.checkout(str(r.name).replace('origin/', ''))
            localGit.pull()

    # push to bitbucket
    remote = localRepo.create_remote('bitbucket', url=bb_repo_url)
    for r in remoteBranches:
        remote.push(refspec='{}:{}'.format(str(r.name).replace('origin/', ''), str(r.name).replace('origin/', '')))

    print("Migrated Repo - ", stash_repo_url, " to ", bb_repo_url )

def getRepoHttpURL(repoResponse):
    for link in repoResponse['links']['clone']:
        if link['name'] == 'http':
            url = link['href']
            break
    return url

def create_bitbucket_repo(stash_repo, bb_project_key, stashRepoURL):
    print("stash url: ", stashRepoURL)
    headers = {'Content-Type': 'application/json'}
    repo_data = '{"name": "' + stash_repo['name'] + '", "scmId": "git", "forkable": true, "defaultBranch" : "master"}'

    repo_response = requests.post(BB_BASE_URL + '/rest/api/1.0/projects/' + bb_project_key + '/repos', 
        headers=headers, data=repo_data, auth=(BITBUCKET_USERNAME, BITBUCKET_PASSWORD),  verify=False)    
    bb_repo_response = repo_response.json()
    bb_repo_url = getRepoHttpURL(bb_repo_response)

    #populate empty repo with data
    populateBitBucketRepo(stash_repo, stashRepoURL, bb_repo_url)


def migraterepos(stash, project_key, project_name):
    # make sure project exists
    bb_project_key = createBitBucketProjectIfNotExists(
        project_key, project_name)
    print("bb_key is: ", bb_project_key)
    bb_project_key = project_key

    # iterate over all the repos in this project
    for repo in stash.projects[project_key].repos.list():
        print("STASH REPO: ", repo)
        stashReponse = repo
        stashRepoURL = getRepoHttpURL(stashReponse)
        create_bitbucket_repo(stashReponse, bb_project_key, stashRepoURL)


def migrateallprojects(stash):
    # iterate over all the projects
    for project in stash.projects:
        # migrate all repos
        migraterepos(stash, project['key'], project['name'])


migraterepos(getStash(), "PROJA", "PROJECTA")