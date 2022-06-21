# Application tunables (maps to metadata)
%global app_name cert-manager
%global helm_repo stx-platform

# Install location
%global app_folder /usr/local/share/applications/helm

# Build variables
%global helm_folder /usr/lib/helm

%global cm_version 1.7.1

Summary: StarlingX Cert-Manager Application FluxCD Helm Charts
Name: stx-cert-manager-helm
Version: 1.0
Release: %{tis_patch_ver}%{?_tis_dist}
License: Apache-2.0
Group: base
Packager: Wind River <info@windriver.com>
URL: unknown

Source0: helm-charts-certmanager-%{version}.tar.gz
Source1: Makefile
Source2: 0001-Patch-for-acmesolver-and-chartyaml-cm-v1.7.1.patch
Source3: helm-charts-certmanager-%{cm_version}.tar.gz

BuildArch: noarch

BuildRequires: helm
BuildRequires: chartmuseum
BuildRequires: python-k8sapp-cert-manager
BuildRequires: python-k8sapp-cert-manager-wheels

%description
StarlingX Cert-Manager Application FluxCD Helm Charts

%prep
%setup -n helm-charts-certmanager-%{version}

%build
# Host a server for the charts
chartmuseum --debug --port=8879 --context-path='/charts' --storage="local" --storage-local-rootdir="." &
sleep 2
helm repo add local http://localhost:8879/charts

# Make psp-rolebinding chart. These produce a tgz file
cd helm-charts
make psp-rolebinding
cd -

# Extract the cert-manager chart
cd %{_builddir}
rm -rf fluxcd
/usr/bin/mkdir -p fluxcd
cd fluxcd
/usr/bin/tar xfv %{SOURCE3}

# Apply patches with our modifications
cd %{_builddir}/fluxcd/helm-charts
cp %{SOURCE2} .
patch -p1 < %{SOURCE2}

# Copy CRD yaml files to templates
cp deploy/crds/*.yaml deploy/charts/cert-manager/templates/

# Copy Makefile
cd deploy/charts
cp %{SOURCE1} .

# Remove files causing lint error from cert-manager release
rm cert-manager/templates/BUILD.bazel
rm cert-manager/templates/deployment.yaml.orig

# Make the updated cert-manager helm-chart
make cert-manager
mv *.tgz %{app_name}-%{version}-%{tis_patch_ver}.tgz
cd -

# Terminate helm server (the last background task)
kill %1

# Create a chart tarball compliant with sysinv kube-app.py
%define app_staging %{_builddir}/staging
%define app_tarball %{app_name}-%{version}-%{tis_patch_ver}.tgz

# Setup the staging directory
cd %{_builddir}/helm-charts-certmanager-%{version}
mkdir -p %{app_staging}
cp files/metadata.yaml %{app_staging}
mkdir -p %{app_staging}/charts
cp %{_builddir}/fluxcd/helm-charts/deploy/charts/*.tgz %{app_staging}/charts
cp %{_builddir}/helm-charts-certmanager-%{version}/helm-charts/psp*.tgz %{app_staging}/charts
cp -Rv fluxcd-manifests %{app_staging}/

cd %{app_staging}

# Populate metadata
sed -i 's/@APP_NAME@/%{app_name}/g' %{app_staging}/metadata.yaml
sed -i 's/@APP_VERSION@/%{version}-%{tis_patch_ver}/g' %{app_staging}/metadata.yaml
sed -i 's/@HELM_REPO@/%{helm_repo}/g' %{app_staging}/metadata.yaml

# Copy the plugins: installed in the buildroot
mkdir -p %{app_staging}/plugins
cp /plugins/%{app_name}/*.whl %{app_staging}/plugins

# Generate checksum file and package the tarball
cd -
find . -type f ! -name '*.md5' -print0 | xargs -0 md5sum > checksum.md5
tar -zcf %{_builddir}/%{app_tarball} -C %{app_staging}/ .

# Cleanup staging
rm -fr %{app_staging}

%install
install -d -m 755 %{buildroot}/%{app_folder}
install -p -D -m 755 %{_builddir}/%{app_tarball} %{buildroot}/%{app_folder}

%files
%defattr(-,root,root,-)
%{app_folder}/%{app_tarball}
