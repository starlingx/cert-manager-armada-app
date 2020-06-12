#
# Copyright (c) 2020 Wind River Systems, Inc.
#
# SPDX-License-Identifier: Apache-2.0
#

from sysinv.common import constants
from sysinv.tests.db import base as dbbase
from sysinv.tests.helm.test_helm import HelmOperatorTestSuiteMixin


class K8SAppCertMgrAppMixin(object):
    app_name = constants.HELM_APP_CERT_MANAGER
    path_name = app_name + '.tgz'

    def setUp(self):
        super(K8SAppCertMgrAppMixin, self).setUp()


# Test Configuration:
# - Controller
# - IPv6
# - Ceph Storage
# - cert-manager app
class K8sAppCertMgrControllerTestCase(K8SAppCertMgrAppMixin,
                                      dbbase.BaseIPv6Mixin,
                                      dbbase.BaseCephStorageBackendMixin,
                                      HelmOperatorTestSuiteMixin,
                                      dbbase.ControllerHostTestCase):
    pass


# Test Configuration:
# - AIO
# - IPv4
# - Ceph Storage
# - cert-manager app
class K8SAppCertMgrAIOTestCase(K8SAppCertMgrAppMixin,
                               dbbase.BaseCephStorageBackendMixin,
                               HelmOperatorTestSuiteMixin,
                               dbbase.AIOSimplexHostTestCase):
    pass
