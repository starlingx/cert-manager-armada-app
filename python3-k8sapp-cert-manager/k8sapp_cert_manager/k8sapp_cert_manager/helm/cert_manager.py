#
# Copyright (c) 2020-2023 Wind River Systems, Inc.
#
# SPDX-License-Identifier: Apache-2.0
#

from k8sapp_cert_manager.common import constants as app_constants

from oslo_log import log as logging

from sysinv.common import constants
from sysinv.common import exception
from sysinv.common import kubernetes

from sysinv.helm import base
from sysinv.helm import common

from sysinv.db import api as dbapi

import yaml

LOG = logging.getLogger(__name__)


class CertMgrHelm(base.BaseHelm):
    """Class to encapsulate helm operations for the cert-manager chart"""
    class PodNames(object):
        CERT_MANAGER = 'cert-manager'
        WEBHOOK = 'webhook'
        CAINJECTOR = 'cainjector'

    SUPPORTED_NAMESPACES = base.BaseHelm.SUPPORTED_NAMESPACES + \
        [common.HELM_NS_CERT_MANAGER]

    SUPPORTED_APP_NAMESPACES = {
        constants.HELM_APP_CERT_MANAGER:
            base.BaseHelm.SUPPORTED_NAMESPACES + [common.HELM_NS_CERT_MANAGER],
    }

    COMPONENT_CORE_PLATFORM = 'platform'

    COMPONENT_CORE_APPLICATION = 'application'

    SUPPORTED_COMPONENT_LABELS = [
        {app_constants.HELM_CHART_COMPONENT_LABEL: COMPONENT_CORE_PLATFORM},
        {app_constants.HELM_CHART_COMPONENT_LABEL: COMPONENT_CORE_APPLICATION},
    ]

    DEFAULT_LABEL_OVERRIDES = {
        PodNames.CERT_MANAGER: {
            app_constants.HELM_CHART_COMPONENT_LABEL: COMPONENT_CORE_PLATFORM,
        },
        PodNames.WEBHOOK: {
            app_constants.HELM_CHART_COMPONENT_LABEL: COMPONENT_CORE_PLATFORM,
        },
        PodNames.CAINJECTOR: {
            app_constants.HELM_CHART_COMPONENT_LABEL: COMPONENT_CORE_PLATFORM,
        },
    }

    CHART = app_constants.HELM_CHART_CERT_MANAGER

    LABEL_PARAMETER = 'podLabels'

    SERVICE_NAME = 'cert-manager'

    def get_namespaces(self):
        return self.SUPPORTED_NAMESPACES

    def get_overrides(self, namespace=None):
        overrides = {
            common.HELM_NS_CERT_MANAGER: {
                'replicaCount': self._num_replicas_for_platform_app(),
                self.PodNames.WEBHOOK: {
                    'replicaCount': self._num_replicas_for_platform_app(),
                },
                self.PodNames.CAINJECTOR: {
                    'replicaCount': self._num_replicas_for_platform_app(),
                },
            }
        }

        self._set_core_affinity_override(overrides)

        if namespace in self.SUPPORTED_NAMESPACES:
            return overrides[namespace]
        elif namespace:
            raise exception.InvalidHelmNamespace(chart=self.CHART,
                                                 namespace=namespace)
        else:
            return overrides

    def _set_core_affinity_override(self, overrides):
        """ Set user overrides for core affinity

        Analyzes and returns proper overrides for cert-manager pods.
        Supported overrides are app.starlingx.io/component: [platform,application]

        """

        dbapi_instance = dbapi.get_instance()

        db_app = dbapi_instance.kube_app_get(app_constants.HELM_APP_CERT_MANAGER)

        # Current chart overrides
        current_chart_overrides = self._get_current_pod_labels()

        # User chart overrides
        new_chart_overrides = self._get_helm_overrides(
            dbapi_instance,
            db_app,
            app_constants.HELM_CHART_CERT_MANAGER,
            app_constants.HELM_CHART_NS_CERT_MANAGER,
            'user_overrides')

        labels = self.SUPPORTED_COMPONENT_LABELS

        for item in self.DEFAULT_LABEL_OVERRIDES:
            if item == self.PodNames.WEBHOOK or item == self.PodNames.CAINJECTOR:
                overrides[common.HELM_NS_CERT_MANAGER][item][self.LABEL_PARAMETER] = (
                    new_chart_overrides
                    if new_chart_overrides and new_chart_overrides in labels
                    else current_chart_overrides[item])
            else:
                overrides[common.HELM_NS_CERT_MANAGER][self.LABEL_PARAMETER] = (
                    new_chart_overrides
                    if new_chart_overrides and new_chart_overrides in labels
                    else current_chart_overrides[item])

    def _get_current_pod_labels(self):
        current_pod_labels = {}
        try:
            kube_client = kubernetes.KubeOperator()
            for pod_name in self.DEFAULT_LABEL_OVERRIDES:
                pod_desc = kube_client.kube_get_pods_by_selector(
                    app_constants.HELM_CHART_NS_CERT_MANAGER,
                    "app=%s" % pod_name, "")
                for label, value in pod_desc[0].metadata.labels.items():
                    item = {label: value}
                    if item in self.SUPPORTED_COMPONENT_LABELS:
                        current_pod_labels[pod_name] = item
        except exception.HelmOverrideNotFound:
            LOG.debug("Can not read pods's labels. Default value will be used\
                       instead for label overrides.")
        finally:
            if not current_pod_labels:
                current_pod_labels = self.DEFAULT_LABEL_OVERRIDES
        return current_pod_labels

    def _get_helm_overrides(self, dbapi_instance, app, chart, namespace,
                            type_of_overrides):
        helm_overrides = {}
        try:
            helm_overrides = dbapi_instance.helm_override_get(
                app_id=app.id,
                name=chart,
                namespace=namespace,
            )[type_of_overrides]

            if type(helm_overrides) == str:
                helm_overrides = yaml.safe_load(helm_overrides)
        except exception.HelmOverrideNotFound:
            LOG.debug("Overrides for this chart not found, nothing to be done.")
        return helm_overrides
