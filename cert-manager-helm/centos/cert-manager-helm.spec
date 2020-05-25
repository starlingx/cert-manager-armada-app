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

%description
StarlingX Cert-Manager Helm Charts

%prep
%setup -n helm-charts-certmanager

%patch01 -p1

%build
# initialize helm and build the toolkit
# helm init --client-only does not work if there is no networking
# The following commands do essentially the same as: helm init
%define helm_home %{getenv:HOME}/.helm
mkdir %{helm_home}
mkdir %{helm_home}/repository
mkdir %{helm_home}/repository/cache
mkdir %{helm_home}/repository/local
mkdir %{helm_home}/plugins
mkdir %{helm_home}/starters
mkdir %{helm_home}/cache
mkdir %{helm_home}/cache/archive

# Stage a repository file that only has a local repo
cp %{SOURCE1} %{helm_home}/repository/repositories.yaml

# Stage a local repo index that can be updated by the build
cp %{SOURCE2} %{helm_home}/repository/local/index.yaml

# Host a server for the charts
helm serve --repo-path . &
helm repo rm local
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
