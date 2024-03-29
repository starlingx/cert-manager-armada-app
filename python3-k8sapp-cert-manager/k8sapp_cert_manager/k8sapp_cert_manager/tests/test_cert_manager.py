# Copyright (c) 2023 Wind River Systems, Inc.
#
# SPDX-License-Identifier: Apache-2.0
#
import mock

from k8sapp_cert_manager.common import constants as app_constants
from k8sapp_cert_manager.tests import test_plugins
from k8sapp_cert_manager.helm import cert_manager

from sysinv.db import api as dbapi
from sysinv.helm import common

from sysinv.tests.db import base as dbbase
from sysinv.tests.db import utils as dbutils
from sysinv.tests.helm import base


class CertManagerTestCase(test_plugins.K8SAppCertMgrAppMixin,
                          base.HelmTestCaseMixin):

    def setUp(self):
        super(CertManagerTestCase, self).setUp()
        self.app = dbutils.create_test_app(name='cert-manager')
        self.dbapi = dbapi.get_instance()

        # Mock get_disk_capacity utility
        self.mock_get_current_pod_labels = mock.MagicMock()
        p = mock.patch('k8sapp_cert_manager.helm.cert_manager.CertMgrHelm._get_current_pod_labels',
                       self.mock_get_current_pod_labels)
        p.start().return_value = cert_manager.CertMgrHelm.DEFAULT_LABEL_OVERRIDES
        self.addCleanup(p.stop)


class CertManagerIPv4ControllerHostTestCase(CertManagerTestCase,
                                            dbbase.ProvisionedControllerHostTestCase):

    def test_replicas(self):
        overrides = self.operator.get_helm_chart_overrides(
            app_constants.HELM_CHART_CERT_MANAGER,
            cnamespace=common.HELM_NS_CERT_MANAGER)

        self.assertOverridesParameters(overrides, {
            # 1 replica for 1 controller
            'replicaCount': 1
        })


class CertManagerIPv6AIODuplexSystemTestCase(CertManagerTestCase,
                                             dbbase.BaseIPv6Mixin,
                                             dbbase.ProvisionedAIODuplexSystemTestCase):

    def test_replicas(self):
        overrides = self.operator.get_helm_chart_overrides(
            app_constants.HELM_CHART_CERT_MANAGER,
            cnamespace=common.HELM_NS_CERT_MANAGER)

        self.assertOverridesParameters(overrides, {
            # 2 replicas for 2 controllers
            'replicaCount': 2
        })
