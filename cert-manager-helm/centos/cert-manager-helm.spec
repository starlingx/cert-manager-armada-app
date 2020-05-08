# Build variables
%global helm_folder /usr/lib/helm

%global sha 1d6ecc9cf8d841782acb5f3d3c28467c24c5fd18

Summary: Cert-Manager helm charts
Name: cert-manager-helm
Version: 1.0
Release: %{tis_patch_ver}%{?_tis_dist}
License: Apache-2.0
Group: base
Packager: Wind River <info@windriver.com>
URL: https://cert-manager.io/docs/installation/kubernetes/

Source0: helm-charts-certmanager-%{sha}.tar.gz
Source1: repositories.yaml
Source2: index.yaml
Source3: Makefile

BuildArch:     noarch

Patch01: 0001-Patch-for-acmesolver.patch

BuildRequires: helm
BuildRequires: chartmuseum

%description
StarlingX Cert-Manager Helm Charts

%prep
%setup -n helm-charts-certmanager

%patch01 -p1

%build
# Host a server for the charts
chartmuseum --debug --port=8879 --context-path='/charts' --storage="local" --storage-local-rootdir="." &
sleep 2
helm repo add local http://localhost:8879/charts

# Copy CRD yaml files to templates
cp deploy/crds/*.yaml deploy/charts/cert-manager/templates/

# Create the tgz files
cp %{SOURCE3} deploy/charts
cd deploy/charts

# In Cert-manager release-0.15, 'helm lint' fails 
# on templates/BUILD.bazel (with invalid file extension)
# Removing the problem file
rm cert-manager/templates/BUILD.bazel

make cert-manager
cd -

# terminate helm server (the last backgrounded task)
kill %1

%install
install -d -m 755 ${RPM_BUILD_ROOT}%{helm_folder}
install -p -D -m 755 deploy/charts/*.tgz ${RPM_BUILD_ROOT}%{helm_folder}

%files
%defattr(-,root,root,-)
%{helm_folder}/*
