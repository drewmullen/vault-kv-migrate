#!/usr/bin/python3

import hvac
import requests
import urllib3
import argparse


# Wrapper methods


def list_recursive(client, path, kv_version, source_mount):
    seed_list = list_path(client, path, kv_version, source_mount)
    for i, li in enumerate(seed_list):
        seed_list[i] = (path + li)
    final_list = recursive_path_builder(client, seed_list, kv_version, source_mount)
    return final_list


def delete_recursive(client, path, kv_version, source_mount):
    kv_list = list_recursive(client, path, kv_version, source_mount)
    delete_secrets_from_list(client, kv_list, kv_version, source_mount)


def read_recursive(client, path, kv_version, source_mount):
    kv_list = list_recursive(client, path, kv_version, source_mount)
    secrets_list = read_secrets_from_list(client, kv_list, kv_version, source_mount)
    return secrets_list


def migrate_secrets(src_client, dest_client, src_path, source_mount, dest_mount, dest_path='', kv_version=1):
    kv_list = read_recursive(src_client, src_path, kv_version, source_mount)
    write_secrets_from_list(dest_client, kv_list, dest_path, src_path, kv_version, dest_mount)
    print("Secrets copied: ", len(kv_list))


# Construction Methods

def recursive_path_builder(client, kv_list, kv_version, source_mount):
    change = 0
    # if any list items end in '/' return 1
    for li in kv_list[:]:
        if li[-1] == '/':
            append_list = list_path(client, li, kv_version, source_mount)
            for new_item in append_list:
                kv_list.append(li + new_item)
            # remove list item ending in '/'
            kv_list.remove(li)
            change = 1
    # new list items added, rerun search
    if change == 1:
        recursive_path_builder(client, kv_list, kv_version, source_mount)

    return kv_list


def list_path(client, path, kv_version, source_mount):
    if kv_version == 2:
        return client.secrets.kv.v2.list_secrets(path, mount_point=source_mount)['data']['keys']
    elif kv_version == 1:
        return client.secrets.kv.v1.list_secrets(path, mount_point=source_mount)['data']['keys']


def read_secrets_from_list(client, kv_list, kv_version, source_mount):
    for i, li in enumerate(kv_list[:]):
        k = kv_list[i]
        if kv_version == 2:
            v = client.secrets.kv.v2.read_secret_version(k, mount_point=source_mount)['data']['data']
        elif kv_version == 1:
            v = client.secrets.kv.v1.read_secret(k, mount_point=source_mount)['data']
        kv_list[i] = {k: v}

    return kv_list


def write_secrets_from_list(client, kv_list, dest_path, src_path, kv_version, dest_mount):
    for li in kv_list:
        sname = list(li)[0]
        short_name = sname.replace(src_path, '')

        if kv_version == 2:
            client.secrets.kv.v2.create_or_update_secret(
                    path=(dest_path + short_name),
                    secret=li[sname],
                    mount_point=dest_mount
                )
        elif kv_version == 1:
            client.secrets.kv.v1.create_or_update_secret(
                path=(dest_path + short_name),
                secret=li[sname],
                mount_point=dest_mount
            )


# this expects the secret to be in the json blob - need to fix
def delete_secrets_from_list(client, kv_list, kv_version, source_mount):
    for li in kv_list:
        if kv_version == 2:
            client.secrets.kv.v2.delete_metadata_and_all_versions(path=li, mount_point=source_mount)
        if kv_version == 1:
            client.secrets.kv.v1.delete_secret(path=li, mount_point=source_mount)


def ensure_trailing_slash(s):
    if s != '':
        if s[-1] != '/':
            s += '/'
    return s


def main():
    pass
    # example run vars
    # path = 'drew/' #must end in /
    # path2 = 'nested/'
    # client = hvac.Client(url='https://127.0.0.1:8200', token='<redacted>', verify=False, namespace="ns1")
    # client2 = hvac.Client(url='https://127.0.0.1:8200', token='<redacted>', verify=False, namespace="kv1")

    # #client = hvac.Client(url='https://vault.example.com', token='abc123', verify=False,
    #    namespace='namespace/child_namespace/sub_child_namespace')
    # migrate_secrets(client, client2, path, path2, kv_version=1)


if __name__ == '__main__':

    parser = argparse.ArgumentParser(description='Recursively interact with Hashicorp Vault KV mount')
    parser.add_argument('action', choices=['copy', 'move', 'delete', 'list', 'read'], default='list', metavar='ACTION')
    parser.add_argument('--tls-skip-verify', action='store_false')
    parser.add_argument('--source-path', '-s', default='')
    parser.add_argument('--source-url', '-su', required=True)
    parser.add_argument('--source-token', '-st', required=True)
    parser.add_argument('--source-namespace', '-sns', default='')
    parser.add_argument('--source-mount', '-sm', default='secret')
    parser.add_argument('--destination-path', '-d')
    parser.add_argument('--destination-url', '-du')
    parser.add_argument('--destination-token', '-dt')
    parser.add_argument('--destination-namespace', '-dns', default='')
    parser.add_argument('--kv-version', '-kvv', type=int, default=1, choices=[1, 2])
    parser.add_argument('--destination-mount', '-dm', default='secret')

    args = parser.parse_args()

    if not args.destination_path:
        args.destination_path = args.source_path
    if not args.destination_url:
        args.destination_url = args.source_url
    if not args.destination_token:
        args.destination_token = args.source_token

    if not args.tls_skip_verify:
        requests = requests.Session()
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

    args.destination_path = ensure_trailing_slash(args.destination_path)
    args.source_path = ensure_trailing_slash(args.source_path)

    source_client = hvac.Client(
            url=args.source_url,
            token=args.source_token,
            verify=args.tls_skip_verify,
            namespace=args.source_namespace,
            strict_http=True
        )
    destination_client = hvac.Client(
            url=args.destination_url,
            token=args.destination_token,
            verify=args.tls_skip_verify,
            namespace=args.destination_namespace,
            strict_http=True
        )
    if args.action == 'copy':
        migrate_secrets(
                source_client,
                destination_client,
                args.source_path,
                args.source_mount,
                args.destination_mount,
                args.destination_path,
                kv_version=args.kv_version
            )
    elif args.action == 'list':
        print(list_recursive(source_client, args.source_path, args.kv_version, args.source_mount))
    elif args.action == 'read':
        print(read_recursive(source_client, args.source_path, args.kv_version, args.source_mount))
    elif args.action == 'delete':
        delete_recursive(source_client, args.source_path, args.kv_version, args.source_mount)
    elif args.action == 'move':
        migrate_secrets(
            source_client,
            destination_client,
            args.source_path,
            args.source_mount,
            args.destination_mount,
            args.destination_path,
            kv_version=args.kv_version
        )
        delete_recursive(source_client, args.source_path, args.kv_version, args.source_mount)
