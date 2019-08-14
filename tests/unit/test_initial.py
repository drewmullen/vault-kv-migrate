import kv_recursive
import mock


class TestKV(object):

    def setup_method(self, method):
        # anytime client is called we can pass hvacclient
        self.hvacclient = mock.patch('hvac.Client').start()

    def teardown_method(self, method):
        self.hvacclient.stop()

    def test_trailing_slash(self):
        assert kv_recursive.ensure_trailing_slash("test/") == "test/"
        assert kv_recursive.ensure_trailing_slash("test") == "test/"
        assert kv_recursive.ensure_trailing_slash("test/super") == "test/super/"
        assert kv_recursive.ensure_trailing_slash("test/super/") == "test/super/"

    # list_path

    def test_list_path_v2(self):
        self.hvacclient.secrets.kv.v2.list_secrets.return_value = {'data': {'keys': ['test2']}}
        kv_list = kv_recursive.list_path(
                self.hvacclient,
                path='',
                kv_version=2,
                source_mount='secret',
                kv_list=['test']
            )

        assert kv_list == ['test', 'test2']
        assert self.hvacclient.secrets.kv.v2.list_secrets.called

    def test_list_path_v1(self):
        self.hvacclient.secrets.kv.v1.list_secrets.return_value = {'data': {'keys': ['test2']}}
        kv_list = kv_recursive.list_path(
                self.hvacclient,
                path='',
                kv_version=1,
                source_mount='secret',
                kv_list=['test']
            )

        assert kv_list == ['test', 'test2']
        assert self.hvacclient.secrets.kv.v1.list_secrets.called

    def test_read_secrets_v2(self):
        self.hvacclient.secrets.kv.v2.read_secret_version.return_value = {'data': {'data': {"name": "drew"}}}
        secrets = kv_recursive.read_secrets_from_list(
            self.hvacclient,
            kv_list=['test', 'test2'],
            kv_version=2,
            source_mount='secret'
        )
        assert secrets == [{'test': {'name': 'drew'}}, {'test2': {'name': 'drew'}}]

    def test_read_secrets_v1(self):
        self.hvacclient.secrets.kv.v1.read_secret.return_value = {'data': {"name": "drew"}}
        secrets = kv_recursive.read_secrets_from_list(
            self.hvacclient,
            kv_list=['test', 'test2'],
            kv_version=1,
            source_mount='secret'
        )
        assert secrets == [{'test': {'name': 'drew'}}, {'test2': {'name': 'drew'}}]

    def test_write_secrets_from_list_v2(self):
        kv_recursive.write_secrets_from_list(
            self.hvacclient,
            kv_list=[{'test': {'name': 'drew'}}],
            dest_path='',
            src_path='',
            kv_version=2,
            dest_mount='secret'
        )
        assert self.hvacclient.secrets.kv.v2.create_or_update_secret.called

    def test_write_secrets_from_list_v1(self):
        kv_recursive.write_secrets_from_list(
            self.hvacclient,
            kv_list=[{'test': {'name': 'drew'}}],
            dest_path='',
            src_path='',
            kv_version=1,
            dest_mount='secret'
        )
        assert self.hvacclient.secrets.kv.v1.create_or_update_secret.called

    def test_delete_secrets_from_list_v2(self):
        kv_recursive.delete_secrets_from_list(
            self.hvacclient,
            kv_list=['test', 'test2'],
            kv_version=2,
            source_mount='secret'
        )
        assert self.hvacclient.secrets.kv.v2.delete_metadata_and_all_versions.called

    def test_delete_secrets_from_list_v1(self):
        kv_recursive.delete_secrets_from_list(
            self.hvacclient,
            kv_list=['test', 'test2'],
            kv_version=1,
            source_mount='secret'
        )
        assert self.hvacclient.secrets.kv.v1.delete_secret.called

    @mock.patch('kv_recursive.list_path')
    def test_recusive_path_builder_no_lists(self, mock_list_path):
        kv_recursive.recursive_path_builder(
            self.hvacclient,
            kv_list=['test'],
            kv_version=2,
            source_mount='secret'
        )

        assert not mock_list_path.called
