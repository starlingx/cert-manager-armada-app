# Build variables
%global helm_folder /usr/lib/helm

%global sha 6da95758a4751b20cf85b29a3252e993449660eb

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

## Patch definition goes here if required

BuildRequires: helm

%description
StarlingX Cert-Manager Helm Charts

%prep
%setup -n helm-charts-certmanager

## Apply patches here if required

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

# Create the tgz files
cp %{SOURCE3} deploy/charts
which make
cd deploy/charts
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
