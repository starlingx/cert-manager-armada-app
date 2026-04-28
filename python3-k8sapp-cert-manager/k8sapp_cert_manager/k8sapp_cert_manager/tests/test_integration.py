#
# Copyright (c) 2026 Wind River Systems, Inc.
#
# SPDX-License-Identifier: Apache-2.0
#
"""Integration tests for cert-manager-armada-app."""
# pylint: disable=protected-access,unused-argument

import os
import unittest

from k8sapp_cert_manager.common import (
    constants as app_constants
)
from k8sapp_cert_manager.helm import cert_manager
from k8sapp_cert_manager.lifecycle import (
    lifecycle_cert_manager as lcm
)


class TestConstantsIntegration(unittest.TestCase):
    """Tests verifying constants consistency."""

    def test_helm_app_name_matches_namespace(self):
        """Verify HELM_APP_CERT_MANAGER matches
        lifecycle NAMESPACE.
        """
        self.assertEqual(
            app_constants.HELM_APP_CERT_MANAGER,
            lcm.NAMESPACE)

    def test_helm_chart_name_matches_app_name(self):
        """Verify HELM_CHART_CERT_MANAGER matches
        HELM_APP_CERT_MANAGER.
        """
        self.assertEqual(
            app_constants.HELM_CHART_CERT_MANAGER,
            app_constants.HELM_APP_CERT_MANAGER)

    def test_helm_chart_ns_matches_app_name(self):
        """Verify HELM_CHART_NS_CERT_MANAGER
        matches HELM_APP.
        """
        self.assertEqual(
            app_constants.HELM_CHART_NS_CERT_MANAGER,
            app_constants.HELM_APP_CERT_MANAGER)

    def test_component_label_constant(self):
        """Verify HELM_CHART_COMPONENT_LABEL."""
        self.assertEqual(
            app_constants.HELM_CHART_COMPONENT_LABEL,
            'app.starlingx.io/component')

    def test_issuer_api_version_format(self):
        """Verify ISSUER apiVersion matches
        group/version.
        """
        expected = '%s/%s' % (
            lcm.CERT_MANAGER_GROUP,
            lcm.CERT_MANAGER_VERSION)
        self.assertEqual(
            lcm.ISSUER['apiVersion'], expected)

    def test_cert_api_version(self):
        """Verify CERT apiVersion."""
        self.assertEqual(
            lcm.CERT['apiVersion'],
            'cert-manager.io/v1')

    def test_cert_issuer_ref_matches_issuer_name(
            self):
        """Verify CERT issuerRef.name matches
        ISSUER_NAME.
        """
        self.assertEqual(
            lcm.CERT['spec']['issuerRef']['name'],
            lcm.ISSUER_NAME)

    def test_cert_namespace_matches_module(self):
        """Verify CERT namespace matches NAMESPACE."""
        self.assertEqual(
            lcm.CERT['metadata']['namespace'],
            lcm.NAMESPACE)

    def test_issuer_namespace_matches_module(self):
        """Verify ISSUER namespace matches
        NAMESPACE.
        """
        self.assertEqual(
            lcm.ISSUER['metadata']['namespace'],
            lcm.NAMESPACE)


class TestModuleImports(unittest.TestCase):
    """Tests verifying all modules can be imported."""

    def test_import_constants(self):
        """Verify constants module imports."""
        from k8sapp_cert_manager.common import (
            constants)
        self.assertIsNotNone(constants)

    def test_import_cert_manager_helm(self):
        """Verify cert_manager helm module imports."""
        from k8sapp_cert_manager.helm import (
            cert_manager)
        self.assertIsNotNone(cert_manager)

    def test_import_lifecycle(self):
        """Verify lifecycle module imports."""
        from k8sapp_cert_manager.lifecycle import (
            lifecycle_cert_manager)
        self.assertIsNotNone(lifecycle_cert_manager)

    def test_import_init_packages(self):
        """Verify __init__ packages import."""
        import k8sapp_cert_manager
        import k8sapp_cert_manager.common
        import k8sapp_cert_manager.helm
        import k8sapp_cert_manager.lifecycle
        self.assertIsNotNone(k8sapp_cert_manager)

    def test_certmgrhelm_class_exists(self):
        """Verify CertMgrHelm class is accessible."""
        self.assertTrue(
            hasattr(cert_manager, 'CertMgrHelm'))

    def test_lifecycle_operator_class_exists(self):
        """Verify lifecycle operator class exists."""
        self.assertTrue(
            hasattr(
                lcm,
                'CertManagerAppLifecycleOperator'))


class TestProjectStructure(unittest.TestCase):
    """Tests validating project file structure."""

    def setUp(self):
        """Set up project root path."""
        self.test_dir = os.path.dirname(
            os.path.abspath(__file__))
        self.package_dir = os.path.dirname(
            self.test_dir)

    def test_helm_directory_exists(self):
        """Verify helm directory exists."""
        helm_dir = os.path.join(
            self.package_dir, 'helm')
        self.assertTrue(os.path.isdir(helm_dir))

    def test_lifecycle_directory_exists(self):
        """Verify lifecycle directory exists."""
        lifecycle_dir = os.path.join(
            self.package_dir, 'lifecycle')
        self.assertTrue(
            os.path.isdir(lifecycle_dir))

    def test_common_directory_exists(self):
        """Verify common directory exists."""
        common_dir = os.path.join(
            self.package_dir, 'common')
        self.assertTrue(os.path.isdir(common_dir))

    def test_tests_directory_exists(self):
        """Verify tests directory exists."""
        self.assertTrue(
            os.path.isdir(self.test_dir))

    def test_init_files_exist(self):
        """Verify __init__.py files exist in all
        packages.
        """
        subdirs = [
            'helm', 'lifecycle', 'common', 'tests']
        for subdir in subdirs:
            init_file = os.path.join(
                self.package_dir, subdir,
                '__init__.py')
            self.assertTrue(
                os.path.isfile(init_file),
                "Missing __init__.py in %s" % subdir)
