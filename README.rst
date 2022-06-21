# StarlingX/Cert-Manager-Armada-App

## Introduction
[Cert-Manager](https://cert-manager.io/) is Kubernetes native application that facilities certificate management. This repository deploys Cert-Manager as a platform-managed application using FluxCD Helm Charts for the StarlingX project.

## Build
The build tools available as independent repositories under the StarlingX project are necessary to build this application.

See [StarlingX Build Guide](https://docs.starlingx.io/developer_resources/build_guide.html) for more details.

To build this app:
```
${MY_REPO_ROOT_DIR}/cgcs-root/build-tools/build-pkgs cert-manager-helm stx-cert-manager-helm
```
The generated RPM is located in `$MY_BUILD_DIR/std/rpmbuild/RPMS`.

To extract the tarball without installing on build system, use command:
```
rpm2cpio stx-cert-manager-helm-1.0-0.tis.noarch.rpm | cpio -idmv
```

## Usage
Note that the Cert-Manager application is included on a StarlingX install system by default.

Following commands can be used to upload, apply, remove, delete, and view the application:

```
system application-remove cert-manager
system application-delete cert-manager
system application-upload <.tgz file>
system application-apply cert-manager
system application-list
```

Cert-Manager Kubernetes resources can be found in the `cert-manager` namespace.

```
kubectl get namespaces | grep cert-manager
kubectl get crd | grep cert-manager
kubectl get pods --namespace cert-manager
```
