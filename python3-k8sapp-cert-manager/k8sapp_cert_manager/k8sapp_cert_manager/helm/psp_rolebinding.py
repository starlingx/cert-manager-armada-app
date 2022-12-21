#
# Copyright (c) 2020 Wind River Systems, Inc.
#
# SPDX-License-Identifier: Apache-2.0
#

from k8sapp_cert_manager.common import constants as app_constants

from sysinv.common import constants
from sysinv.common import exception

from sysinv.helm import base
from sysinv.helm import common


class PSPRolebindingHelm(base.BaseHelm):
    """Class to encapsulate helm operations for the psp rolebinding chart"""

    SUPPORTED_NAMESPACES = base.BaseHelm.SUPPORTED_NAMESPACES + \
        [common.HELM_NS_CERT_MANAGER]
    SUPPORTED_APP_NAMESPACES = {
        constants.HELM_APP_CERT_MANAGER:
            base.BaseHelm.SUPPORTED_NAMESPACES + [common.HELM_NS_CERT_MANAGER],
    }

    CHART = app_constants.HELM_CHART_PSP_ROLEBINDING
    SERVICE_NAME = 'psp-rolebinding'

    def get_namespaces(self):
        return self.SUPPORTED_NAMESPACES

    def get_overrides(self, namespace=None):
        overrides = {
            common.HELM_NS_CERT_MANAGER: {}
        }

        if namespace in self.SUPPORTED_NAMESPACES:
            return overrides[namespace]
        elif namespace:
            raise exception.InvalidHelmNamespace(chart=self.CHART,
                                                 namespace=namespace)
        else:
            return overrides
