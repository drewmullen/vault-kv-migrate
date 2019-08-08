#!/usr/bin/python3

# This library provides you with modules to manage secrets recursively. Options include:
#
# list, read, migrate, delete
#
# list_recursive: provide a client and the root portion of secrets path, and receive a list of all secrets in that path
# read_recursive: provide a client and the root portion of secrets path, and receive a list of all secrets in that path and their kvs
# migrate_recursive: provide a client and the root portion of secrets path, and receive a list of all secrets in that path and their kvs
# delete_recursive: provide a list of secrets to delete

# TODO: delete_recursive currently expects the kv_list to also contain secret key/values, this should be removed. a list of secrets should be fine
# TODO: verify ssl support
# TODO: accept parameters to work as a command
# TODO: provide action wrappers ('copy', 'move', 'delete')

import hvac
import requests
import urllib3
import ast
import json

requests = requests.Session()
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

## Wrapper methods

def list_recursive(client, path, kv_version):
    kv_list = []
    kv_list = list_path(client, path, kv_version, kv_list)
    kv_list = recursive_path_builder(client, kv_list, kv_version)
    return kv_list


def delete_recursive(client, path):
    kv_list = list_recursive(client, path)
    kv_list = read_secrets_from_list(client, kv_list)
    delete_secrets_from_list(client, kv_list)


def read_recursive(client, path, kv_version):
    kv_list = list_recursive(client, path, kv_version)
    secrets_list = read_secrets_from_list(client, kv_list, kv_version)
    return secrets_list


def migrate_secrets(src_client, dest_client, src_path, dest_path='', kv_version=2):
    if dest_path != '':
        if dest_path[-1] != '/':
            dest_path += '/'
    kv_list = read_recursive(src_client, src_path, kv_version)
    write_secrets_from_list(dest_client, kv_list, dest_path, src_path, kv_version)
    print("Secrets moved: ", len(kv_list))


# Construction Methods

def recursive_path_builder(client, kv_list, kv_version):
    change = 0
    # if any list items end in '/' return 1
    for li in kv_list[:]:
        if li[-1] == '/':
            list_path(client, li, kv_version, kv_list)
            # remove list item ending in '/'
            kv_list.remove(li)
            change = 1
    # new list items added, rerun search
    if change == 1:
        recursive_path_builder(client, kv_list, kv_version)

    return kv_list


def list_path(client, path, kv_version, kv_list=[]):
    if kv_version == 2:
        l = client.secrets.kv.v2.list_secrets(path, mount_point='secret')['data']['keys']
    elif kv_version == 1:
        l = client.secrets.kv.v1.list_secrets(path, mount_point='secret')['data']['keys']
    for li in l:
        kv_list.append(path  + li)
    return kv_list


def read_secrets_from_list(client, kv_list, kv_version):
    for i, li in enumerate(kv_list[:]):
        k = kv_list[i]
        if kv_version == 2:
            v = client.secrets.kv.v2.read_secret_version(k, mount_point='secret')['data']['data']
        elif kv_version == 1:
            v = client.secrets.kv.v1.read_secret(k, mount_point='secret')['data']
        kv_list[i] = {k:v}

    return kv_list


def write_secrets_from_list(client, kv_list, dest_path, src_path, kv_version):
    for li in kv_list:
        sname = list(li)[0]
        short_name = sname.replace(src_path, '')

        if kv_version == 2:
            client.secrets.kv.v2.create_or_update_secret(path=(dest_path + short_name), secret=li[sname])
        elif kv_version == 1:
            client.secrets.kv.v1.create_or_update_secret(path=(dest_path + short_name), secret=li[sname])


# this expects the secret to be in the json blob - need to fix
def delete_secrets_from_list(client, kv_list):
    for li in kv_list:
        sname= str(li.keys()[0])
        client.secrets.kv.v2.delete_metadata_and_all_versions(path=sname)


def main():
    #example run vars
    path = ''
    path2 = 'nested/'
    client = hvac.Client(url='https://127.0.0.1:8200', token='<redacted>', verify=False)#, namespace="ns1")
    client2 = hvac.Client(url='https://127.0.0.1:8200', token='<redacted>', verify=False)#, namespace="kv1")

    #client = hvac.Client(url='https://vault.example.com', token='abc123', verify=False, namespace='namespace/child_namespace/sub_child_namespace')
    migrate_secrets(client, client2, path, path2, kv_version=1)


if __name__ == '__main__':
    main()
