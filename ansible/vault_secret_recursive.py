#!/usr/bin/python3

DOCUMENTATION = '''
---
module: vault_secret_recursive
author:  Drew Mullen
short_description: move vault kv secrets from 1 path to another

options:
    vault_url:
        description:
            - URL of the vault to connect to
    token:
        description:
            - token capable of read, write, delete on source paths. if capable of CRUD at destination paths, you only need to pass this param.
    dest_token:
        description:
            - Use if source token and destination token are different. must be capable of read, write, delete at destination paths
    src_namespace:
        description:
            - namespace where secrets currently reside (source)
    src_root_path:
        description:
            - root path to search recursively for secrets (source)
    dest_namespace:
        description:
            - namespace where secrets will be copied to (destination)
    dest_root_path:
        description:
            - root path to write secrets to (destination)
        default:
            - sets default to `src_root_path` which is assuming you want the same path but are moving secrets to a new namespace. you can prefix where you write secrets to the destination using this param.
    action:
        description:
            - action to execute. read returns a list of secret paths with the kv in a dict. copy performs a linux-like copy from src to dest. move performs a linux-like move from src to dest (delets src). delete performs a recursive delete from the src_root_path.
        default: read
        choices: ['read','copy','move','delete']
    verify_ssl:
        description:
            - do you want to verify tls?
        default: false
        choices: ['true', 'false']
    capath:
        description:
            - path to public key for TLS verification. default "/etc/pki/tls/cert.pem"
'''

EXAMPLES = '''
    - name: play example

'''

## TODO
# report if existing?
# option to do only 1?
# add dest_token in case the token to read src has to be different that token to write to dest

from ansible.module_utils.basic import AnsibleModule
import hvac
import json
import ast
import requests
import urllib3
import os
import hvac_kv_recursive

kv_list = []
requests = requests.Session()

def main():
    module = AnsibleModule(
        argument_spec=dict(
            vault_url=dict(required=True, type='str'),
            token=dict(required=True, type='str'),
            action=dict(type='str', choices=['read','copy','move','delete'], default='read'),
            dest_token=dict(type='str', default=None),
            src_namespace=dict(type='str', default=''),
            src_root_path=dict(type='str', default=''),
            dest_namespace=dict(type='str', default=''),
            dest_root_path=dict(type='str', default=None),
            verify=dict(type='bool',default=False),
            capath=dict(type='str', default="/etc/pki/tls/cert.pem")
        ),
        supports_check_mode=False
    )

    url = module.params['vault_url']
    token = module.params['token']
    action = module.params['action']
    dest_token = module.params['dest_token']
    src_namespace = module.params['src_namespace']
    src_root_path = module.params['src_root_path']
    dest_namespace = module.params['dest_namespace']
    dest_root_path = module.params['dest_root_path']
    verify = module.params['verify']
    capath = module.params['capath']

    if dest_token == None:
        dest_token = token
    if dest_root_path == None:
        dest_root_path = src_root_path
    #changed = False

    # verify tls
    if verify:
        if not os.environ.get("REQUESTS_CA_BUNDLE"):
            os.environ["REQUESTS_CA_BUNDLE"] = capath
    else:
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
        requests.verify = False

    # verify trailing '/' in paths, empty shouldnt have '/' though
    if len(src_root_path) > 0:
        if src_root_path[0] == '/':
            src_root_path = ''
        elif src_root_path[-1] != '/':
            src_root_path += '/'

    if len(dest_root_path) > 0:
        if dest_root_path[0] == '/':
            dest_root_path = ''
        elif dest_root_path[-1] != '/':
            dest_root_path += '/'

    # before we do anything, verify the token provided can read, write, and delete to each path

    if action == 'move' or action == 'copy':
        client = pre_check(url, src_namespace, src_root_path, token, verify, module)
        dest_client = pre_check(url, dest_namespace, dest_root_path, dest_token, verify, module)
    else:
        client = pre_check(url, src_namespace, src_root_path, token, verify, module)

    # perform changes

    if action == 'delete':
        hvac_kv_recursive.delete_recursive(client, src_root_path)
        module.exit_json(change=True)
    elif action == 'copy':
        hvac_kv_recursive.migrate_secrets(client, dest_client, src_root_path, dest_root_path)
        module.exit_json(change=True)
    elif action == 'move':
        hvac_kv_recursive.migrate_secrets(client, dest_client, src_root_path, dest_root_path)
        hvac_kv_recursive.delete_recursive(client, src_root_path)
        module.exit_json(change=True)
    # action == 'read'
    else:
        kv_list = []
        kv_list = hvac_kv_recursive.read_recursive(client, src_root_path)
        module.exit_json(changed=False, secret_list=kv_list)


def client_init(url, ns, token, verify):
    return hvac.Client(url=url, verify=verify, namespace=ns,token=token)


# test write, read, delete provided namespace/path return clients
def pre_check(url, namespace, root_path, token, verify, module):
    cur_client = client_init(url, namespace, token, verify)
    testpassword='this is super secret'
    # CRUD test
    try:
        cur_client.secrets.kv.v2.create_or_update_secret(path=root_path + 'vault_test_secret', secret=dict(password=testpassword) )
        testpassword == cur_client.secrets.kv.v2.read_secret_version(path=root_path + 'vault_test_secret')['data']['data']['password']
        cur_client.secrets.kv.v2.delete_metadata_and_all_versions(path=root_path + 'vault_test_secret')
    except:
        module.fail_json(changed=False, msg="error connecting or permissions to vault")

    return cur_client


if __name__ == '__main__':
    main()
