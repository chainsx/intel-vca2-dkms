#
# Intel VCA Software Stack (VCASS)
#
# Copyright(c) 2017 Intel Corporation.
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License, version 2, as
# published by the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
# General Public License for more details.
#
# The full GNU General Public License is included in this distribution in
# the file called "COPYING".
#
# Intel VCA Scripts.
#

name = daemon-vca

# RPM characteristics
arch = $(shell uname -p)

ifndef PKG_VER
	PKG_VER = 0.0.0
endif
version=$(PKG_VER)
ifndef OS
	OS=CENTOS
endif

ifdef MODULES_SRC
	modules_path=$(MODULES_SRC)
else
	$(error Error: MODULES_SRC not defined!)
endif

release = 0

#  RPM build files and directories
topdir = $(HOME)/rpmbuild
rpm = $(topdir)/RPMS/$(arch)/$(name)-$(version)-$(release).$(arch).rpm
specfile = $(topdir)/SPECS/$(name).spec
source_tar = $(topdir)/SOURCES/$(name)-$(version).tar.gz
src = $(shell cat MANIFEST)
setup = $(topdir)/.setup


# RPM build flags
rpmbuild_flags = -E '%define _topdir $(topdir)'
rpmbuild_flags += -E '%define module_headers_installed true'
rpmclean_flags = $(rpmbuild_flags) --clean --rmsource --rmspec
rpmbuild_flags += -E '%define _version $(version)'

include make.spec

all: $(rpm)

$(rpm): $(specfile) $(source_tar)
	rpmbuild $(rpmbuild_flags) $(specfile) -ba

$(source_tar): $(setup) MANIFEST
	tar czf $@ . --exclude=Makefile --exclude=.git --exclude=CMakeFiles --exclude=CMakeCache.txt --exclude=cmake_install.cmake

$(specfile): $(setup) make.spec
	@echo "$$make_spec" > $@
#	$(error see $(specfile) )

$(setup):
	mkdir -p $(topdir)/{SOURCES,SPECS}
	touch $@

clean:
	-rpmbuild $(rpmclean_flags) $(specfile)

.PHONY: all clean
