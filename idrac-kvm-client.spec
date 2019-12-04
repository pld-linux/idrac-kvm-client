Summary:	iDRAC KVM client script that doesn't require web browser
Name:		idrac-kvm-client
Version:	0.1
Release:	1
License:	BSD
Group:		Applications/System
Source0:	%{name}.py
BuildRequires:	rpmbuild(macros) >= 1.268
Requires:	jre
Requires:	jre-base-X11
Requires:	python3-modules
BuildArch:	noarch
BuildRoot:	%{tmpdir}/%{name}-%{version}-root-%(id -u -n)

%description
iDRAC java KVM client script that doesn't require web browser to initiate
connection. Tested with iDRAC 6.

%prep
%setup -q -c -T

%build

%install
rm -rf $RPM_BUILD_ROOT

install -d $RPM_BUILD_ROOT%{_bindir}

cp -p %{SOURCE0} $RPM_BUILD_ROOT%{_bindir}/%{name}

%clean
rm -rf $RPM_BUILD_ROOT

%files
%defattr(644,root,root,755)
%attr(755,root,root) %{_bindir}/%{name}
