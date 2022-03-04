# Application tunables (maps to metadata)
%global app_name cert-manager
%global helm_repo stx-platform

# Install location
%global app_folder /usr/local/share/applications/helm

# Build variables
%global helm_folder /usr/lib/helm

%global fluxcd_cm_version 1.7.1

Summary: StarlingX Cert-Manager Armada Helm Charts
Name: stx-cert-manager-helm
Version: 1.0
Release: %{tis_patch_ver}%{?_tis_dist}
License: Apache-2.0
Group: base
Packager: Wind River <info@windriver.com>
URL: unknown

Source0: helm-charts-certmanager-%{version}.tar.gz
Source1: Makefile

# fluxcd specific source items
Source4: 0001-Patch-for-acmesolver-and-chartyaml-cm-v1.7.1.patch
Source5: helm-charts-certmanager-%{fluxcd_cm_version}.tar.gz
Source6: kustomization.yaml
Source7: base_helmrepository.yaml
Source8: base_kustomization.yaml
Source9: base_namespace.yaml
Source10: cert-manager_helmrelease.yaml
Source11: cert-manager_kustomization.yaml
Source12: cert-manager_cert-manager-static-overrides.yaml
Source13: cert-manager_cert-manager-system-overrides.yaml

BuildArch: noarch

BuildRequires: helm
BuildRequires: chartmuseum
BuildRequires: cert-manager-helm
BuildRequires: python-k8sapp-cert-manager
BuildRequires: python-k8sapp-cert-manager-wheels

%description
StarlingX Cert-Manager Armada Helm Charts

%package fluxcd
Summary: StarlingX Cert-Manager Application FluxCD Helm Charts
Group: base
License: Apache-2.0

%description fluxcd
StarlingX Cert-Manager Application FluxCD Helm Charts

%prep
%setup -n helm-charts-certmanager-%{version}

%build
# Host a server for the charts
chartmuseum --debug --port=8879 --context-path='/charts' --storage="local" --storage-local-rootdir="." &
sleep 2
helm repo add local http://localhost:8879/charts

# Make the charts. These produce a tgz file
cd helm-charts
make psp-rolebinding
cd -

# set up fluxcd tar source
cd %{_builddir}
rm -rf fluxcd
/usr/bin/mkdir -p fluxcd
cd fluxcd
/usr/bin/tar xfv /builddir/build/SOURCES/helm-charts-certmanager-%{fluxcd_cm_version}.tar.gz

cd %{_builddir}/fluxcd/helm-charts
cp %{SOURCE4} .
patch -p1 < %{SOURCE4}
rm -f deploy/charts/cert-manager/templates/deployment.yaml.orig

# Copy CRD yaml files to templates
cp deploy/crds/*.yaml deploy/charts/cert-manager/templates/

# Create the tgz files
cp %{SOURCE1} deploy/charts
cd deploy/charts

# In Cert-manager release, 'helm lint' fails
# on templates/BUILD.bazel (with invalid file extension)
# Removing the problem file
rm cert-manager/templates/BUILD.bazel

make cert-manager
mv *.tgz %{app_name}-fluxcd-%{version}-%{tis_patch_ver}.tgz
cd -

# terminate helm server (the last backgrounded task)
kill %1

# Create a chart tarball compliant with sysinv kube-app.py
%define app_staging %{_builddir}/staging
%define app_tarball_armada %{app_name}-%{version}-%{tis_patch_ver}.tgz
%define app_tarball_fluxcd %{app_name}-fluxcd-%{version}-%{tis_patch_ver}.tgz

# Setup staging
cd %{_builddir}/helm-charts-certmanager-%{version}
mkdir -p %{app_staging}
cp files/metadata.yaml %{app_staging}
cp manifests/*.yaml %{app_staging}
mkdir -p %{app_staging}/charts
cp helm-charts/*.tgz %{app_staging}/charts
cp %{helm_folder}/cert*.tgz %{app_staging}/charts
cd %{app_staging}

# Populate metadata
sed -i 's/@APP_NAME@/%{app_name}/g' %{app_staging}/metadata.yaml
sed -i 's/@APP_VERSION@/%{version}-%{tis_patch_ver}/g' %{app_staging}/metadata.yaml
sed -i 's/@HELM_REPO@/%{helm_repo}/g' %{app_staging}/metadata.yaml

# Copy the plugins: installed in the buildroot
mkdir -p %{app_staging}/plugins
cp /plugins/%{app_name}/*.whl %{app_staging}/plugins

# package armada
find . -type f ! -name '*.md5' -print0 | xargs -0 md5sum > checksum.md5
tar -zcf %{_builddir}/%{app_tarball_armada} -C %{app_staging}/ .

# package fluxcd
rm -f %{app_staging}/certmanager-manifest.yaml
rm -f %{app_staging}/charts/*.tgz
cp %{_builddir}/fluxcd/helm-charts/deploy/charts/*.tgz %{app_staging}/charts
cp %{_builddir}/helm-charts-certmanager-%{version}/helm-charts/psp*.tgz %{app_staging}/charts
fluxcd_dest=%{app_staging}/fluxcd-manifests
mkdir -p $fluxcd_dest
cp %{SOURCE6} %{app_staging}/fluxcd-manifests
cd %{_sourcedir}
directories="base cert-manager"
for dir in $directories;
do
  mkdir -p $dir
  prefix="${dir}_"
  for file in ${dir}_*; do
    mv $file $dir/"${file#$prefix}"
  done
  cp -r $dir $fluxcd_dest
done
cd -

find . -type f ! -name '*.md5' -print0 | xargs -0 md5sum > checksum.md5
tar -zcf %{_builddir}/%{app_tarball_fluxcd} -C %{app_staging}/ .

# Cleanup staging
rm -fr %{app_staging}

%install
install -d -m 755 %{buildroot}/%{app_folder}
install -p -D -m 755 %{_builddir}/%{app_tarball_armada} %{buildroot}/%{app_folder}
install -p -D -m 755 %{_builddir}/%{app_tarball_fluxcd} %{buildroot}/%{app_folder}

%files
%defattr(-,root,root,-)
%{app_folder}/%{app_tarball_armada}

%files fluxcd
%defattr(-,root,root,-)
%{app_folder}/%{app_tarball_fluxcd}
