#define as arch specific (1)
%define python_sitelib %(%{__python} -c "from distutils.sysconfig import get_python_lib; print get_python_lib(1)")

#define to 0 for final version
%define svn_version 0
%define with_adns 0
%define with_lua 0
%if 0%{?rhel} != 0
%define with_portaudio 0
%else
%define with_portaudio 1
%endif

Summary: 	Network traffic analyzer
Name: 		wireshark
Version:	1.2.15
%if %{svn_version}
Release: 	0.%{svn_version}%{?dist}
%else
Release: 	1%{?dist}.1
%endif
License: 	GPL+
Group: 		Applications/Internet
%if %{svn_version}
#  svn export http://anonsvn.wireshark.org/wireshark/trunk wireshark-%{version}-SVN-%{svn_version}
Source0:	http://www.wireshark.org/download/automated/src/wireshark-%{version}-SVN-%{svn_version}.tar.bz2
%else
Source0:	http://wireshark.org/download/src/%{name}-%{version}.tar.bz2
%endif
Source1:	wireshark.pam
Source2:	wireshark.console
Source3:	wireshark.desktop
Source4:	wireshark-autoconf.m4
Patch2:		wireshark-nfsv4-opts.patch
Patch3:		wireshark-0.99.7-path.patch
Patch4:		wireshark-1.1.2-nfs41-backchnl-decode.patch
Patch6:		wireshark-1.2.4-enable_lua.patch
Patch7:		wireshark-1.2.8-disable_warning_dialog.patch
Patch8:		wireshark-1.2.6-nfs40-backchnl-decode.patch
Patch9:		wireshark-1.2.6-smb-find-full-dir-info.patch
Patch10:	wireshark-libtool-pie.patch

Url: 		http://www.wireshark.org/
BuildRoot: 	%{_tmppath}/%{name}-%{version}-%{release}-root-%(%{__id_u} -n)
BuildRequires:	libpcap-devel >= 0.9
BuildRequires: 	libsmi-devel
BuildRequires: 	zlib-devel, bzip2-devel
BuildRequires:  openssl-devel
BuildRequires:	glib2-devel, gtk2-devel
BuildRequires:  elfutils-devel, krb5-devel
BuildRequires:  python, pcre-devel, libselinux
BuildRequires:  gnutls-devel
BuildRequires:  desktop-file-utils, automake, libtool
BuildRequires:	xdg-utils
BuildRequires: 	flex, bison, python
%if %{with_adns}
BuildRequires:	adns-devel
%endif
%if %{with_portaudio}
BuildRequires: portaudio-devel
%endif
%if %{with_lua}
BuildRequires:	lua-devel
%endif
Obsoletes:	ethereal
Provides:	ethereal


%package	gnome
Summary:	Gnome desktop integration for wireshark and wireshark-usermode
Group:		Applications/Internet
Requires: 	gtk2
Requires:	usermode >= 1.37
Requires:	wireshark = %{version}-%{release}
Requires:	libsmi
Requires:	xdg-utils, usermode-gtk
%if %{with_adns}
Requires:	adns
%endif
%if %{with_portaudio}
Requires:	portaudio
%endif
Obsoletes:	ethereal-gnome
Provides:	ethereal-gnome

%package devel
Summary:        Development headers and libraries for wireshark
Group:		Development/Libraries
Requires:       %{name} = %{version}-%{release} glibc-devel glib2-devel


%description
Wireshark is a network traffic analyzer for Unix-ish operating systems.

This package lays base for libpcap, a packet capture and filtering 
library, contains command-line utilities, contains plugins and 
documentation for wireshark. A graphical user interface is packaged 
separately to GTK+ package.

%description gnome
Contains wireshark for Gnome 2 and desktop integration file

%description devel
The wireshark-devel package contains the header files, developer
documentation, and libraries required for development of wireshark scripts
and plugins.


%prep
%if %{svn_version}
%setup -q -n %{name}-%{version}-SVN-%{svn_version}
%else
%setup -q -n %{name}-%{version}
%endif
%patch2 -p1 
%patch3 -p1
%patch4 -p1

%if %{with_lua}
%patch6 -p1 -b .enable_lua
%endif

%patch7 -p1 -b .dialog
%patch8 -p1
%patch9 -p1
%patch10 -p1

%build
%ifarch s390 s390x sparcv9 sparc64
export PIECFLAGS="-fPIE"
%else
export PIECFLAGS="-fpie"
%endif
# FC5+ automatic -fstack-protector-all switch
export RPM_OPT_FLAGS=${RPM_OPT_FLAGS//-fstack-protector/-fstack-protector-all}
export CFLAGS="$RPM_OPT_FLAGS $CPPFLAGS $PIECFLAGS -fno-strict-aliasing"
export CXXFLAGS="$RPM_OPT_FLAGS $CPPFLAGS $PIECFLAGS -fno-strict-aliasing"
export LDFLAGS="$LDFLAGS -lm -lcrypto -pie"
%if %{svn_version}
./autogen.sh
%endif

%configure \
   --bindir=%{_sbindir} \
   --enable-zlib \
   --enable-ipv6 \
   --with-libsmi \
   --with-gnu-ld \
   --enable-gtk2 \
   --with-pic \
%if %{with_adns}
   --with-adns \
%else
   --with-adns=no \
%endif
%if %{with_lua}
   --with-lua \
%else
   --with-lua=no \
%endif
   --with-ssl \
   --disable-warnings-as-errors \
   --with-plugindir=%{_libdir}/%{name}/plugins/%{version} 
make %{?_smp_mflags}

%install
rm -rf $RPM_BUILD_ROOT

# The evil plugins hack
perl -pi -e 's|-L../../epan|-L../../epan/.libs|' plugins/*/*.la

make DESTDIR=$RPM_BUILD_ROOT install

#symlink tshark to tethereal
ln -s tshark $RPM_BUILD_ROOT%{_sbindir}/tethereal

# install support files for usermode, gnome and kde
mkdir -p $RPM_BUILD_ROOT/%{_sysconfdir}/pam.d
install -m 644 %{SOURCE1} $RPM_BUILD_ROOT/%{_sysconfdir}/pam.d/wireshark
mkdir -p $RPM_BUILD_ROOT/%{_sysconfdir}/security/console.apps
install -m 644 %{SOURCE2} $RPM_BUILD_ROOT/%{_sysconfdir}/security/console.apps/wireshark
mkdir -p $RPM_BUILD_ROOT/%{_bindir}
ln -s consolehelper $RPM_BUILD_ROOT/%{_bindir}/wireshark

# install man
mkdir -p $RPM_BUILD_ROOT/%{_mandir}/man1
install -m 644 *.1 $RPM_BUILD_ROOT/%{_mandir}/man1

# Install python stuff.
mkdir -p $RPM_BUILD_ROOT%{python_sitelib}
install -m 644 tools/wireshark_be.py tools/wireshark_gen.py  $RPM_BUILD_ROOT%{python_sitelib}

desktop-file-install --vendor fedora                            \
        --dir ${RPM_BUILD_ROOT}%{_datadir}/applications         \
        --add-category X-Fedora                                 \
        %{SOURCE3}

mkdir -p $RPM_BUILD_ROOT/%{_datadir}/pixmaps
install -m 644 image/wsicon48.png $RPM_BUILD_ROOT/%{_datadir}/pixmaps/wireshark.png

#install devel files
install -d -m 0755  $RPM_BUILD_ROOT/%{_includedir}/wireshark
IDIR="${RPM_BUILD_ROOT}%{_includedir}/wireshark"
mkdir -p "${IDIR}/epan"
mkdir -p "${IDIR}/epan/ftypes"
mkdir -p "${IDIR}/epan/dfilter"
mkdir -p "${IDIR}/wiretap"
install -m 644 color.h			"${IDIR}/"
install -m 644 register.h		"${IDIR}/"
install -m 644 epan/packet.h		"${IDIR}/epan/"
install -m 644 epan/prefs.h		"${IDIR}/epan/"
install -m 644 epan/proto.h		"${IDIR}/epan/"
install -m 644 epan/tvbuff.h		"${IDIR}/epan/"
install -m 644 epan/pint.h		"${IDIR}/epan/"
install -m 644 epan/to_str.h		"${IDIR}/epan/"
install -m 644 epan/value_string.h	"${IDIR}/epan/"
install -m 644 epan/column_info.h	"${IDIR}/epan/"
install -m 644 epan/frame_data.h	"${IDIR}/epan/"
install -m 644 epan/packet_info.h	"${IDIR}/epan/"
install -m 644 epan/column-utils.h	"${IDIR}/epan/"
install -m 644 epan/epan.h		"${IDIR}/epan/"
install -m 644 epan/range.h		"${IDIR}/epan/"
install -m 644 epan/gnuc_format_check.h	"${IDIR}/epan/"
install -m 644 epan/ipv4.h		"${IDIR}/epan"
install -m 644 epan/nstime.h		"${IDIR}/epan/"
install -m 644 epan/ipv6-utils.h	"${IDIR}/epan/"
install -m 644 epan/guid-utils.h	"${IDIR}/epan/"
install -m 644 epan/exceptions.h	"${IDIR}/epan/"
install -m 644 epan/address.h		"${IDIR}/epan/"
install -m 644 epan/slab.h		"${IDIR}/epan/"
install -m 644 epan/tfs.h		"${IDIR}/epan/"
install -m 644 epan/except.h		"${IDIR}/epan/"
install -m 644 epan/emem.h		"${IDIR}/epan/"
install -m 644 epan/ftypes/ftypes.h	"${IDIR}/epan/ftypes/"
install -m 644 epan/dfilter/dfilter.h	"${IDIR}/epan/dfilter/"
install -m 644 epan/dfilter/drange.h	"${IDIR}/epan/dfilter/"
install -m 644 wiretap/wtap.h		"${IDIR}/wiretap/"

#	Create pkg-config control file.
mkdir -p "${RPM_BUILD_ROOT}%{_libdir}/pkgconfig"
cat > "${RPM_BUILD_ROOT}%{_libdir}/pkgconfig/wireshark.pc" <<- "EOF"
	prefix=%{_prefix}
	exec_prefix=%{_prefix}
	libdir=%{_libdir}
	includedir=%{_includedir}

	Name:		%{name}
	Description:	Network Traffic Analyzer
	Version:	%{version}
	Requires:	glib-2.0 gmodule-2.0
	Libs:		-L${libdir} -lwireshark -lwiretap
	Cflags:		-DWS_VAR_IMPORT=extern -DHAVE_STDARG_H -I${includedir}/wireshark -I${includedir}/wireshark/epan
EOF

#	Install the autoconf macro.
mkdir -p "${RPM_BUILD_ROOT}%{_datadir}/aclocal"
cp "%{SOURCE4}" "${RPM_BUILD_ROOT}%{_datadir}/aclocal/wireshark.m4"

# Remove .la files
rm -f $RPM_BUILD_ROOT/%{_libdir}/%{name}/plugins/%{version}/*.la

# Remove .la files in libdir
rm -f $RPM_BUILD_ROOT/%{_libdir}/*.la

%clean
rm -rf $RPM_BUILD_ROOT

%post -p /sbin/ldconfig

%postun -p /sbin/ldconfig

%files
%defattr(-,root,root)
%doc AUTHORS COPYING ChangeLog INSTALL NEWS README* 
%{_sbindir}/editcap
#%{_sbindir}/idl2wrs
%{_sbindir}/tshark
%{_sbindir}/mergecap
%{_sbindir}/text2pcap
%{_sbindir}/dftest
%{_sbindir}/capinfos
%{_sbindir}/randpkt
%{_sbindir}/dumpcap
%{_sbindir}/tethereal
%{_sbindir}/rawshark
%{python_sitelib}/*
%{_libdir}/lib*.so.*
%{_libdir}/wireshark/plugins
%{_mandir}/man1/editcap.*
%{_mandir}/man1/tshark.*
%{_mandir}/man1/mergecap.*
%{_mandir}/man1/text2pcap.*
%{_mandir}/man1/capinfos.*
%{_mandir}/man1/dumpcap.*
%{_mandir}/man4/wireshark-filter.*
%{_mandir}/man1/rawshark.*
#%{_libdir}/wireshark
%config(noreplace) %{_sysconfdir}/pam.d/wireshark
%config(noreplace) %{_sysconfdir}/security/console.apps/wireshark
%{_datadir}/wireshark

%files gnome
%defattr(-,root,root)
%{_datadir}/applications/fedora-wireshark.desktop
%{_datadir}/pixmaps/wireshark.png
%{_bindir}/wireshark
%{_sbindir}/wireshark
%{_mandir}/man1/wireshark.*

%files devel
%defattr(-,root,root)
%doc doc/README.*
%if %{with_lua}
%config(noreplace) %{_datadir}/wireshark/init.lua
%endif
%{_includedir}/wireshark
%{_libdir}/lib*.so
%{_libdir}/pkgconfig/*
%{_datadir}/aclocal/*
%{_mandir}/man1/idl2wrs.*
%{_sbindir}/idl2wrs

%changelog
* Tue Mar  8 2011 Jan Safranek <jsafrane@redhat.com> 1.2.15-1
- upgrade to 1.2.15
- see http://www.wireshark.org/docs/relnotes/wireshark-1.2.14.html
- see http://www.wireshark.org/docs/relnotes/wireshark-1.2.15.html
- Resolves: CVE-2011-0444 CVE-2011-0538 CVE-2011-0713 CVE-2011-1139
  CVE-2011-1140 CVE-2011-1141 CVE-2011-1143

* Wed Jan  5 2011 Jan Safranek <jsafrane@redhat.com> 1.2.13-1.1
- fix buffer overflow in ENTTEC dissector
- Resolves: #667337

* Fri Nov 26 2010 Jan Safranek <jsafrane@redhat.com> 1.2.13-1
- upgrade to 1.2.13
- see http://www.wireshark.org/docs/relnotes/wireshark-1.2.11.html
- see http://www.wireshark.org/docs/relnotes/wireshark-1.2.12.html
- see http://www.wireshark.org/docs/relnotes/wireshark-1.2.13.html
- Resolves: #657534 (CVE-2010-4300 CVE-2010-3445)

* Mon Aug 16 2010 Jan Safranek <jsafrane@redhat.com> 1.2.10-2
- fix crash when processing SCTP packets (#624032)

* Tue Aug 10 2010 Jan Safranek <jsafrane@redhat.com> 1.2.10-1
- upgrade to 1.2.10
- see http://www.wireshark.org/docs/relnotes/wireshark-1.2.10.html
- Resolves: #604312 (proper fix for CVE-2010-2284)

* Mon Jun 28 2010 Petr Lautrbach <plautrba@redhat.com> 1.2.9-2
- save and check child exit status
- Resolves: #579990

* Wed Jun 16 2010 Radek Vokal <rvokal@redhat.com> - 1.2.9-1
- upgrade to 1.2.9
- see http://www.wireshark.org/docs/relnotes/wireshark-1.2.9.html
- Resolves: #604312

* Mon May 10 2010 Radek Vokal <rvokal@redhat.com> - 1.2.8-1
- upgrade to 1.2.8
- see http://www.wireshark.org/docs/relnotes/wireshark-1.2.8.html
- use sitearch instead of sitelib to avoid pyo and pyc conflicts 
- bring back -pie
- add patch to allow decode of NFSv4.0 callback channel
- add patch to allow decode of more SMB FIND_FILE infolevels

* Thu Feb 25 2010 Radek Vokal <rvokal@redhat.com> - 1.2.6-2
- remove `time' from spec file

* Mon Feb 22 2010 Radek Vokal <rvokal@redhat.com> - 1.2.6-1
- upgrade to 1.2.6
- see http://www.wireshark.org/docs/relnotes/wireshark-1.2.6.html 
- minor spec file tweaks for better svn checkout support (#553500)
- init.lua is present always and not only when lua support is enabled
- fix file list, init.lua is only in -devel subpackage (#552406)
- Autoconf macro for plugin development.

* Fri Dec 18 2009 Radek Vokal <rvokal@redhat.com> - 1.2.5-1
- upgrade to 1.2.5
- fixes security vulnaribilities, see http://www.wireshark.org/security/wnpa-sec-2009-09.html 

* Thu Dec 17 2009 Radek Vokal <rvokal@redhat.com> - 1.2.4-3
- split -devel package (#547899, #203642, #218451)
- removing root warning dialog (#543709)

* Mon Dec 14 2009 Radek Vokal <rvokal@redhat.com> - 1.2.4-2
- enable lua support - http://wiki.wireshark.org/Lua
- attempt to fix filter crash on 64bits

* Wed Nov 18 2009 Radek Vokal <rvokal@redhat.com> - 1.2.4-1
- upgrade to 1.2.4
- http://www.wireshark.org/docs/relnotes/wireshark-1.2.4.html

* Fri Oct 30 2009 Radek Vokal <rvokal@redhat.com> - 1.2.3-1
- upgrade to 1.2.3
- http://www.wireshark.org/docs/relnotes/wireshark-1.2.3.html

* Mon Sep 21 2009 Radek Vokal <rvokal@redhat.com> - 1.2.2-1
- upgrade to 1.2.2
- http://www.wireshark.org/docs/relnotes/wireshark-1.2.2.html

* Mon Sep 14 2009 Bill Nottingham <notting@redhat.com> - 1.2.1-5
- do not use portaudio in RHEL

* Fri Aug 28 2009 Radek Vokal <rvokal@redhat.com> - 1.2.1-4
- yet anohter rebuilt

* Fri Aug 21 2009 Tomas Mraz <tmraz@redhat.com> - 1.2.1-3
- rebuilt with new openssl

* Mon Jul 27 2009 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 1.2.1-2
- Rebuilt for https://fedoraproject.org/wiki/Fedora_12_Mass_Rebuild

* Wed Jul 22 2009 Radek Vokal <rvokal@redhat.com> - 1.2.1
- upgrade to 1.2.1
- http://www.wireshark.org/docs/relnotes/wireshark-1.2.1.html

* Tue Jun 16 2009 Radek Vokal <rvokal@redhat.com> - 1.2.0
- upgrade to 1.2.0
- http://www.wireshark.org/docs/relnotes/wireshark-1.2.0.html

* Fri May 22 2009 Radek Vokal <rvokal@redhat.com> - 1.1.4-0.pre1
- update to latest development build

* Thu Mar 26 2009 Radek Vokal <rvokal@redhat.com> - 1.1.3-1
- upgrade to 1.1.3

* Thu Mar 26 2009 Radek Vokal <rvokal@redhat.com> - 1.1.2-4.pre1
- fix libsmi support

* Wed Feb 25 2009 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 1.1.2-3.pre1
- Rebuilt for https://fedoraproject.org/wiki/Fedora_11_Mass_Rebuild

* Mon Feb 16 2009 Radek Vokal <rvokal@redhat.com> - 1.1.2-2.pre1
- add netdump support

* Sun Feb 15 2009 Steve Dickson <steved@redhat.com> - 1.1.2-1.pre1
- NFSv4.1: Add support for backchannel decoding

* Mon Jan 19 2009 Radek Vokal <rvokal@redhat.com> - 1.1.2-0.pre1
- upgrade to latest development release
- added support for portaudio (#480195)

* Sun Jan 18 2009 Tomas Mraz <tmraz@redhat.com> - 1.1.1-0.pre1.2
- rebuild with new openssl

* Sat Nov 29 2008 Ignacio Vazquez-Abrams <ivazqueznet+rpm@gmail.com> - 1.1.1-0.pre1.1
- Rebuild for Python 2.6

* Thu Nov 13 2008 Radek Vokál <rvokal@redhat.com> 1.1.1-0.pre1
- upgrade to 1.1.1 development branch

* Wed Sep 10 2008 Radek Vokál <rvokal@redhat.com> 1.0.3-1
- upgrade to 1.0.3
- Security-related bugs in the NCP dissector, zlib compression code, and Tektronix .rf5 file parser have been fixed. 
- WPA group key decryption is now supported. 
- A bug that could cause packets to be wrongly dissected as "Redback Lawful Intercept" has been fixed. 

* Mon Aug 25 2008 Radek Vokál <rvokal@redhat.com> 1.0.2-3
- fix requires for wireshark-gnome

* Thu Jul 17 2008 Steve Dickson <steved@redhat.com> 1.0.2-2
- Added patches to support NFSv4.1

* Fri Jul 11 2008 Radek Vokál <rvokal@redhat.com> 1.0.2-1
- upgrade to 1.0.2

* Tue Jul  8 2008 Radek Vokál <rvokal@redhat.com> 1.0.1-1
- upgrade to 1.0.1

* Sun Jun 29 2008 Dennis Gilmore <dennis@ausil.us> 1.0.0-3
- add sparc arches to -fPIE 
- rebuild for new gnutls

* Tue Apr  1 2008 Radek Vokál <rvokal@redhat.com> 1.0.0-2
- fix BuildRequires - python, yacc, bison

* Tue Apr  1 2008 Radek Vokál <rvokal@redhat.com> 1.0.0-1
- April Fools' day upgrade to 1.0.0

* Tue Feb 19 2008 Fedora Release Engineering <rel-eng@fedoraproject.org> - 0.99.7-3
- Autorebuild for GCC 4.3

* Wed Dec 19 2007 Radek Vokál <rvokal@redhat.com> 0.99.7-2
- fix crash in unprivileged mode (#317681)

* Tue Dec 18 2007 Radek Vokál <rvokal@redhat.com> 0.99.7-1
- upgrade to 0.99.7

* Fri Dec  7 2007 Radek Vokál <rvokal@redhat.com> 0.99.7-0.pre2.1
- rebuilt for openssl

* Mon Nov 26 2007 Radek Vokal <rvokal@redhat.com> 0.99.7-0.pre2
- switch to libsmi from net-snmp
- disable ADNS due to its lack of Ipv6 support
- 0.99.7 prerelease 2

* Tue Nov 20 2007 Radek Vokal <rvokal@redhat.com> 0.99.7-0.pre1
- upgrade to 0.99.7 pre-release

* Wed Sep 19 2007 Radek Vokál <rvokal@redhat.com> 0.99.6-3
- fixed URL

* Thu Aug 23 2007 Radek Vokál <rvokal@redhat.com> 0.99.6-2
- rebuilt

* Mon Jul  9 2007 Radek Vokal <rvokal@redhat.com> 0.99.6-1
- upgrade to 0.99.6 final

* Fri Jun 15 2007 Radek Vokál <rvokal@redhat.com> 0.99.6-0.pre2
- another pre-release
- turn on ADNS support

* Wed May 23 2007 Radek Vokál <rvokal@redhat.com> 0.99.6-0.pre1
- update to pre1 of 0.99.6 release

* Mon Feb  5 2007 Radek Vokál <rvokal@redhat.com> 0.99.5-1
- multiple security issues fixed (#227140)
- CVE-2007-0459 - The TCP dissector could hang or crash while reassembling HTTP packets
- CVE-2007-0459 - The HTTP dissector could crash.
- CVE-2007-0457 - On some systems, the IEEE 802.11 dissector could crash.
- CVE-2007-0456 - On some systems, the LLT dissector could crash.

* Mon Jan 15 2007 Radek Vokal <rvokal@redhat.com> 0.99.5-0.pre2
- another 0.99.5 prerelease, fix build bug and pie flags

* Tue Dec 12 2006 Radek Vokal <rvokal@redhat.com> 0.99.5-0.pre1
- update to 0.99.5 prerelease

* Thu Dec  7 2006 Jeremy Katz <katzj@redhat.com> - 0.99.4-5
- rebuild for python 2.5 

* Tue Nov 28 2006 Radek Vokal <rvokal@redhat.com> 0.99.4-4
- rebuilt for new libpcap and net-snmp

* Thu Nov 23 2006 Radek Vokal <rvokal@redhat.com> 0.99.4-3
- add htmlview to Buildrequires to be picked up by configure scripts (#216918)

* Tue Nov  7 2006 Radek Vokal <rvokal@redhat.com> 0.99.4-2.fc7
- Requires: net-snmp for the list of MIB modules 

* Wed Nov  1 2006 Radek Vokál <rvokal@redhat.com> 0.99.4-1
- upgrade to 0.99.4 final

* Tue Oct 31 2006 Radek Vokál <rvokal@redhat.com> 0.99.4-0.pre2
- upgrade to 0.99.4pre2

* Tue Oct 10 2006 Radek Vokal <rvokal@redhat.com> 0.99.4-0.pre1
- upgrade to 0.99.4-0.pre1

* Fri Aug 25 2006 Radek Vokál <rvokal@redhat.com> 0.99.3-1
- upgrade to 0.99.3
- Wireshark 0.99.3 fixes the following vulnerabilities:
- the SCSI dissector could crash. Versions affected: CVE-2006-4330
- the IPsec ESP preference parser was susceptible to off-by-one errors. CVE-2006-4331
- a malformed packet could make the Q.2931 dissector use up available memory. CVE-2006-4333 

* Tue Jul 18 2006 Radek Vokál <rvokal@redhat.com> 0.99.2-1
- upgrade to 0.99.2

* Wed Jul 12 2006 Jesse Keating <jkeating@redhat.com> - 0.99.2-0.pre1.1
- rebuild

* Tue Jul 11 2006 Radek Vokál <rvokal@redhat.com> 0.99.2-0.pre1
- upgrade to 0.99.2pre1, fixes (#198242)

* Tue Jun 13 2006 Radek Vokal <rvokal@redhat.com> 0.99.1-0.pre1
- spec file changes

* Fri Jun  9 2006 Radek Vokal <rvokal@redhat.com> 0.99.1pre1-1
- initial build for Fedora Core
