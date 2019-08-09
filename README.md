# kv_recursive
a command line tool to interact with Hashicorp Vault kv engine recursively

## Actions Implemented

- `list`
- `read`
- `copy`
- `move`
- `delete`

## Execution Examples

Example of copying the root secret/ kv mount secrets to a namespace "teama"
```
python kv_recursive.py copy \
--source-url "https://127.0.0.1:8200" \
--source-token "<redacted>" \
--destination-namespace "teama"
```

List secrets
```
python kv_recursive.py read \
--source-url "https://127.0.0.1:8200" \
--source-token "<redacted>" \
```
## What are the "path" arguments?

This code allows you to define a subset of your kv mount via pathing. so you can specify not only the kv mount but a subset of secrets in that mount and only interact with those.

```
vault list -ns=kvs secret/
Keys
----
drew/
frew
```

For example, i can run a copy and pass the `--source-path "drew"` and it will start the recursive search at `drew/*`; `frew` will be ignored!

```
python kv_recursive.py copy \
--source-url "https://127.0.0.1:8200" \
--source-token "<redacted>" \
--source-namespace "kvs"
--source-path "drew" 
```

The same works with `--destination-path` except the write will start at the path you provie.

## Arguments:

| name                  | syntax                        |     default    | required? | choices                        | desc.                                                                          |
|-----------------------|-------------------------------|:--------------:|:---------:|--------------------------------|--------------------------------------------------------------------------------|
| action                |                               |      list      |     *     | copy, move, delete, list, read | action to perform                                                              |
| skip tls verification | --tls-skip-verify             |                |           |                                |                                                                                |
| source path           | --source-path, -s             |       ''       |     *     |                                | kv path to use as root for recursion lookup                                    |
| source url            | --source-url, -su             |                |     *     |                                | FQDN of vault url with port where kvs are sourced from                         |
| source token          | --source-token, -st           |                |     *     |                                | token used for read authorization in source vault                              |
| source namespace      | --source-namespace, -sns      |       ''       |           |                                | namespace where kv resides. leave empty if kv mount is in root                 |
| source mount          | --source-mount, -sm           |     secret     |           |                                | name of the kv mount to read from                                              |
| destination path      | --destination-path, -d        |  --source-path |           |                                | kv path to use as root for recursion write. defaults to same as --source-path. |
| destination url       | --destination-url, -du        |  --source-url  |           |                                | FQDN of vault url with port where kvs are written to. default is --source-url  |
| destination token     | --destination-token, -dt      | --source-token |           |                                | token used for write authorization in source vault. default is --source-token  |
| destination namespace | --destination-namespace, -dns |                |           |                                | namespace to write kvs. leave empty if kv mount is in root                     |
| destination mount     | --destination-mount, -dm      |                |           |                                | name of the kv mount to write to. default is same as --source-mount            |
| kv version            | --kv-version, -kvv            |        1       |           |                                | which kv version secrets are stored as. will be written using same version     |
