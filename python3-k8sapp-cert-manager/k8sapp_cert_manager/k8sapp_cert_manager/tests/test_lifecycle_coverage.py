#
# Copyright (c) 2026 Wind River Systems, Inc.
#
# SPDX-License-Identifier: Apache-2.0
#
"""Unit tests for CertManagerAppLifecycleOperator."""
# pylint: disable=protected-access,unused-argument

import mock
import unittest

from k8sapp_cert_manager.lifecycle import (
    lifecycle_cert_manager as lcm
)

from sysinv.common import constants
from sysinv.common import exception
from sysinv.helm.lifecycle_constants import LifecycleConstants


class TestLifecycleModuleConstants(unittest.TestCase):
    """Tests for module-level constants."""

    def test_namespace(self):
        """Verify NAMESPACE constant."""
        self.assertEqual(lcm.NAMESPACE, 'cert-manager')

    def test_cert_manager_group(self):
        """Verify CERT_MANAGER_GROUP constant."""
        self.assertEqual(
            lcm.CERT_MANAGER_GROUP, 'cert-manager.io')

    def test_cert_manager_version(self):
        """Verify CERT_MANAGER_VERSION constant."""
        self.assertEqual(lcm.CERT_MANAGER_VERSION, 'v1')

    def test_cert_name(self):
        """Verify CERT_NAME constant."""
        self.assertEqual(lcm.CERT_NAME, 'stx-test-cm')

    def test_cert_secret_name(self):
        """Verify CERT_SECRET_NAME constant."""
        self.assertEqual(
            lcm.CERT_SECRET_NAME, 'stx-test-cm')

    def test_issuer_name(self):
        """Verify ISSUER_NAME constant."""
        self.assertEqual(
            lcm.ISSUER_NAME, 'system-local-ca')

    def test_issuer_plural(self):
        """Verify ISSUER_PLURAL constant."""
        self.assertEqual(lcm.ISSUER_PLURAL, 'issuers')

    def test_plural_name_cert(self):
        """Verify PLURAL_NAME_CERT constant."""
        self.assertEqual(
            lcm.PLURAL_NAME_CERT, 'certificates')

    def test_test_cert_retries(self):
        """Verify TEST_CERT_RETRIES constant."""
        self.assertEqual(lcm.TEST_CERT_RETRIES, 60)

    def test_issuer_structure(self):
        """Verify ISSUER dict structure."""
        self.assertEqual(
            lcm.ISSUER['kind'], 'Issuer')
        self.assertEqual(
            lcm.ISSUER['metadata']['name'],
            'system-local-ca')
        self.assertEqual(
            lcm.ISSUER['metadata']['namespace'],
            'cert-manager')

    def test_cert_structure(self):
        """Verify CERT dict structure."""
        self.assertEqual(
            lcm.CERT['kind'], 'Certificate')
        self.assertEqual(
            lcm.CERT['metadata']['name'],
            'stx-test-cm')
        self.assertEqual(
            lcm.CERT['spec']['secretName'],
            'stx-test-cm')
        self.assertEqual(
            lcm.CERT['spec']['issuerRef']['name'],
            'system-local-ca')


class TestPreAutoApplyCheck(unittest.TestCase):
    """Tests for pre_auto_apply_check method."""

    def setUp(self):
        """Set up test fixtures."""
        self.operator = (
            lcm.CertManagerAppLifecycleOperator())

    @mock.patch('os.path.isfile', return_value=True)
    def test_pre_auto_apply_check_bootstrap(
            self, mock_isfile):
        """Verify pre_auto_apply_check raises
        during bootstrap.
        """
        self.assertRaises(
            exception.LifecycleSemanticCheckException,
            self.operator.pre_auto_apply_check)

    @mock.patch('os.path.isfile', return_value=False)
    def test_pre_auto_apply_check_no_bootstrap(
            self, mock_isfile):
        """Verify pre_auto_apply_check passes
        when not bootstrapping.
        """
        result = self.operator.pre_auto_apply_check()
        self.assertIsNone(result)


class TestAppLifecycleActions(unittest.TestCase):
    """Tests for app_lifecycle_actions method."""

    def setUp(self):
        """Set up test fixtures."""
        self.operator = (
            lcm.CertManagerAppLifecycleOperator())
        self.context = mock.MagicMock()
        self.conductor = mock.MagicMock()
        self.app_op = mock.MagicMock()
        self.app = mock.MagicMock()
        self.hook_info = mock.MagicMock()

    @mock.patch.object(
        lcm.CertManagerAppLifecycleOperator,
        'pre_auto_apply_check')
    def test_semantic_check_pre_auto_apply(
            self, mock_check):
        """Verify semantic check for pre auto apply."""
        self.hook_info.lifecycle_type = (
            LifecycleConstants
            .APP_LIFECYCLE_TYPE_SEMANTIC_CHECK)
        self.hook_info.mode = (
            LifecycleConstants.APP_LIFECYCLE_MODE_AUTO)
        self.hook_info.operation = (
            constants.APP_APPLY_OP)
        self.hook_info.relative_timing = (
            LifecycleConstants.APP_LIFECYCLE_TIMING_PRE)

        self.operator.app_lifecycle_actions(
            self.context, self.conductor,
            self.app_op, self.app, self.hook_info)
        mock_check.assert_called_once()

    @mock.patch(
        'k8sapp_cert_manager.lifecycle'
        '.lifecycle_cert_manager'
        '.lifecycle_utils'
        '.add_pod_security_admission'
        '_controller_labels')
    @mock.patch(
        'k8sapp_cert_manager.lifecycle'
        '.lifecycle_cert_manager'
        '.lifecycle_utils'
        '.create_local_registry_secrets')
    def test_resource_pre_apply(
            self, mock_create, mock_add):
        """Verify resource lifecycle for pre-apply."""
        self.hook_info.lifecycle_type = (
            LifecycleConstants
            .APP_LIFECYCLE_TYPE_RESOURCE)
        self.hook_info.operation = (
            constants.APP_APPLY_OP)
        self.hook_info.relative_timing = (
            LifecycleConstants.APP_LIFECYCLE_TIMING_PRE)

        self.operator.app_lifecycle_actions(
            self.context, self.conductor,
            self.app_op, self.app, self.hook_info)
        mock_create.assert_called_once()
        mock_add.assert_called_once()

    @mock.patch(
        'k8sapp_cert_manager.lifecycle'
        '.lifecycle_cert_manager'
        '.lifecycle_utils'
        '.delete_local_registry_secrets')
    def test_resource_post_remove(
            self, mock_delete):
        """Verify resource lifecycle for post-remove."""
        self.hook_info.lifecycle_type = (
            LifecycleConstants
            .APP_LIFECYCLE_TYPE_RESOURCE)
        self.hook_info.operation = (
            constants.APP_REMOVE_OP)
        self.hook_info.relative_timing = (
            LifecycleConstants
            .APP_LIFECYCLE_TIMING_POST)

        self.operator.app_lifecycle_actions(
            self.context, self.conductor,
            self.app_op, self.app, self.hook_info)
        mock_delete.assert_called_once()

    @mock.patch.object(
        lcm.CertManagerAppLifecycleOperator,
        'issue_test_cert')
    @mock.patch(
        'os.path.isfile', return_value=False)
    def test_fluxcd_request_apply_status(
            self, mock_isfile, mock_issue):
        """Verify fluxcd request for apply status."""
        self.hook_info.lifecycle_type = (
            LifecycleConstants
            .APP_LIFECYCLE_TYPE_FLUXCD_REQUEST)
        self.hook_info.operation = (
            constants.APP_APPLY_OP)
        self.hook_info.relative_timing = (
            LifecycleConstants
            .APP_LIFECYCLE_TIMING_STATUS)

        self.operator.app_lifecycle_actions(
            self.context, self.conductor,
            self.app_op, self.app, self.hook_info)
        mock_issue.assert_called_once()

    @mock.patch.object(
        lcm.CertManagerAppLifecycleOperator,
        'issue_test_cert')
    @mock.patch(
        'os.path.isfile', return_value=True)
    def test_fluxcd_request_apply_status_bootstrap(
            self, mock_isfile, mock_issue):
        """Verify fluxcd request skipped at bootstrap."""
        self.hook_info.lifecycle_type = (
            LifecycleConstants
            .APP_LIFECYCLE_TYPE_FLUXCD_REQUEST)
        self.hook_info.operation = (
            constants.APP_APPLY_OP)
        self.hook_info.relative_timing = (
            LifecycleConstants
            .APP_LIFECYCLE_TIMING_STATUS)

        base_class = (
            lcm.CertManagerAppLifecycleOperator
            .__bases__[0])
        with mock.patch.object(
                base_class,
                'app_lifecycle_actions'):
            self.operator.app_lifecycle_actions(
                self.context, self.conductor,
                self.app_op, self.app,
                self.hook_info)
        mock_issue.assert_not_called()

    def test_default_hook_calls_super(self):
        """Verify unhandled hook type calls super."""
        self.hook_info.lifecycle_type = 'unknown_type'

        base_class = (
            lcm.CertManagerAppLifecycleOperator
            .__bases__[0])
        with mock.patch.object(
                base_class,
                'app_lifecycle_actions') as mock_super:
            self.operator.app_lifecycle_actions(
                self.context, self.conductor,
                self.app_op, self.app,
                self.hook_info)
            mock_super.assert_called_once()


class TestIssueTestCert(unittest.TestCase):
    """Tests for issue_test_cert method."""

    def setUp(self):
        """Set up test fixtures."""
        self.operator = (
            lcm.CertManagerAppLifecycleOperator())
        self.time_patcher = mock.patch(
            'k8sapp_cert_manager.lifecycle'
            '.lifecycle_cert_manager.time.sleep')
        self.mock_sleep = self.time_patcher.start()

    def tearDown(self):
        """Tear down test fixtures."""
        self.time_patcher.stop()

    @mock.patch(
        'k8sapp_cert_manager.lifecycle'
        '.lifecycle_cert_manager'
        '.kubernetes.KubeOperator')
    def test_issue_test_cert_success(
            self, mock_kube_class):
        """Verify issue_test_cert succeeds on first try."""
        mock_kube = mock_kube_class.return_value
        mock_kube.delete_custom_resource.return_value = (
            None)
        mock_kube.apply_custom_resource.return_value = (
            None)
        mock_kube.kube_get_secret.return_value = (
            mock.MagicMock())

        result = self.operator.issue_test_cert()
        self.assertIsNone(result)

    @mock.patch(
        'k8sapp_cert_manager.lifecycle'
        '.lifecycle_cert_manager'
        '.kubernetes.KubeOperator')
    def test_issue_test_cert_initial_delete_fails(
            self, mock_kube_class):
        """Verify issue_test_cert handles initial
        delete failure.
        """
        mock_kube = mock_kube_class.return_value
        mock_kube.delete_custom_resource.side_effect = [
            Exception("not found"),
            None,
        ]
        mock_kube.apply_custom_resource.return_value = (
            None)
        mock_kube.kube_get_secret.return_value = (
            mock.MagicMock())

        result = self.operator.issue_test_cert()
        self.assertIsNone(result)

    @mock.patch(
        'k8sapp_cert_manager.lifecycle'
        '.lifecycle_cert_manager'
        '.kubernetes.KubeOperator')
    def test_issue_cert_apply_issuer_fails_then_ok(
            self, mock_kube_class):
        """Verify issue_test_cert retries when
        issuer apply fails.
        """
        mock_kube = mock_kube_class.return_value
        mock_kube.delete_custom_resource.return_value = (
            None)
        mock_kube.apply_custom_resource.side_effect = [
            Exception("issuer fail"),
            None,
            None,
        ]
        mock_kube.kube_get_secret.return_value = (
            mock.MagicMock())

        result = self.operator.issue_test_cert()
        self.assertIsNone(result)

    @mock.patch(
        'k8sapp_cert_manager.lifecycle'
        '.lifecycle_cert_manager'
        '.kubernetes.KubeOperator')
    def test_issue_cert_apply_cert_fails_then_ok(
            self, mock_kube_class):
        """Verify issue_test_cert retries when
        cert apply fails.
        """
        mock_kube = mock_kube_class.return_value
        mock_kube.delete_custom_resource.return_value = (
            None)
        mock_kube.apply_custom_resource.side_effect = [
            None,
            Exception("cert fail"),
            None,
            None,
        ]
        mock_kube.kube_get_secret.return_value = (
            mock.MagicMock())

        result = self.operator.issue_test_cert()
        self.assertIsNone(result)

    @mock.patch(
        'k8sapp_cert_manager.lifecycle'
        '.lifecycle_cert_manager'
        '.kubernetes.KubeOperator')
    def test_issue_cert_secret_not_ready_then_ready(
            self, mock_kube_class):
        """Verify issue_test_cert retries when
        secret is not ready.
        """
        mock_kube = mock_kube_class.return_value
        mock_kube.delete_custom_resource.return_value = (
            None)
        mock_kube.apply_custom_resource.return_value = (
            None)
        mock_kube.kube_get_secret.side_effect = [
            None,
            mock.MagicMock(),
        ]

        result = self.operator.issue_test_cert()
        self.assertIsNone(result)

    @mock.patch(
        'k8sapp_cert_manager.lifecycle'
        '.lifecycle_cert_manager'
        '.kubernetes.KubeOperator')
    def test_issue_cert_secret_exception_then_ready(
            self, mock_kube_class):
        """Verify issue_test_cert handles secret
        retrieval exception.
        """
        mock_kube = mock_kube_class.return_value
        mock_kube.delete_custom_resource.return_value = (
            None)
        mock_kube.apply_custom_resource.return_value = (
            None)
        mock_kube.kube_get_secret.side_effect = [
            Exception("secret error"),
            mock.MagicMock(),
        ]

        result = self.operator.issue_test_cert()
        self.assertIsNone(result)

    @mock.patch(
        'k8sapp_cert_manager.lifecycle'
        '.lifecycle_cert_manager'
        '.TEST_CERT_RETRIES', 2)
    @mock.patch(
        'k8sapp_cert_manager.lifecycle'
        '.lifecycle_cert_manager'
        '.kubernetes.KubeOperator')
    def test_issue_test_cert_timeout_raises(
            self, mock_kube_class):
        """Verify issue_test_cert raises after
        all retries exhausted.
        """
        mock_kube = mock_kube_class.return_value
        mock_kube.delete_custom_resource.return_value = (
            None)
        mock_kube.apply_custom_resource.return_value = (
            None)
        mock_kube.kube_get_secret.return_value = None

        self.assertRaises(
            exception.SysinvException,
            self.operator.issue_test_cert)

    @mock.patch(
        'k8sapp_cert_manager.lifecycle'
        '.lifecycle_cert_manager'
        '.TEST_CERT_RETRIES', 2)
    @mock.patch(
        'k8sapp_cert_manager.lifecycle'
        '.lifecycle_cert_manager'
        '.kubernetes.KubeOperator')
    def test_issue_test_cert_cleanup_fails(
            self, mock_kube_class):
        """Verify issue_test_cert handles cleanup
        failure gracefully.
        """
        mock_kube = mock_kube_class.return_value
        mock_kube.delete_custom_resource.side_effect = [
            None,
            Exception("cleanup fail"),
        ]
        mock_kube.apply_custom_resource.return_value = (
            None)
        mock_kube.kube_get_secret.return_value = None

        self.assertRaises(
            exception.SysinvException,
            self.operator.issue_test_cert)

    @mock.patch(
        'k8sapp_cert_manager.lifecycle'
        '.lifecycle_cert_manager'
        '.TEST_CERT_RETRIES', 2)
    @mock.patch(
        'k8sapp_cert_manager.lifecycle'
        '.lifecycle_cert_manager'
        '.kubernetes.KubeOperator')
    def test_issue_test_cert_all_applies_fail(
            self, mock_kube_class):
        """Verify issue_test_cert raises when all
        apply attempts fail.
        """
        mock_kube = mock_kube_class.return_value
        mock_kube.delete_custom_resource.return_value = (
            None)
        mock_kube.apply_custom_resource.side_effect = (
            Exception("apply fail"))
        mock_kube.kube_get_secret.return_value = None

        self.assertRaises(
            exception.SysinvException,
            self.operator.issue_test_cert)


class TestAppLifecycleActionsSemanticNonAuto(
        unittest.TestCase):
    """Tests for non-auto semantic check paths."""

    def setUp(self):
        """Set up test fixtures."""
        self.operator = (
            lcm.CertManagerAppLifecycleOperator())
        self.context = mock.MagicMock()
        self.conductor = mock.MagicMock()
        self.app_op = mock.MagicMock()
        self.app = mock.MagicMock()
        self.hook_info = mock.MagicMock()

    def test_semantic_check_non_auto_mode(self):
        """Verify semantic check with non-auto mode
        falls through to super.
        """
        self.hook_info.lifecycle_type = (
            LifecycleConstants
            .APP_LIFECYCLE_TYPE_SEMANTIC_CHECK)
        self.hook_info.mode = 'manual'
        self.hook_info.operation = (
            constants.APP_APPLY_OP)
        self.hook_info.relative_timing = (
            LifecycleConstants.APP_LIFECYCLE_TIMING_PRE)

        base_class = (
            lcm.CertManagerAppLifecycleOperator
            .__bases__[0])
        with mock.patch.object(
                base_class,
                'app_lifecycle_actions') as mock_super:
            self.operator.app_lifecycle_actions(
                self.context, self.conductor,
                self.app_op, self.app,
                self.hook_info)
            mock_super.assert_called_once()

    def test_resource_non_matching_operation(self):
        """Verify resource lifecycle with
        non-matching operation.
        """
        self.hook_info.lifecycle_type = (
            LifecycleConstants
            .APP_LIFECYCLE_TYPE_RESOURCE)
        self.hook_info.operation = 'unknown_op'
        self.hook_info.relative_timing = (
            LifecycleConstants.APP_LIFECYCLE_TIMING_PRE)

        base_class = (
            lcm.CertManagerAppLifecycleOperator
            .__bases__[0])
        with mock.patch.object(
                base_class,
                'app_lifecycle_actions') as mock_super:
            self.operator.app_lifecycle_actions(
                self.context, self.conductor,
                self.app_op, self.app,
                self.hook_info)
            mock_super.assert_called_once()
