import kv_recursive
import pytest
import mock
import hvac

### Tests

## ensure trailing slash

def test_trailing_slash():
    assert kv_recursive.ensure_trailing_slash("test/") == "test/"
    assert kv_recursive.ensure_trailing_slash("test") == "test/"
    assert kv_recursive.ensure_trailing_slash("test/super") == "test/super/"
    assert kv_recursive.ensure_trailing_slash("test/super/") == "test/super/"

## recursive_path_builder

#@mock.patch('kv_recursive.list_path')
#def test_recursive_path_buider(mock_list_path):
#    client = ""
#    kv_list = ['test/', 'test1']
#    kv_version = 1
#    source_mount = 'secret'
#    
#    mock_list_path.return_value = ''
#
#    kv_recursive.recursive_path_builder(client, kv_list, kv_version, source_mount)
#
#    assert kv_recursive.list_path.called
#    # assert kv_recursive.recursive_path_builder.called


#@mock.patch('hvac.api.secrets_engines.kv_v1.list_secrets')
#def test_list_path(mock_kv)
#
#kv_version = 1
#list_path()
#
#
# kv_list has test/, ensure list_path is called then ensure recursive_path_builder is called

# kv_list has no ending /s, ensure neither list_path or recursive_ are called

## list_path

# pass a list with secret/test, mock return to read_secret() and enssure properformat of output

## read_secrets_from_list

# pass a list with secret/test, mock return to read_secret() and enssure properformat of output
