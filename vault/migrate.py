import hvac

old_vault_client = hvac.Client(
    url='https://oldvault.company.com',
    token='xxxxxxxx'
)

new_vault_client = hvac.Client(
    url='https://newvault.company.com',
    token='xxxxxxxxx'
)

vault_secrets = {}

def addKeyToVaultDict(key, value):
    if key not in vault_secrets:
        vault_secrets[key] = value
    elif isinstance(vault_secrets[key], list):
        vault_secrets[key].append(value)
    else:
        vault_secrets[key] = [vault_secrets[key], value]

def listSecrets(vault, secret_engine, path):
    list_response = None
    try:
        list_response = vault.secrets.kv.v2.list_secrets(
            path=path,
            mount_point=secret_engine
        )
    except hvac.exceptions.InvalidPath:
        #ignore secret engine if empty
        print("Empty Secret Engine - ", secret_engine, " - ", path)

    return list_response

def listAllVaultSecrets(vault, secret_engine, path="/"):
    list_response = listSecrets(vault, secret_engine, path)

    if list_response is None:
        return
    else:
        keys = list_response['data']['keys']
        for key in keys:
            if key[-1] == "/":
                listAllVaultSecrets(vault, secret_engine, path + key)
            else:
                addKeyToVaultDict(secret_engine, path + key)

def listVaultSecretEngines(vault):
    _temp = []
    backends = vault.sys.list_mounted_secrets_engines()['data'].keys()
    for key in backends:
        _temp.append(key.rstrip('/'))

    return _temp

def getVaultSecrets(vault):
    secret_engines = []

    # List All Secret Engines in the Vault
    secret_engines = listVaultSecretEngines(vault)

    for x in range(len(secret_engines)):
        listAllVaultSecrets(vault, secret_engines[x], "/")

    return vault_secrets

def readSecret(vault, secret_engine, secret):
    read_response = vault.secrets.kv.v2.read_secret_version(
        path=secret,
        mount_point=secret_engine,
        raise_on_deleted_version=True
    )
    secret_value = read_response['data']['data']
    return secret_value

def createSecretEngine(vault, path):
    vault.sys.enable_secrets_engine(
        backend_type='kv',
        version=2,
        path=path + "/"
    )

def writeSecret(vault, secret_engine, secretPath, secret):
    try:
        # check if secret engine exists, if not create first
        secretEngines = listVaultSecretEngines(vault)

        if secret_engine not in secretEngines:
            createSecretEngine(vault, secret_engine)
            print("Secret Engine created - ", secret_engine)

        vault.secrets.kv.create_or_update_secret(
            path=secretPath,
            mount_point=secret_engine,
            secret=secret
        )
    except Exception as e:
        print("Some error occurred in writing secret", e)


def migrateVaultSecrets(old_vault, new_vault):
    try:
        secret_list = getVaultSecrets(old_vault)
        for key in secret_list:
            for secretpath in secret_list[key]:
                secret_value = readSecret(old_vault, key, secretpath)
                writeSecret(new_vault, key, secretpath, secret_value)
        print("Secrets migrated successfully")
    except Exception as e:
        print("Some Error occured in migrating secrets", e)


migrateVaultSecrets(old_vault=old_vault_client, new_vault=new_vault_client)