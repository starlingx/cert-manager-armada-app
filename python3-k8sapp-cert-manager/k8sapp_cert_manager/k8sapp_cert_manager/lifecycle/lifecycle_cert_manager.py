#
# Copyright (c) 2022,2025 Wind River Systems, Inc.
#
# SPDX-License-Identifier: Apache-2.0
#
# All Rights Reserved.
#

""" System inventory App lifecycle operator."""
# Temporary disable pylint for lifecycle hooks until Ic83fbd25d23ae34889cb288330ec448f920bda39 merges
# This will be reverted in a future commit
# pylint: disable=no-member
# pylint: disable=no-name-in-module
import os
import time

from oslo_log import log as logging
from sysinv.common import constants
from sysinv.common import exception
from sysinv.common import kubernetes
from sysinv.helm import lifecycle_base as base
from sysinv.helm import lifecycle_utils as lifecycle_utils
from sysinv.helm.lifecycle_constants import LifecycleConstants

LOG = logging.getLogger(__name__)
NAMESPACE = "cert-manager"
CERT_MANAGER_GROUP = 'cert-manager.io'
CERT_MANAGER_VERSION = 'v1'
CERT_NAME = "stx-test-cm"
CERT_SECRET_NAME = "stx-test-cm"
ISSUER_NAME = "system-local-ca"
ISSUER_PLURAL = "issuers"
PLURAL_NAME_CERT = 'certificates'
TEST_CERT_RETRIES = 60
ISSUER = {
    'apiVersion': f'{CERT_MANAGER_GROUP}/{CERT_MANAGER_VERSION}',
    'kind': 'Issuer',
    'metadata': {
        'creationTimestamp': None,
        'name': ISSUER_NAME,
        'namespace': NAMESPACE
    },
    'spec': {
        'ca': {
            'secretName': ISSUER_NAME
        }
    },
    'status': {}
}
CERT = {
    'apiVersion': 'cert-manager.io/v1',
    'kind': 'Certificate',
    'metadata': {
        'creationTimestamp': None,
        'name': CERT_NAME,
        'namespace': NAMESPACE
    },
    'spec': {
        'commonName': CERT_NAME,
        'issuerRef': {
            'kind': 'Issuer',
            'name': ISSUER_NAME,
            'namespace': NAMESPACE
        },
        'secretName': CERT_SECRET_NAME,
    }
}


class CertManagerAppLifecycleOperator(base.AppLifecycleOperator):

    def app_lifecycle_actions(self, context, conductor_obj, app_op, app, hook_info):
        """ Perform lifecycle actions for an operation

        :param context: request context
        :param conductor_obj: conductor object
        :param app_op: AppOperator object
        :param app: AppOperator.Application object
        :param hook_info: LifecycleHookInfo object

        """
        # Semantic checks
        if hook_info.lifecycle_type == LifecycleConstants.APP_LIFECYCLE_TYPE_SEMANTIC_CHECK:
            if hook_info.mode == LifecycleConstants.APP_LIFECYCLE_MODE_AUTO and \
                    hook_info.operation == constants.APP_APPLY_OP and \
                    hook_info.relative_timing == LifecycleConstants.APP_LIFECYCLE_TIMING_PRE:
                return self.pre_auto_apply_check()

        # Rbd
        elif hook_info.lifecycle_type == LifecycleConstants.APP_LIFECYCLE_TYPE_RBD:
            if hook_info.operation == constants.APP_APPLY_OP and \
                    hook_info.relative_timing == LifecycleConstants.APP_LIFECYCLE_TIMING_PRE:
                return lifecycle_utils.create_rbd_provisioner_secrets(app_op, app, hook_info)
            elif hook_info.operation == constants.APP_REMOVE_OP and \
                    hook_info.relative_timing == LifecycleConstants.APP_LIFECYCLE_TIMING_POST:
                return lifecycle_utils.delete_rbd_provisioner_secrets(app_op, app, hook_info)

        # Resources
        elif hook_info.lifecycle_type == LifecycleConstants.APP_LIFECYCLE_TYPE_RESOURCE:
            if hook_info.operation == constants.APP_APPLY_OP and \
                    hook_info.relative_timing == LifecycleConstants.APP_LIFECYCLE_TIMING_PRE:
                lifecycle_utils.create_local_registry_secrets(app_op, app, hook_info)
                lifecycle_utils.add_pod_security_admission_controller_labels(app_op, app, hook_info)
                return
            elif hook_info.operation == constants.APP_REMOVE_OP and \
                    hook_info.relative_timing == LifecycleConstants.APP_LIFECYCLE_TIMING_POST:
                return lifecycle_utils.delete_local_registry_secrets(app_op, app, hook_info)

        # FluxCD request
        elif hook_info.lifecycle_type == LifecycleConstants.APP_LIFECYCLE_TYPE_FLUXCD_REQUEST:
            if hook_info.operation == constants.APP_APPLY_OP and \
                    hook_info.relative_timing == LifecycleConstants.APP_LIFECYCLE_TIMING_STATUS \
                    and not os.path.isfile(constants.ANSIBLE_BOOTSTRAP_FLAG):
                return self.issue_test_cert()

        # Use the default behaviour for other hooks
        super(CertManagerAppLifecycleOperator, self).app_lifecycle_actions(
            context, conductor_obj, app_op, app, hook_info)

    def pre_auto_apply_check(self):
        """ Semantic check for auto-apply

        Disable auto-apply during bootstrap.

        """
        # Apply is controlled by ansible-playbooks during bootstrap.
        if os.path.isfile(constants.ANSIBLE_BOOTSTRAP_FLAG):
            raise exception.LifecycleSemanticCheckException(
                "Auto-apply disabled during bootstrap.")

    def issue_test_cert(self):
        """ Issue a test certificate to ensure cert-manager is functional """

        LOG.info("Issue test certificate to assert cert-manager readiness.")
        kubernetes_operator = kubernetes.KubeOperator()

        # Delete any pre-existing test certificate
        try:
            kubernetes_operator.delete_custom_resource(CERT_MANAGER_GROUP,
                                                       CERT_MANAGER_VERSION,
                                                       NAMESPACE,
                                                       PLURAL_NAME_CERT,
                                                       CERT_NAME)
        except Exception as e:
            LOG.warning(f"Unable to remove existing test certificate: {e}")

        apply_failed = True
        secret_failed = True

        for _ in range(1, TEST_CERT_RETRIES + 1):
            if apply_failed:
                LOG.info("Applying Issuer...")
                try:
                    kubernetes_operator.apply_custom_resource(CERT_MANAGER_GROUP,
                                                              CERT_MANAGER_VERSION,
                                                              NAMESPACE,
                                                              ISSUER_PLURAL,
                                                              ISSUER_NAME,
                                                              ISSUER)
                except Exception as e:
                    LOG.warning(f"Error applying certificate issuer: {e}. Retrying.")
                    time.sleep(3)
                    continue

                LOG.info("Applying test certificate CRD...")
                try:
                    kubernetes_operator.apply_custom_resource(CERT_MANAGER_GROUP,
                                                              CERT_MANAGER_VERSION,
                                                              NAMESPACE,
                                                              PLURAL_NAME_CERT,
                                                              CERT_NAME,
                                                              CERT)
                except Exception as e:
                    LOG.warning(f"Error applying certificate CRD: {e}. Retrying.")
                    time.sleep(3)
                    continue
                apply_failed = False

            LOG.info("Waiting cert-manager to issue the certificate...")
            time.sleep(3)

            try:
                result = kubernetes_operator.kube_get_secret(CERT_SECRET_NAME, NAMESPACE)
                if result:
                    LOG.info("cert-manager is ready to issue certificates.")
                    secret_failed = False
                    break
            except Exception as e:
                LOG.warning(f"Unable to retrieve secret: {e}")

        # Cleanup
        try:
            kubernetes_operator.delete_custom_resource(CERT_MANAGER_GROUP,
                                                       CERT_MANAGER_VERSION,
                                                       NAMESPACE,
                                                       PLURAL_NAME_CERT,
                                                       CERT_NAME)
        except Exception as e:
            LOG.warning(f"Unable to remove existing test certificate: {e}")

        if secret_failed:
            raise exception.SysinvException("Cert-manager is not ready after the allotted time. "
                                            "Check the pod logs.")
