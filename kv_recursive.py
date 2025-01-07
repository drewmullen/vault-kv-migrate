#!/usr/bin/python3
import hvac
import requests
import urllib3
import argparse
import logging
import os

# Configure logging

LOG_LEVELS = {
    "INFO": logging.INFO,
    "DEBUG": logging.DEBUG,
}

log_level_name = os.getenv("KV_MIGRATE_LOG", "INFO").upper()  # Default to "INFO"
log_level = LOG_LEVELS.get(log_level_name, logging.INFO)  # Use INFO if invalid level

logging.basicConfig(level=log_level, format='%(asctime)s - %(levelname)s - %(message)s')

# Wrapper methods
def list_recursive(client, path, source_kv_version, source_mount):
    logging.debug(f"Listing secrets recursively at path: {path}, source_kv_version: {source_kv_version}, mount: {source_mount}")
    seed_list = list_path(client, path, source_kv_version, source_mount)
    for i, li in enumerate(seed_list):
        seed_list[i] = (path + li)
    final_list = recursive_path_builder(client, seed_list, source_kv_version, source_mount)
    logging.debug(f"Final list of secrets: {final_list}")
    return final_list

def delete_recursive(client, path, source_kv_version, source_mount):
    logging.info(f"Deleting secrets recursively from path: {path}, source_kv_version: {source_kv_version}, mount: {source_mount}")
    kv_list = list_recursive(client, path, source_kv_version, source_mount)
    delete_secrets_from_list(client, kv_list, source_kv_version, source_mount)
    logging.info(f"Deleted secrets: {kv_list}")

def read_recursive(client, path, source_kv_version, source_mount):
    logging.info(f"Reading secrets recursively from path: {path}, source_kv_version: {source_kv_version}, mount: {source_mount}")
    kv_list = list_recursive(client, path, source_kv_version, source_mount)
    secrets_list = read_secrets_from_list(client, kv_list, source_kv_version, source_mount)
    logging.debug(f"Secrets read: {secrets_list}")
    return secrets_list

def migrate_secrets(src_client, dest_client, src_path, source_mount, dest_mount, dest_path='', source_kv_version=1, destination_kv_version=1):
    logging.info(f"Copying secrets from {src_path} to {dest_path} (source_mount: {source_mount}, dest_mount: {dest_mount})")
    kv_list = read_recursive(src_client, src_path, source_kv_version, source_mount)
    write_secrets_from_list(dest_client, kv_list, dest_path, src_path, destination_kv_version, dest_mount)
    logging.info(f"Copied {len(kv_list)} secrets successfully.")

# Construction Methods
def recursive_path_builder(client, kv_list, source_kv_version, source_mount):
    logging.debug(f"Building recursive path for source_kv_version: {source_kv_version}, mount: {source_mount}")
    change = 0
    for li in kv_list[:]:
        if li[-1] == '/':
            append_list = list_path(client, li, source_kv_version, source_mount)
            for new_item in append_list:
                kv_list.append(li + new_item)
            kv_list.remove(li)
            change = 1
    if change == 1:
        recursive_path_builder(client, kv_list, source_kv_version, source_mount)
    return kv_list

def list_path(client, path, source_kv_version, source_mount):
    logging.debug(f"Listing path: {path}, source_kv_version: {source_kv_version}, mount: {source_mount}")
    if source_kv_version == 2:
        return client.secrets.kv.v2.list_secrets(path, mount_point=source_mount)['data']['keys']
    elif source_kv_version == 1:
        return client.secrets.kv.v1.list_secrets(path, mount_point=source_mount)['data']['keys']

def read_secrets_from_list(client, kv_list, source_kv_version, source_mount):
    logging.debug(f"Reading secrets from list for source_kv_version: {source_kv_version}, mount: {source_mount}")
    for i, li in enumerate(kv_list[:]):
        k = kv_list[i]
        if source_kv_version == 2:
            v = client.secrets.kv.v2.read_secret_version(k, mount_point=source_mount, raise_on_deleted_version=True)['data']['data']
        elif source_kv_version == 1:
            v = client.secrets.kv.v1.read_secret(k, mount_point=source_mount)['data']
        kv_list[i] = {k: v}
    return kv_list

def write_secrets_from_list(client, kv_list, dest_path, src_path, destination_kv_version, dest_mount):
    logging.debug(f"Writing secrets to destination: {dest_path}, source_kv_version: {destination_kv_version}, mount: {dest_mount}")
    for li in kv_list:
        sname = list(li)[0]
        short_name = sname.replace(src_path, '')
        if destination_kv_version == 2:
            client.secrets.kv.v2.create_or_update_secret(
                path=(dest_path + short_name),
                secret=li[sname],
                mount_point=dest_mount
            )
        elif destination_kv_version == 1:
            client.secrets.kv.v1.create_or_update_secret(
                path=(dest_path + short_name),
                secret=li[sname],
                mount_point=dest_mount
            )
    logging.info(f"Secrets written to destination: {len(kv_list)} items.")

def delete_secrets_from_list(client, kv_list, source_kv_version, source_mount):
    logging.debug(f"Deleting secrets from list for source_kv_version: {source_kv_version}, mount: {source_mount}")
    for li in kv_list:
        if source_kv_version == 2:
            client.secrets.kv.v2.delete_metadata_and_all_versions(path=li, mount_point=source_mount)
        elif source_kv_version == 1:
            client.secrets.kv.v1.delete_secret(path=li, mount_point=source_mount)

def ensure_trailing_slash(s):
    if s != '':
        if s[-1] != '/':
            s += '/'
    return s

def main():
    pass

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Recursively interact with Hashicorp Vault KV mount')
    parser.add_argument('action', choices=['copy', 'move', 'delete', 'list', 'read', 'count'], default='list', metavar='ACTION')
    parser.add_argument('--tls-skip-verify', action='store_false')
    parser.add_argument('--source-path', '-s', default='')
    parser.add_argument('--source-url', '-su', required=True)
    parser.add_argument('--source-token', '-st', required=True)
    parser.add_argument('--source-namespace', '-sns', default='')
    parser.add_argument('--source-mount', '-sm', default='kv-v2')
    parser.add_argument('--destination-path', '-d')
    parser.add_argument('--destination-url', '-du')
    parser.add_argument('--destination-token', '-dt')
    parser.add_argument('--destination-namespace', '-dns', default='')
    parser.add_argument('--source-kv-version', '-skv', type=int, default=2, choices=[1, 2])
    parser.add_argument('--destination-kv-version', '-dkv', type=int, default=2, choices=[1, 2])
    parser.add_argument('--destination-mount', '-dm', default='kv-v2')
    args = parser.parse_args()
    logging.debug("Script started with arguments: %s", args)

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
                args.source_kv_version,
                args.destination_kv_version
        )
    elif args.action == 'list':
        print(list_recursive(source_client, args.source_path, args.source_kv_version, args.source_mount))
    elif args.action == 'count':
        print(len(list_recursive(source_client, args.source_path, args.source_kv_version, args.source_mount)))
    elif args.action == 'read':
        print(read_recursive(source_client, args.source_path, args.source_kv_version, args.source_mount))
    elif args.action == 'delete':
        delete_recursive(source_client, args.source_path, args.source_kv_version, args.source_mount)
    elif args.action == 'move':
        migrate_secrets(
            source_client,
            destination_client,
            args.source_path,
            args.source_mount,
            args.destination_mount,
            args.destination_path,
            args.source_kv_version,
            args.destination_kv_version
        )
        delete_recursive(source_client, args.source_path, args.source_kv_version, args.source_mount)
