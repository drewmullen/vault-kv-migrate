vault namespace create test
vault secrets enable -ns=test -path=secret kv
export VAULT_NAMESPACE=test
vault kv put secret/test name=test
vault kv put secret/test2/test3 name=test
vault kv put secret/testa/testb/testc name=test
vault kv put secret/testa/testc name=test
vault kv put secret/test/abcd/efgh/ijk/lmno name=test
vault kv put secret/test/abcd/efgh/qrs name=test
vault kv put secret/test2/xyz name=test
vault kv put secret/test/nested/test name=test

unset VAULT_NAMESPACE

echo "wrote 8 secrets"
