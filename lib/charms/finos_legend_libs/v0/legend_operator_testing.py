# Copyright 2021 Canonical Ltd.
# See LICENSE file for licensing details.

"""Module defining base testing utilities for the library/child charms."""

import abc
import json
import unittest
from unittest import mock

import yaml
from charms.finos_legend_libs.v0 import legend_operator_base
from ops import model
from ops import testing as ops_testing

# The unique Charmhub library identifier, never change it
LIBID = "e3d6d34826fd4581b2ddb197334f6961"

# Increment this major API version when introducing breaking changes
LIBAPI = 0

# Increment this PATCH version before using `charmcraft publish-lib` or reset
# to 0 if you are raising the major API version
LIBPATCH = 7


TEST_CERTIFICATE_BASE64 = """
MIIDMTCCAhmgAwIBAgIULab4sJerDL5F2FtcQBTxkhPDs1EwDQYJKoZIhvcNAQELBQAwSDELMAkG
A1UEBhMCVVMxCzAJBgNVBAgMAk5ZMQswCQYDVQQHDAJOWTELMAkGA1UECgwCWFgxEjAQBgNVBAMM
CWxvY2FsaG9zdDAeFw0yMTEwMTExNDAyNTdaFw0yMjEwMTExNDAyNTdaMEgxCzAJBgNVBAYTAlVT
MQswCQYDVQQIDAJOWTELMAkGA1UEBwwCTlkxCzAJBgNVBAoMAlhYMRIwEAYDVQQDDAlsb2NhbGhv
c3QwggEiMA0GCSqGSIb3DQEBAQUAA4IBDwAwggEKAoIBAQDGioqT5EnyGbBx1umaS8TwyIFJdr6/
cxcTQsGnBoIiUZLqIS/scaV4A2A1JtntL86qy6YZ2OkMHtUqBOQuUpO8eWHlibH8OFOOOHUKYo0P
xx0XADb9c7BjuBy0ePsJOspueJ1J2BI+/6+7Ueq2M3tqG3ruu5bc0B6nC2Tagj1Siy+ueAJ+MYnx
msy6ZGq0UDzj0+2lPGYTRcZ5atL5qDChDK0LB2gq2/srnFN9a1E4wAnPu6SfT9/7m4SDhMWge/9k
H87yLjN4szvo7B6I6M7r+3+CAR1+OVY00eHDZVds4JkJcfg7x3ata7bQjcGCmPR8u0UZO+6cofaO
WcMkFQ5vAgMBAAGjEzARMA8GA1UdEQQIMAaHBAohFm0wDQYJKoZIhvcNAQELBQADggEBAHUMawM7
68rTVD7PMjQEoAaJ9U7EHNUIX7RiX+/PmPsm9FrW/nsEAOxGVJN6+wYYiSDaH10Yg7T32J+NZQBE
re+M++Qs5SC2FLthNEJHKcN+tEnV9UM4VCg1v6u517qCw+NLXJywYtHSIhtSisL0Z+hRS6GYPPf6
BanzjI7vm6nh29V8Z4VGpH7mRhZ69+AnHRhG7rrV97WuBN3DnPq+YpOgJv6Og5bln1DOndbG+Xb7
3zOuf4sfitPvZKqGF/aZUAhZ3KbCs0NVRCMHSieExEy9APR3xOPGuwBIlfbzO8FhM+k1mkEpQfum
noMqQQqz5jpU2SD5w0+nqOctqS2GvEk=
"""

# NOTE: `legend_operator_base.parse_base64_certificate` is independently unit tested.
TEST_CERTIFICATE = legend_operator_base.parse_base64_certificate(TEST_CERTIFICATE_BASE64)


class BaseFinosLegendTestCharm(legend_operator_base.BaseFinosLegendCharm):
    """Base testing charm with some mocked relations/default values."""

    def __init__(self, framework):
        super().__init__(framework)

    @classmethod
    def _get_relations_test_data(cls):
        return {
            "legend-test-rel-1": {"rel1": "test1"},
            "legend-test-rel-2": {"rel2": "test2"}}

    @classmethod
    def _get_required_relations(cls):
        return ['legend-test-rel-1', 'legend-test-rel-2']

    @classmethod
    def _get_application_connector_port(cls):
        return 7667

    @classmethod
    def _get_ingress_routes(cls):
        return "/legend"

    @classmethod
    def _get_workload_container_name(cls):
        return "legend"

    @classmethod
    def _get_workload_service_names(cls):
        return ["legend-test-service"]

    @classmethod
    def _get_workload_pebble_layers(cls):
        return {
            service_name: {
                "services": {
                    service_name: {
                        "command": "bash -c 'echo yes'"}}}
            for service_name in cls._get_workload_service_names()}

    def _get_jks_truststore_preferences(self):
        return {
            "truststore_path": "/path/to/truststore.jks",
            "truststore_passphrase": "legend-test",
            "trusted_certificates": {
                "testing-cert-1": TEST_CERTIFICATE}}

    def _get_service_configs(self, relations_data):
        return self._get_service_configs_clone(relations_data)

    def _get_service_configs_clone(self, relations_data):
        """Shadow method for `_get_service_configs` to avoid calling it during testing."""
        return {
            "/legend-test-1.json": '{"some": "json"}',
            "/legend-test-2.ini": "[section]\nwith_some = options"}


class BaseFinosLegendCharmTestCase(unittest.TestCase):
    """Base TestCase class for quick test setup.

    This class offers the following functionality:
    * automatically setting up mocks for the utility functions from `legend_operator_base`.
    * skeleton tests which cover all abstract methods which child classes of
      `legend_operator_base.BaseFinosLegendCharm` should have.
    * some utility methods for testing

    To use this class, simply override `_set_up_harness` with your setup of choice.
    Note that the class you pass to the harness must be an instance of
    `BaseFinosLegendTestCharm`.
    Note that neither `begin` nor `begin_with_initial_hooks` are called during `setUp`.
    """

    MOCK_TRUSTSTORE_DATA = "Mock Legend JKS TrustStore data."

    def setUp(self):
        """Sets up the testcase by mocking utility methods and calling `_set_up_harness()`."""
        super().setUp()

        self.patch(legend_operator_base.k8s_svc_patch, 'KubernetesServicePatch')

        self._set_up_utils_mocks()

        self.harness = self._set_up_harness()

    def patch(self, obj, method):
        """Returns a Mock for the given method name."""
        _m = mock.patch.object(obj, method)
        mck = _m.start()
        self.addCleanup(_m.stop)
        return mck

    @classmethod
    @abc.abstractmethod
    def _set_up_harness(cls):
        """Returns an `ops_testing.Harness` instance."""
        raise NotImplementedError("No harness setup implemented.")

    def _set_up_utils_mocks(self):
        """Sets up mocks for all the utility methods in the library."""
        utility_funtions_to_patch = [
            'create_jks_truststore_with_certificates',
            'add_file_to_container',
            'parse_base64_certificate',
            'get_ip_address']
        for item in utility_funtions_to_patch:
            setattr(self, "mocked_%s" % item, self.patch(legend_operator_base, item))
        self.truststore_mock = mock.MagicMock()
        self.truststore_mock.saves.return_value = self.MOCK_TRUSTSTORE_DATA
        self.mocked_create_jks_truststore_with_certificates.return_value = (
            self.truststore_mock)
        self.mocked_add_file_to_container.return_value = True
        self.mocked_parse_base64_certificate.return_value = TEST_CERTIFICATE

    def _emit_container_ready(self):
        container_name = self.harness.charm._get_workload_container_name()
        container = self.harness.model.unit.get_container(container_name)
        getattr(self.harness.charm.on, "%s_pebble_ready" % container_name).emit(container)

    def _test_workload_container(self):
        self.harness.begin_with_initial_hooks()
        self.assertEqual(
            self.harness.charm._workload_container,
            self.harness.model.unit.get_container(
                self.harness.charm._get_workload_container_name()))

    def _test_get_logging_level_from_config(self):
        option_name = "log-level-option"
        self.harness.begin_with_initial_hooks()
        # Test all valid options:
        for log_opt in legend_operator_base.VALID_APPLICATION_LOG_LEVEL_SETTINGS:
            self.harness.update_config({option_name: log_opt})
            self.assertEqual(
                self.harness.charm._get_logging_level_from_config(option_name), log_opt)

        # Invalid test:
        self.harness.update_config({option_name: '13'})
        self.assertIsNone(
            self.harness.charm._get_logging_level_from_config(option_name))

    def _test_get_relation(self):
        self.harness.begin_with_initial_hooks()

        # All relations missing:
        for relation_name in self.harness.charm._get_required_relations():
            self.assertIsNone(
                self.harness.charm._get_relation(relation_name))

        # Progressively add relations:
        relations_test_data = self.harness.charm._get_relations_test_data()
        for relation_name, relation_data in relations_test_data.items():
            self.assertIsNone(self.harness.charm._get_relation(relation_name))
            rel_id = self._add_relation(relation_name, relation_data)
            self.harness.update_config({})
            self.assertTrue(self.harness.charm._get_relation(relation_name, rel_id))

        # Check duplicate relation:
        relation_name = list(relations_test_data.keys())[-1]
        if relation_name:
            # Should work as there's no relation:
            self.assertTrue(self.harness.charm._get_relation(relation_name))
            rel_id = self._add_relation(
                relation_name, relations_test_data[relation_name])
            self.harness.update_config()

            # Should fail without a specific 'relation_id' given:
            self.assertTrue(
                self.harness.charm._get_relation(relation_name, relation_id=rel_id))
            with self.assertRaises(model.TooManyRelatedAppsError):
                self.harness.charm._get_relation(
                    relation_name, relation_id=None, raise_on_multiple_relations=True)
            self.assertIsNone(
                self.harness.charm._get_relation(
                    relation_name, relation_id=None, raise_on_multiple_relations=False))

    def _test_setup_jks_truststore(self):
        self.harness.begin()

        container = mock.MagicMock()
        add_files_mock = self.mocked_add_file_to_container
        add_files_mock.return_value = True

        # Bad inputs:
        self.assertIsInstance(
            self.harness.charm._setup_jks_truststore(container, 13), model.BlockedStatus)
        add_files_mock.assert_not_called()
        self.assertIsInstance(
            self.harness.charm._setup_jks_truststore(container, {}), model.BlockedStatus)
        add_files_mock.assert_not_called()
        self.assertIsInstance(
            self.harness.charm._setup_jks_truststore(
                container, {"truststore_path": "yes"}),
            model.BlockedStatus)
        add_files_mock.assert_not_called()

        # Correct inputs:
        correct_jks_prefs = self.harness.charm._get_jks_truststore_preferences()
        self.assertIsNone(
            self.harness.charm._setup_jks_truststore(container, correct_jks_prefs))
        add_files_mock.assert_called_once_with(
            container, correct_jks_prefs['truststore_path'],
            self.truststore_mock.saves.return_value, raise_on_error=False)

        # JKS trust creation fails:
        add_files_mock = self.mocked_add_file_to_container
        add_files_mock.reset_mock()
        add_files_mock.return_value = True
        self.mocked_create_jks_truststore_with_certificates.side_effect = ValueError
        self.assertIsInstance(
            self.harness.charm._setup_jks_truststore(container, correct_jks_prefs),
            model.BlockedStatus)
        add_files_mock.assert_not_called()

        # Container write fails:
        add_files_mock.return_value = False
        self.mocked_create_jks_truststore_with_certificates.side_effect = None
        self.assertIsInstance(
            self.harness.charm._setup_jks_truststore(container, correct_jks_prefs),
            model.BlockedStatus)
        add_files_mock.assert_called_once_with(
            container, correct_jks_prefs['truststore_path'],
            self.truststore_mock.saves.return_value, raise_on_error=False)

    def _add_relation(self, relation_name, relation_data):
        relator_name = "%s-relator" % relation_name
        rel_id = self.harness.add_relation(relation_name, relator_name)
        relator_unit = "%s/0" % relator_name
        self.harness.add_relation_unit(rel_id, relator_unit)
        self.harness.update_relation_data(
            rel_id, relator_name, relation_data)
        return rel_id

    @mock.patch("ops.testing._TestingPebbleClient.restart_services")
    @mock.patch("ops.testing._TestingPebbleClient.stop_services")
    def _test_relations_waiting(self, _container_stop_mock, _container_restart_mock):
        """Progressively adds relations and tests that charm class behaves accordingly.

        Args:
            _container_stop_mock: mock of `ops.testing._TestingPebbleClient.stop_services`
            _container_restart_mock: mock of `ops.testing._TestingPebbleClient.restart_services`
        """
        def _check_charm_missing_relations(relation_names):
            # We initially expect it to block complaining about missing relations:
            self.assertIsInstance(
                self.harness.charm.unit.status, model.BlockedStatus)
            self.assertEqual(
                self.harness.charm.unit.status.message,
                "missing following relations: %s" % ", ".join(sorted(relation_names)))

            # Services should be called to stop with any non-standard status:
            _container_stop_mock.assert_called_with(
                tuple(self.harness.charm._get_workload_service_names()))

        self.harness.set_leader()
        self.harness.begin_with_initial_hooks()

        # We initially expect it to complain about all relations:
        _check_charm_missing_relations(self.harness.charm._get_required_relations())

        # Check behavior when progressively adding relations:
        added_rels = set()
        required_rels = set(self.harness.charm._get_required_relations())
        for rel_name, rel_data in self.harness.charm._get_relations_test_data().items():
            self._add_relation(rel_name, rel_data)
            added_rels.add(rel_name)
            self.harness.update_config()
            missing_rels = required_rels.difference(added_rels)
            if missing_rels:
                _check_charm_missing_relations(missing_rels)

        trust_prefs = self.harness.charm._get_jks_truststore_preferences()
        self.mocked_create_jks_truststore_with_certificates.assert_has_calls(
            [mock.call(trust_prefs["trusted_certificates"])])

        # Check all config files present:
        container = self.harness.charm.unit.get_container(
            self.harness.charm._get_workload_container_name())
        config_file_write_calls = [
            mock.call(container, path, data, make_dirs=True)
            for path, data in self.harness.charm._get_service_configs_clone({}).items()]
        config_file_write_calls.insert(
            0, mock.call(
                container, trust_prefs["truststore_path"],
                self.MOCK_TRUSTSTORE_DATA, raise_on_error=False))
        self.mocked_add_file_to_container.assert_has_calls(
            config_file_write_calls)

        # By this point, the services configs should have been written and
        # the services should have been started:
        _container_restart_mock.assert_has_calls(
            [mock.call(tuple(self.harness.charm._get_workload_service_names()))])
        self.assertIsInstance(
            self.harness.charm.unit.status, model.ActiveStatus)

    @mock.patch("ops.testing._TestingPebbleClient.restart_services")
    @mock.patch("ops.testing._TestingPebbleClient.stop_services")
    def _test_update_config_gitlab_relation(self, _container_stop_mock, _container_restart_mock):
        self.harness.set_leader()
        self.harness.begin_with_initial_hooks()

        # Setup the URI getter mock,
        mock_get_uris = self.patch(self.harness.charm, '_get_legend_gitlab_redirect_uris')
        fake_callback_uris = ['legendary.callback.url']
        mock_get_uris.return_value = fake_callback_uris

        # Add the gitlab integrator relation and grab its relation ID.
        test_data = self.harness.charm._get_relations_test_data()
        gitlab_rel_name = self.harness.charm._get_legend_gitlab_relation_name()
        gitlab_rel_data = test_data.pop(gitlab_rel_name)
        gitlab_rel_id = self._add_relation(gitlab_rel_name, gitlab_rel_data)

        # Add the rest of the necessary relations.
        for rel_name, rel_data in test_data.items():
            self._add_relation(rel_name, rel_data)
            self.harness.update_config()

        # Assert that the unit is currently active.
        self.assertIsInstance(
            self.harness.charm.unit.status, model.ActiveStatus)

        # Assert that the initial Callback URIs have been set.
        relation_data = self.harness.get_relation_data(gitlab_rel_id, self.harness.charm.app)
        expected_rel_data = {'legend-gitlab-redirect-uris': json.dumps(fake_callback_uris)}
        self.assertDictEqual(expected_rel_data, relation_data)

        # Setup for the config update.
        fake_callback_uris = ['foo.lish']
        mock_get_uris.return_value = fake_callback_uris

        # Update the external-hostname config option and assert that the relation data changed.
        self.harness.update_config({"external-hostname": "foo.lish"})

        relation_data = self.harness.get_relation_data(gitlab_rel_id, self.harness.charm.app)
        expected_rel_data = {'legend-gitlab-redirect-uris': json.dumps(fake_callback_uris)}
        self.assertDictEqual(expected_rel_data, relation_data)

    @mock.patch("ops.testing._TestingPebbleClient.restart_services")
    @mock.patch("ops.testing._TestingPebbleClient.stop_services")
    def _test_upgrade_charm(self, _container_stop_mock, _container_restart_mock):
        self.harness.set_leader()
        self.harness.begin_with_initial_hooks()

        # We'll add the gitlab relation after the first upgrade.
        test_data = self.harness.charm._get_relations_test_data()
        gitlab_rel_name = self.harness.charm._get_legend_gitlab_relation_name()
        gitlab_rel_data = test_data.pop(gitlab_rel_name)

        # Add the rest of the relations.
        for rel_name, rel_data in test_data.items():
            self._add_relation(rel_name, rel_data)
            self.harness.update_config()

        # Setup for the Upgrade Charm event and emit it.
        mock_get_uris = self.patch(self.harness.charm, '_get_legend_gitlab_redirect_uris')
        fake_callback_uris = ['legendary.callback.url']
        mock_get_uris.return_value = fake_callback_uris
        self.harness.charm.on.upgrade_charm.emit()
        mock_get_uris.assert_not_called()

        # Add the gitlab relation.
        gitlab_rel_id = self._add_relation(gitlab_rel_name, gitlab_rel_data)

        # Assert that the unit is currently active.
        self.assertIsInstance(
            self.harness.charm.unit.status, model.ActiveStatus)

        # Assert that the initial Callback URIs have been set.
        relation_data = self.harness.get_relation_data(gitlab_rel_id, self.harness.charm.app)
        expected_rel_data = {'legend-gitlab-redirect-uris': json.dumps(fake_callback_uris)}
        self.assertDictEqual(expected_rel_data, relation_data)

        # Setup for the second Upgrade Event.
        fake_callback_uris = ['foo.lish']
        mock_get_uris.return_value = fake_callback_uris

        # Emit the Upgrade Charm event.
        self.harness.charm.on.upgrade_charm.emit()

        # Assert that the unit is still active.
        self.assertIsInstance(
            self.harness.charm.unit.status, model.ActiveStatus)

        # Check if the Callback URIs have been updated.
        mock_get_uris.assert_called()
        relation_data = self.harness.get_relation_data(gitlab_rel_id, self.harness.charm.app)
        expected_rel_data = {"legend-gitlab-redirect-uris": json.dumps(fake_callback_uris)}
        self.assertDictEqual(expected_rel_data, relation_data)


class BaseFinosLegendCoreServiceTestCharm(
        legend_operator_base.BaseFinosLegendCoreServiceCharm, BaseFinosLegendTestCharm):
    """Testing Charm class for Legend services requiring Gitlab/Mongo relations."""
    @classmethod
    def _get_legend_gitlab_relation_name(cls):
        return "legend_gitlab"

    @classmethod
    def _get_legend_db_relation_name(cls):
        return "legend_db"

    @classmethod
    def _get_required_relations(cls):
        return [
            cls._get_legend_db_relation_name(),
            cls._get_legend_gitlab_relation_name()]

    @classmethod
    def _get_relations_test_data(cls):
        return {
            cls._get_legend_db_relation_name(): {
                "legend-db-connection": json.dumps(
                    {
                        "username": "test_db_user",
                        "password": "test_db_pass",
                        "database": "test_db_name",
                        "uri": "test_db_uri",
                    }
                )
            },
            cls._get_legend_gitlab_relation_name(): {
                "legend-gitlab-connection": json.dumps(
                    {
                        "gitlab_host": "gitlab_test_host",
                        "gitlab_port": 7667,
                        "gitlab_scheme": "https",
                        "client_id": "test_client_id",
                        "client_secret": "test_client_secret",
                        "openid_discovery_url": "test_discovery_url",
                        "gitlab_host_cert_b64": "test_gitlab_cert",
                    }
                )
            },
        }

    def _get_legend_gitlab_redirect_uris(self):
        return ["http://service.legend:443/callback"]

    def _get_core_legend_service_configs(self, legend_db_credentials, legend_gitlab_credentials):
        if any([not param for param in [legend_db_credentials, legend_gitlab_credentials]]):
            return model.WaitingStatus("Missing params")
        return self._get_service_configs_clone({
            self._get_legend_db_relation_name(): legend_db_credentials,
            self._get_legend_gitlab_relation_name(): legend_gitlab_credentials
        })


class TestBaseFinosCoreServiceLegendCharm(BaseFinosLegendCharmTestCase):
    """More specialized implementation of a `BaseFinosLegendCharmTestCase`.

    This class offers all the functioality of `BaseFinosLegendCharmTestCase` while also hooking
    in testing logic for charms with a GitLab and MongoDB relation dependency.

    To use this class, simply override `_set_up_harness` with your setup of choice.
    Note that the class you pass to the harness must be an instance of
    `BaseFinosLegendTestCharm`.
    Note that neither `begin` nor `begin_with_initial_hooks` are called during `setUp`.
    """

    @classmethod
    def _set_up_harness(cls):
        rel_data = {
            rel: {"interface": "%s-interfaces" % rel}
            for rel in BaseFinosLegendCoreServiceTestCharm._get_required_relations()}
        charm_meta = {
            "name": "legend-base-test",
            "requires": {"ingress": {"interface": "ingress"}},
            "provides": rel_data,
            "containers": {
                BaseFinosLegendCoreServiceTestCharm._get_workload_container_name(): {
                    "resource": "image"}},
            "resources": {"image": {"type": "oci-image"}}}
        charm_config = {
            "options": {
                "external-hostname": {
                    "type": "string",
                    "default": "",
                },
            },
        }
        harness = ops_testing.Harness(
            BaseFinosLegendCoreServiceTestCharm,
            meta=yaml.dump(charm_meta),
            config=yaml.dump(charm_config))
        return harness

    def _test_get_core_legend_service_configs(self):
        self.harness.begin_with_initial_hooks()

        relations_test_data = self.harness.charm._get_relations_test_data()
        db_creds = json.loads(
            relations_test_data[
                self.harness.charm._get_legend_db_relation_name()][
                    "legend-db-connection"])
        gitlab_creds = json.loads(
            relations_test_data[
                self.harness.charm._get_legend_gitlab_relation_name()][
                    "legend-gitlab-connection"])

        # Missing DB data:
        self.assertIsInstance(
            self.harness.charm._get_core_legend_service_configs(None, None),
            model.WaitingStatus)

        # Missing GitLab data:
        self.assertIsInstance(
            self.harness.charm._get_core_legend_service_configs(db_creds, None),
            model.WaitingStatus)

        # Missing GitLab data:
        self.assertNotIsInstance(
            self.harness.charm._get_core_legend_service_configs(db_creds, gitlab_creds),
            model.WaitingStatus)

    @mock.patch.object(legend_operator_base, "parse_base64_certificate")
    def _test_get_legend_gitlab_certificate(self, mock_parse_cert):
        self.harness.begin_with_initial_hooks()
        mock_get_creds = self.patch(
            self.harness.charm._legend_gitlab_consumer, 'get_legend_gitlab_creds'
        )
        # Test with no credentials.
        mock_get_creds.return_value = None
        self.assertIsNone(self.harness.charm._get_legend_gitlab_certificate())

        # Test with empty string certificate.
        mock_get_creds.return_value = {"gitlab_host_cert_b64": ""}
        self.assertIsNone(self.harness.charm._get_legend_gitlab_certificate())

        # Test with a certificate.
        mock_get_creds.return_value = {"gitlab_host_cert_b64": "some-cert"}
        cert = self.harness.charm._get_legend_gitlab_certificate()
        mock_parse_cert.assert_called_once_with("some-cert")
        self.assertEqual(cert, mock_parse_cert.return_value)
