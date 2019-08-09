import argparse

parser = argparse.ArgumentParser(description='Recursively interact with Hashicorp Vault KV mount')
parser.add_argument('action', choices=['copy','move','delete', 'list'], default='copy', metavar='ACTION')
parser.add_argument('--tls-skip-verify', action='store_false')
parser.add_argument('--source-path', '-s', default='')
parser.add_argument('--source-url', '-su', required=True)
parser.add_argument('--source-token', '-st', required=True)
parser.add_argument('--source-namespace', '-sns')
parser.add_argument('--source-mount', '-sm', default='secret')
parser.add_argument('--destination-path', '-d')
parser.add_argument('--destination-url', '-du')
parser.add_argument('--destination-token', '-dt')
parser.add_argument('--destination-namespace', '-dns')
parser.add_argument('--kv-version', '-kvv', type=int, default=1)
parser.add_argument('--destination-mount', '-dm', default='secret')

args = parser.parse_args()

if not args.destination_path:
    args.destination_path = args.source_path
if not args.destination_url:
    args.destination_url = args.source_url
if not args.destination_token:
    args.destination_token = args.source_token


print(args)