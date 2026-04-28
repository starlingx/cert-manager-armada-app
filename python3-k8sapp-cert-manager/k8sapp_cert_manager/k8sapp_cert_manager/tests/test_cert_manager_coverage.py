#
# Copyright (c) 2026 Wind River Systems, Inc.
#
# SPDX-License-Identifier: Apache-2.0
#
"""Unit tests for CertMgrHelm class."""
# pylint: disable=protected-access,unused-argument

import mock
import unittest
import yaml

from k8sapp_cert_manager.common import (
    constants as app_constants
)
from k8sapp_cert_manager.helm import cert_manager

from sysinv.common import constants
from sysinv.common import exception
from sysinv.helm import common

COMPONENT_LABEL = app_constants.HELM_CHART_COMPONENT_LABEL
CHART_CERT_MANAGER = app_constants.HELM_CHART_CERT_MANAGER
CHART_NS = app_constants.HELM_CHART_NS_CERT_MANAGER
HELM_NS = common.HELM_NS_CERT_MANAGER


class TestCertMgrHelmClassAttributes(unittest.TestCase):
    """Tests for CertMgrHelm class-level attributes."""

    def test_chart_constant(self):
        """Verify CHART matches expected constant."""
        self.assertEqual(
            cert_manager.CertMgrHelm.CHART,
            CHART_CERT_MANAGER)

    def test_service_name(self):
        """Verify SERVICE_NAME is set correctly."""
        self.assertEqual(
            cert_manager.CertMgrHelm.SERVICE_NAME,
            'cert-manager')

    def test_label_parameter(self):
        """Verify LABEL_PARAMETER is set correctly."""
        self.assertEqual(
            cert_manager.CertMgrHelm.LABEL_PARAMETER,
            'podLabels')

    def test_component_core_platform(self):
        """Verify COMPONENT_CORE_PLATFORM value."""
        self.assertEqual(
            cert_manager.CertMgrHelm
            .COMPONENT_CORE_PLATFORM,
            'platform')

    def test_component_core_application(self):
        """Verify COMPONENT_CORE_APPLICATION value."""
        self.assertEqual(
            cert_manager.CertMgrHelm
            .COMPONENT_CORE_APPLICATION,
            'application')

    def test_supported_component_labels(self):
        """Verify SUPPORTED_COMPONENT_LABELS structure."""
        labels = (
            cert_manager.CertMgrHelm
            .SUPPORTED_COMPONENT_LABELS)
        self.assertEqual(len(labels), 2)
        self.assertIn(
            {COMPONENT_LABEL: 'platform'}, labels)
        self.assertIn(
            {COMPONENT_LABEL: 'application'}, labels)

    def test_default_label_overrides_keys(self):
        """Verify DEFAULT_LABEL_OVERRIDES has
        correct pod names.
        """
        overrides = (
            cert_manager.CertMgrHelm
            .DEFAULT_LABEL_OVERRIDES)
        self.assertIn('cert-manager', overrides)
        self.assertIn('webhook', overrides)
        self.assertIn('cainjector', overrides)

    def test_default_label_overrides_values(self):
        """Verify DEFAULT_LABEL_OVERRIDES values
        are platform.
        """
        overrides = (
            cert_manager.CertMgrHelm
            .DEFAULT_LABEL_OVERRIDES)
        expected = {COMPONENT_LABEL: 'platform'}
        for pod_name in overrides:
            self.assertEqual(
                overrides[pod_name], expected)

    def test_pod_names_cert_manager(self):
        """Verify PodNames.CERT_MANAGER value."""
        self.assertEqual(
            cert_manager.CertMgrHelm
            .PodNames.CERT_MANAGER,
            'cert-manager')

    def test_pod_names_webhook(self):
        """Verify PodNames.WEBHOOK value."""
        self.assertEqual(
            cert_manager.CertMgrHelm
            .PodNames.WEBHOOK,
            'webhook')

    def test_pod_names_cainjector(self):
        """Verify PodNames.CAINJECTOR value."""
        self.assertEqual(
            cert_manager.CertMgrHelm
            .PodNames.CAINJECTOR,
            'cainjector')

    def test_supported_namespaces_includes_cert_mgr(self):
        """Verify SUPPORTED_NAMESPACES includes
        cert-manager namespace.
        """
        self.assertIn(
            HELM_NS,
            cert_manager.CertMgrHelm
            .SUPPORTED_NAMESPACES)

    def test_supported_app_namespaces(self):
        """Verify SUPPORTED_APP_NAMESPACES structure."""
        app_ns = (
            cert_manager.CertMgrHelm
            .SUPPORTED_APP_NAMESPACES)
        self.assertIn(
            constants.HELM_APP_CERT_MANAGER, app_ns)
        self.assertIn(
            HELM_NS,
            app_ns[constants.HELM_APP_CERT_MANAGER])


class TestCertMgrHelmGetOverrides(unittest.TestCase):
    """Tests for CertMgrHelm.get_overrides method."""

    def setUp(self):
        """Set up test fixtures."""
        self.patcher_base = mock.patch(
            'sysinv.helm.base.BaseHelm.__init__',
            return_value=None)
        self.patcher_base.start()
        self.helm = cert_manager.CertMgrHelm(
            mock.MagicMock())
        self.helm._num_replicas_for_platform_app = (
            mock.MagicMock(return_value=2))
        self.helm._set_core_affinity_override = (
            mock.MagicMock())

    def tearDown(self):
        """Tear down test fixtures."""
        self.patcher_base.stop()

    def test_get_overrides_with_valid_namespace(self):
        """Verify get_overrides returns dict for
        valid namespace.
        """
        result = self.helm.get_overrides(
            namespace=HELM_NS)
        self.assertIsInstance(result, dict)
        self.assertIn('replicaCount', result)

    def test_get_overrides_replica_count(self):
        """Verify get_overrides sets correct
        replicaCount.
        """
        result = self.helm.get_overrides(
            namespace=HELM_NS)
        self.assertEqual(result['replicaCount'], 2)

    def test_get_overrides_webhook_replica_count(self):
        """Verify get_overrides sets webhook
        replicaCount.
        """
        result = self.helm.get_overrides(
            namespace=HELM_NS)
        self.assertEqual(
            result['webhook']['replicaCount'], 2)

    def test_get_overrides_cainjector_replica_count(
            self):
        """Verify get_overrides sets cainjector
        replicaCount.
        """
        result = self.helm.get_overrides(
            namespace=HELM_NS)
        self.assertEqual(
            result['cainjector']['replicaCount'], 2)

    def test_get_overrides_no_namespace_returns_all(
            self):
        """Verify get_overrides with no namespace
        returns full dict.
        """
        result = self.helm.get_overrides(
            namespace=None)
        self.assertIn(HELM_NS, result)

    def test_get_overrides_invalid_namespace_raises(
            self):
        """Verify get_overrides raises for invalid
        namespace.
        """
        self.assertRaises(
            exception.InvalidHelmNamespace,
            self.helm.get_overrides,
            namespace='invalid-ns')

    def test_get_overrides_calls_affinity(self):
        """Verify get_overrides calls
        _set_core_affinity_override.
        """
        self.helm.get_overrides(namespace=HELM_NS)
        affinity_mock = (
            self.helm._set_core_affinity_override)
        affinity_mock.assert_called_once()

    def test_get_namespaces(self):
        """Verify get_namespaces returns
        SUPPORTED_NAMESPACES.
        """
        result = self.helm.get_namespaces()
        self.assertEqual(
            result, self.helm.SUPPORTED_NAMESPACES)


class TestCertMgrHelmGetCurrentPodLabels(
        unittest.TestCase):
    """Tests for _get_current_pod_labels method."""

    def setUp(self):
        """Set up test fixtures."""
        self.patcher_base = mock.patch(
            'sysinv.helm.base.BaseHelm.__init__',
            return_value=None)
        self.patcher_base.start()
        self.helm = cert_manager.CertMgrHelm(
            mock.MagicMock())

    def tearDown(self):
        """Tear down test fixtures."""
        self.patcher_base.stop()

    @mock.patch(
        'k8sapp_cert_manager.helm.cert_manager'
        '.kubernetes.KubeOperator')
    def test_get_current_pod_labels_success(
            self, mock_kube):
        """Verify _get_current_pod_labels with
        valid pods.
        """
        mock_pod = mock.MagicMock()
        mock_pod.metadata.labels.items.return_value = [
            (COMPONENT_LABEL, 'platform')
        ]
        mock_kube_instance = mock_kube.return_value
        mock_kube_instance.kube_get_pods_by_selector \
            .return_value = [mock_pod]

        result = self.helm._get_current_pod_labels()
        self.assertIsInstance(result, dict)

    @mock.patch(
        'k8sapp_cert_manager.helm.cert_manager'
        '.kubernetes.KubeOperator')
    def test_get_current_pod_labels_empty_pods(
            self, mock_kube):
        """Verify _get_current_pod_labels with no
        pods returns defaults.
        """
        mock_kube_instance = mock_kube.return_value
        mock_kube_instance.kube_get_pods_by_selector \
            .return_value = []

        result = self.helm._get_current_pod_labels()
        self.assertEqual(
            result,
            self.helm.DEFAULT_LABEL_OVERRIDES)

    @mock.patch(
        'k8sapp_cert_manager.helm.cert_manager'
        '.kubernetes.KubeOperator')
    def test_get_current_pod_labels_api_exception(
            self, mock_kube):
        """Verify _get_current_pod_labels handles
        ApiException.
        """
        from kubernetes.client.rest import ApiException
        mock_kube.side_effect = ApiException(
            status=404)

        result = self.helm._get_current_pod_labels()
        self.assertEqual(
            result,
            self.helm.DEFAULT_LABEL_OVERRIDES)

    @mock.patch(
        'k8sapp_cert_manager.helm.cert_manager'
        '.kubernetes.KubeOperator')
    def test_get_pod_labels_non_matching_labels(
            self, mock_kube):
        """Verify _get_current_pod_labels with
        non-matching labels.
        """
        mock_pod = mock.MagicMock()
        mock_pod.metadata.labels.items.return_value = [
            ('some-other-label', 'value')
        ]
        mock_kube_instance = mock_kube.return_value
        mock_kube_instance.kube_get_pods_by_selector \
            .return_value = [mock_pod]

        result = self.helm._get_current_pod_labels()
        self.assertEqual(
            result,
            self.helm.DEFAULT_LABEL_OVERRIDES)


class TestCertMgrHelmGetHelmOverrides(
        unittest.TestCase):
    """Tests for _get_helm_overrides method."""

    def setUp(self):
        """Set up test fixtures."""
        self.patcher_base = mock.patch(
            'sysinv.helm.base.BaseHelm.__init__',
            return_value=None)
        self.patcher_base.start()
        self.helm = cert_manager.CertMgrHelm(
            mock.MagicMock())

    def tearDown(self):
        """Tear down test fixtures."""
        self.patcher_base.stop()

    def test_get_helm_overrides_success(self):
        """Verify _get_helm_overrides returns
        parsed overrides.
        """
        mock_dbapi = mock.MagicMock()
        mock_app = mock.MagicMock()
        mock_app.id = 1
        override_data = {
            COMPONENT_LABEL: 'platform'}
        mock_dbapi.helm_override_get.return_value = {
            'user_overrides': yaml.dump(
                override_data)
        }

        result = self.helm._get_helm_overrides(
            mock_dbapi, mock_app,
            CHART_CERT_MANAGER, CHART_NS,
            'user_overrides')
        self.assertEqual(result, override_data)

    def test_get_helm_overrides_dict_type(self):
        """Verify _get_helm_overrides with dict
        value (not str).
        """
        mock_dbapi = mock.MagicMock()
        mock_app = mock.MagicMock()
        mock_app.id = 1
        override_data = {
            COMPONENT_LABEL: 'platform'}
        mock_dbapi.helm_override_get.return_value = {
            'user_overrides': override_data
        }

        result = self.helm._get_helm_overrides(
            mock_dbapi, mock_app,
            CHART_CERT_MANAGER, CHART_NS,
            'user_overrides')
        self.assertEqual(result, override_data)

    def test_get_helm_overrides_not_found(self):
        """Verify _get_helm_overrides when override
        not found.
        """
        mock_dbapi = mock.MagicMock()
        mock_app = mock.MagicMock()
        mock_app.id = 1
        mock_dbapi.helm_override_get.side_effect = (
            exception.HelmOverrideNotFound(
                name='cert-manager',
                namespace='cert-manager'))

        result = self.helm._get_helm_overrides(
            mock_dbapi, mock_app,
            CHART_CERT_MANAGER, CHART_NS,
            'user_overrides')
        self.assertEqual(result, {})


class TestCertMgrHelmSetCoreAffinity(
        unittest.TestCase):
    """Tests for _set_core_affinity_override method."""

    def setUp(self):
        """Set up test fixtures."""
        self.patcher_base = mock.patch(
            'sysinv.helm.base.BaseHelm.__init__',
            return_value=None)
        self.patcher_base.start()
        self.helm = cert_manager.CertMgrHelm(
            mock.MagicMock())

    def tearDown(self):
        """Tear down test fixtures."""
        self.patcher_base.stop()

    @mock.patch.object(
        cert_manager.CertMgrHelm,
        '_get_helm_overrides')
    @mock.patch.object(
        cert_manager.CertMgrHelm,
        '_get_current_pod_labels')
    @mock.patch(
        'k8sapp_cert_manager.helm.cert_manager'
        '.dbapi.get_instance')
    def test_set_core_affinity_valid_new_overrides(
            self, mock_dbapi,
            mock_labels, mock_helm_overrides):
        """Verify _set_core_affinity_override with
        valid new overrides.
        """
        mock_dbapi_instance = mock_dbapi.return_value
        mock_db_app = mock.MagicMock()
        mock_dbapi_instance.kube_app_get.return_value = (
            mock_db_app)

        valid_override = {
            COMPONENT_LABEL: 'application'}
        mock_helm_overrides.return_value = (
            valid_override)
        mock_labels.return_value = (
            self.helm.DEFAULT_LABEL_OVERRIDES)

        overrides = {
            HELM_NS: {
                'webhook': {},
                'cainjector': {},
            }
        }
        self.helm._set_core_affinity_override(
            overrides)
        self.assertIn(
            'podLabels', overrides[HELM_NS])

    @mock.patch.object(
        cert_manager.CertMgrHelm,
        '_get_helm_overrides')
    @mock.patch.object(
        cert_manager.CertMgrHelm,
        '_get_current_pod_labels')
    @mock.patch(
        'k8sapp_cert_manager.helm.cert_manager'
        '.dbapi.get_instance')
    def test_set_core_affinity_no_new_overrides(
            self, mock_dbapi,
            mock_labels, mock_helm_overrides):
        """Verify _set_core_affinity_override falls
        back to current labels.
        """
        mock_dbapi_instance = mock_dbapi.return_value
        mock_db_app = mock.MagicMock()
        mock_dbapi_instance.kube_app_get.return_value = (
            mock_db_app)

        mock_helm_overrides.return_value = {}
        mock_labels.return_value = (
            self.helm.DEFAULT_LABEL_OVERRIDES)

        overrides = {
            HELM_NS: {
                'webhook': {},
                'cainjector': {},
            }
        }
        self.helm._set_core_affinity_override(
            overrides)
        expected = {COMPONENT_LABEL: 'platform'}
        self.assertEqual(
            overrides[HELM_NS]['webhook']['podLabels'],
            expected)

    @mock.patch.object(
        cert_manager.CertMgrHelm,
        '_get_helm_overrides')
    @mock.patch.object(
        cert_manager.CertMgrHelm,
        '_get_current_pod_labels')
    @mock.patch(
        'k8sapp_cert_manager.helm.cert_manager'
        '.dbapi.get_instance')
    def test_set_core_affinity_unsupported_label(
            self, mock_dbapi,
            mock_labels, mock_helm_overrides):
        """Verify _set_core_affinity_override with
        unsupported label value.
        """
        mock_dbapi_instance = mock_dbapi.return_value
        mock_db_app = mock.MagicMock()
        mock_dbapi_instance.kube_app_get.return_value = (
            mock_db_app)

        mock_helm_overrides.return_value = {
            'unsupported': 'value'}
        mock_labels.return_value = (
            self.helm.DEFAULT_LABEL_OVERRIDES)

        overrides = {
            HELM_NS: {
                'webhook': {},
                'cainjector': {},
            }
        }
        self.helm._set_core_affinity_override(
            overrides)
        expected = {COMPONENT_LABEL: 'platform'}
        self.assertEqual(
            overrides[HELM_NS]['webhook']['podLabels'],
            expected)
