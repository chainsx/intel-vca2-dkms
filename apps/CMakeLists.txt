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

cmake_minimum_required (VERSION 3.10)

if(POLICY CMP0167)
    cmake_policy(SET CMP0167 OLD)
endif()

# project name
project (ValleyVistaApps)

if(NOT DEFINED OS)
    set(OS "CENTOS")
    message(STATUS "Setting OS value by default!")
endif()
if(NOT DEFINED PKG_VER)
    set(PKG_VER "0.0.0")
    message(STATUS "Setting PKG_VER value by default!")
endif()

# change to ON if you want to get more logs from Makefile
set(CMAKE_VERBOSE_MAKEFILE ON)

# setting ValleyVistaApps sources
set (vcactl_sources ${PROJECT_SOURCE_DIR}/src/vcactrl.cpp
                    ${PROJECT_SOURCE_DIR}/src/log_args.cpp
                    ${PROJECT_SOURCE_DIR}/src/vca_eeprom_update.cpp)
set (vcactld_sources ${PROJECT_SOURCE_DIR}/src/vcassd.c
                     ${PROJECT_SOURCE_DIR}/src/vcassd_virtio_backend.c
                     ${PROJECT_SOURCE_DIR}/src/vcassd_common.c
                     ${PROJECT_SOURCE_DIR}/src/vca_watchdog.cpp)
set (helper_sources ${PROJECT_SOURCE_DIR}/src/helper_funcs.cpp
                    ${PROJECT_SOURCE_DIR}/src/vca_config_parser.cpp
                    ${PROJECT_SOURCE_DIR}/src/vca_devices.cpp
                    ${PROJECT_SOURCE_DIR}/src/vca_blockio_ctl.cpp)
set (vcactl_headers ${PROJECT_SOURCE_DIR}/src/vcactrl.h
                    ${PROJECT_SOURCE_DIR}/src/log_args.h
                    ${PROJECT_SOURCE_DIR}/src/vca_eeprom_update.h)
set (vcactld_headers ${PROJECT_SOURCE_DIR}/src/vcassd.h
                     ${PROJECT_SOURCE_DIR}/src/vcassd_virtio_backend.h
                     ${PROJECT_SOURCE_DIR}/src/vcassd_common.h)
set (helper_headers ${PROJECT_SOURCE_DIR}/src/helper_funcs.h
                    ${PROJECT_SOURCE_DIR}/src/vca_defs.h
                    ${PROJECT_SOURCE_DIR}/src/vca_config_parser.h
                    ${PROJECT_SOURCE_DIR}/src/vca_devices.h
                    ${PROJECT_SOURCE_DIR}/src/vca_blockio_ctl.h)

# adding OSAL (OS abstraction layer)
if(UNIX)
    set(helper_sources ${helper_sources} ${PROJECT_SOURCE_DIR}/src/linux_osal.cpp)
    set(helper_headers ${helper_headers} ${PROJECT_SOURCE_DIR}/src/linux_osal.h)
elseif(WIN32)
    set(helper_sources ${helper_sources} ${PROJECT_SOURCE_DIR}/src/windows_osal.cpp)
    set(helper_headers ${helper_headers} ${PROJECT_SOURCE_DIR}/src/windows_osal.h)
endif()

# getting ValleyVistaModules path
if(NOT DEFINED MODULES_SRC)
    set(MODULES_SRC "${PROJECT_SOURCE_DIR}/../ValleyVistaModules")
    message(STATUS "Using default MODULES_SRC value!")
endif()
if(EXISTS "${MODULES_SRC}" AND IS_DIRECTORY "${MODULES_SRC}")
    message(STATUS "MODULES_SRC = ${MODULES_SRC}")
else()
    message(FATAL_ERROR "MODULES_SRC directory not exist under path: ${MODULES_SRC}! Exiting!")
endif()
message(STATUS "OS = ${OS}")

# getting boost library path
# change to ON if you want to print more logs from FindBoost.cmake module
set(Boost_DEBUG OFF)
set(Boost_NO_BOOST_CMAKE ON)

if(UNIX)
    # for linux setting to OFF to use shared object installed from boost-devel.<version>x86_64.rpm
    set(Boost_USE_STATIC_LIBS OFF)
else()
    set(Boost_USE_STATIC_LIBS ON)
endif()
set(Boost_USE_STATIC_RUNTIME OFF)
if("x_${OS}" STREQUAL "x_CENTOS")
	#set(Boost_USE_MULTITHREADED ON)	# CentOS: boots MT-safe library in libboost-thread-dev is boost-thread-mt.*
elseif("x_${OS}" STREQUAL "x_UBUNTU" OR "x_${OS}" STREQUAL "x_DEBIAN")
	set(Boost_USE_MULTITHREADED OFF)	# Ubuntu: the -mt suffix has been removed. The installed libboost-thread-dev libraries are MT-safe
endif()
unset(Boost_INCLUDE_DIRS CACHE)		# unnecessary?
unset(Boost_LIBRARY_DIRS CACHE)		# unnecessary?
find_package(Boost
	REQUIRED
	COMPONENTS filesystem thread system date_time
)
if(NOT Boost_FOUND)
    message(FATAL_ERROR "Boost-devel package not installed! Exiting!")
endif()

message(STATUS "Boost_USE_STATIC_LIBS = ${Boost_USE_STATIC_LIBS}")
message(STATUS "Boost_USE_STATIC_RUNTIME = ${Boost_USE_STATIC_RUNTIME}")
message(STATUS "Boost_LIBRARY_DIRS = ${Boost_LIBRARY_DIRS}")
message(STATUS "Boost_INCLUDE_DIRS = ${Boost_INCLUDE_DIRS}")

if(Boost_USE_STATIC_LIBS)
   message(STATUS "Linking against boost static libraries")
else()
   message(STATUS "Linking against boost dynamic libraries")
endif()

# setting compile flags for both Linux and Windows
if(CMAKE_COMPILER_IS_GNUCXX)
    message(STATUS "GCC detected, adding compile flags")
	set(COMMON_FLAGS    "")              							  # Initialize
    option(VCASS_ENABLE_WERROR "Treat compiler warnings as errors" OFF)
    set(COMMON_FLAGS    "${COMMON_FLAGS} -Wall")                       # Turn on common warnings
    if(VCASS_ENABLE_WERROR)
        set(COMMON_FLAGS    "${COMMON_FLAGS} -Werror")
    endif()
    set(COMMON_FLAGS    "${COMMON_FLAGS} -Wformat -Wformat-security") # Format string vulnerabilities
    set(COMMON_FLAGS    "${COMMON_FLAGS} -fstack-protector")          # Stack-based Buffer Overrun Detection
    set(COMMON_FLAGS    "${COMMON_FLAGS} -O2 -D_FORTIFY_SOURCE=2")    # Fortify source
    set(COMMON_FLAGS    "${COMMON_FLAGS} -fPIE -fPIC")                # Position Independent Execution (PIE)
    set(COMMON_FLAGS    "${COMMON_FLAGS} -g")
    set(CMAKE_C_FLAGS   "${CMAKE_C_FLAGS} -g")
    set_property(SOURCE ${PROJECT_SOURCE_DIR}/src/vca_config_parser.cpp APPEND_STRING PROPERTY COMPILE_FLAGS " -lstdc++ ")
    add_definitions("${COMMON_FLAGS}")

    # linker flags used to create executables
    set(CMAKE_EXE_LINKER_FLAGS "-g")                                        # Generate and retain symbol information in the executable
    set(CMAKE_EXE_LINKER_FLAGS "${CMAKE_EXE_LINKER_FLAGS} -z noexecstack")  # Stack execution protection
    set(CMAKE_EXE_LINKER_FLAGS "${CMAKE_EXE_LINKER_FLAGS} -z relro -z now") # Data relocation and protection (RELRO)
    set(CMAKE_EXE_LINKER_FLAGS "${CMAKE_EXE_LINKER_FLAGS} -pie")            # Position Independent Execution (PIE)
    message(STATUS "CMAKE_EXE_LINKER_FLAGS: ${CMAKE_EXE_LINKER_FLAGS}")

    execute_process(COMMAND date +"%Y-%m-%d %H:%M:%S %z" OUTPUT_VARIABLE BUILDDATE)
    string(REGEX REPLACE "\n" "" BUILDDATE ${BUILDDATE})

    if(DEFINED BUILDNO)
	add_definitions(-DBUILDNO=\"${BUILDNO}\" -DBUILDDATE=${BUILDDATE})
    else()
	add_definitions(-DBUILDNO=\"${PKG_VER}\" -DBUILDDATE=${BUILDDATE})
    endif()
else()
    message(FATAL_ERROR "Cannot find any expected compiler!")
endif()

if(DEFINED DEBUG)
    add_definitions(-DDEBUG=${DEBUG})
endif()

set(CMAKE_C_FLAGS   "${CMAKE_C_FLAGS} ${COMMON_FLAGS}")
set(CMAKE_CXX_FLAGS   "${CMAKE_CXX_FLAGS} ${COMMON_FLAGS}")

# printing cmake project settings
message(STATUS "CMAKE_C_FLAGS = ${CMAKE_C_FLAGS}")
message(STATUS "CMAKE_CXX_FLAGS = ${CMAKE_CXX_FLAGS}")
message(STATUS "PROJECT_SOURCE_DIR = ${PROJECT_SOURCE_DIR}")
message(STATUS "CMAKE_BINARY_DIR = ${CMAKE_BINARY_DIR}")

# setting directory for executables
set(CMAKE_RUNTIME_OUTPUT_DIRECTORY ${CMAKE_BINARY_DIR}/bin)
message(STATUS "CMAKE_RUNTIME_OUTPUT_DIRECTORY = ${CMAKE_RUNTIME_OUTPUT_DIRECTORY}")

# adding directories which need to include to projects
include_directories ("${PROJECT_SOURCE_DIR}/src")
include_directories ("${MODULES_SRC}/vca/common")
include_directories ("${MODULES_SRC}/vca/blockio")
include_directories ("${MODULES_SRC}/vca/vca_virtio/uapi")
include_directories(${Boost_INCLUDE_DIRS})

# adding main targets
add_executable(vcactl ${vcactl_sources} ${helper_sources}
                      ${vcactl_headers} ${helper_headers})
add_executable(vcactld ${vcactld_sources} ${helper_sources}
                       ${vcactld_headers} ${helper_headers})
target_include_directories(vcactld PRIVATE ${MODULES_SRC}/vca/vop)
target_include_directories(vcactl PRIVATE ${MODULES_SRC}/vca/vca_csm
                                          ${MODULES_SRC}/vca/vca_mgr
                                          ${MODULES_SRC}/vca/vca_mgr_extd)
target_link_libraries(vcactl pthread rt ${Boost_LIBRARIES})
target_link_libraries(vcactld pthread rt ${Boost_LIBRARIES})

set_property(TARGET vcactl PROPERTY FOLDER "vcactl")
set_property(TARGET vcactld PROPERTY FOLDER "vcactld")

# installing configuration
if(NOT DEFINED DESTDIR)
    set(DESTDIR "${CMAKE_BINARY_DIR}/install_dir")
	message(STATUS "Using default DESTDIR = ${DESTDIR}" )
else()
	message(STATUS "DESTDIR = ${DESTDIR}" )
endif()

set(prefix "/usr")
set(exec_prefix "${prefix}")
set(sbindir "${exec_prefix}/sbin")
set(etcprofiledir "/etc/profile.d")
set(vcaconfigdir "/etc/vca_config.d")
set(udevrulesdir "/lib/udev/rules.d")
set(vcalibdir "/usr/lib/vca")
set(manualdir "/usr/share/man/man1/")
set(compl_dir "/usr/share/bash-completion/completions")
if(	"x_${OS}" STREQUAL "x_CENTOS")
	set(systemd_dir "${prefix}/lib/systemd")	# only correct for CentOS >= 7.0
elseif("x_${OS}" STREQUAL "x_UBUNTU" OR "x_${OS}" STREQUAL "x_DEBIAN")
	set(systemd_dir "/lib/systemd")				# only correct for Ubuntu >= 15.04
endif()
set(services_dir_systemd "${systemd_dir}/system")
set(services_dir_rcd_initd "/etc/rc.d/init.d")
set(tmpfilesconfigdir "/usr/lib/tmpfiles.d")
set(rwxrwxrwx OWNER_READ OWNER_WRITE OWNER_EXECUTE GROUP_READ GROUP_WRITE GROUP_EXECUTE WORLD_READ WORLD_WRITE WORLD_EXECUTE) #777
set(rwxrwxr__ OWNER_READ OWNER_WRITE OWNER_EXECUTE GROUP_READ GROUP_WRITE GROUP_EXECUTE WORLD_READ) #774
set(rwxrwx___ OWNER_READ OWNER_WRITE OWNER_EXECUTE GROUP_READ GROUP_WRITE GROUP_EXECUTE) #770
set(rw_rw_r__ OWNER_READ OWNER_WRITE GROUP_READ GROUP_WRITE WORLD_READ) #664
set(rw_r__r__ OWNER_READ OWNER_WRITE GROUP_READ WORLD_READ)
set(rw_rw____ OWNER_READ OWNER_WRITE GROUP_READ GROUP_WRITE ) #660
set(rwxr_x___ OWNER_READ OWNER_WRITE OWNER_EXECUTE GROUP_READ GROUP_EXECUTE ) #750

# for CentOS 7X and 6X there are different default service mangers (init systems): systemd or SysVinit
# so we need two targets: install_systemd - for CentOS 7X and install_systemV - for CentOS 6X
add_custom_target(install_systemd DEPENDS
	${PROJECT_SOURCE_DIR}/services/vcactl.service
)
add_custom_command(TARGET install_systemd
	COMMAND ${CMAKE_COMMAND} -E make_directory ${DESTDIR}/${services_dir_systemd}
	COMMAND ${CMAKE_COMMAND} -E copy ${PROJECT_SOURCE_DIR}/services/vcactl.service ${DESTDIR}/${services_dir_systemd}
)
add_custom_target(install_systemV DEPENDS
	${PROJECT_SOURCE_DIR}/services/vcactl
)
add_custom_command(TARGET install_systemV
	COMMAND ${CMAKE_COMMAND} -E make_directory ${DESTDIR}/${services_dir_rcd_initd}
	COMMAND ${CMAKE_COMMAND} -E copy ${PROJECT_SOURCE_DIR}/services/vcactl ${DESTDIR}/${services_dir_rcd_initd}
)
execute_process(
	COMMAND cp ${PROJECT_SOURCE_DIR}/vcactl.1 ${PROJECT_SOURCE_DIR}/vcactl.1.bak
	COMMAND gzip ${PROJECT_SOURCE_DIR}/vcactl.1
	COMMAND mv ${PROJECT_SOURCE_DIR}/vcactl.1.bak ${PROJECT_SOURCE_DIR}/vcactl.1
)
# files to be install after build target "install"
install(FILES ${PROJECT_SOURCE_DIR}/services/vcactl.service			PERMISSIONS ${rw_r__r__} DESTINATION ${DESTDIR}${services_dir_systemd})
install(TARGETS vcactl vcactld
	RUNTIME DESTINATION ${DESTDIR}${sbindir}
	PERMISSIONS ${rwxrwxrwx})
install(FILES ${PROJECT_SOURCE_DIR}/vca_config.d/vca_config.xml 		PERMISSIONS ${rw_rw_r__} DESTINATION ${DESTDIR}${vcaconfigdir})
install(FILES ${PROJECT_SOURCE_DIR}/vca_config.d/vca_xen_multicast_config.xml   PERMISSIONS ${rw_rw_r__} DESTINATION ${DESTDIR}${vcaconfigdir})
install(FILES ${PROJECT_SOURCE_DIR}/vca_config.d/vca_daemon_default.sh          PERMISSIONS ${rwxr_x___} DESTINATION ${DESTDIR}${vcaconfigdir})
install(FILES ${PROJECT_SOURCE_DIR}/vca_config.d/vca_auto_boot.sh               PERMISSIONS ${rwxr_x___} DESTINATION ${DESTDIR}${vcaconfigdir})
install(FILES ${PROJECT_SOURCE_DIR}/vca_config.d/MACUpdateImage.img             PERMISSIONS ${rw_rw____} DESTINATION ${DESTDIR}${vcaconfigdir})
install(FILES ${PROJECT_SOURCE_DIR}/vca_config.d/ClearSMBiosEventLogImage.img   PERMISSIONS ${rw_rw____} DESTINATION ${DESTDIR}${vcaconfigdir})
install(FILES ${PROJECT_SOURCE_DIR}/tmpfiles.d/vca.conf                         PERMISSIONS ${rwxrwxrwx} DESTINATION ${DESTDIR}${tmpfilesconfigdir})
install(FILES ${PROJECT_SOURCE_DIR}/rules/95-vca.rules                          PERMISSIONS ${rw_r__r__} DESTINATION ${DESTDIR}${udevrulesdir})
install(FILES ${PROJECT_SOURCE_DIR}/rules/96-vop.rules                          PERMISSIONS ${rw_r__r__} DESTINATION ${DESTDIR}${udevrulesdir})
install(FILES ${PROJECT_SOURCE_DIR}/rules/97-host_eth_up.rules                  PERMISSIONS ${rw_r__r__} DESTINATION ${DESTDIR}${udevrulesdir})
install(FILES ${PROJECT_SOURCE_DIR}/rules/98-vca_mgr.rules                      PERMISSIONS ${rw_r__r__} DESTINATION ${DESTDIR}${udevrulesdir})
install(FILES ${PROJECT_SOURCE_DIR}/rules/99-vca_mgr_extd.rules                 PERMISSIONS ${rw_r__r__} DESTINATION ${DESTDIR}${udevrulesdir})
install(FILES ${PROJECT_SOURCE_DIR}/rules/99-vca_blk_bcknd.rules                PERMISSIONS ${rw_r__r__} DESTINATION ${DESTDIR}${udevrulesdir})
install(FILES ${PROJECT_SOURCE_DIR}/xen_scripts/domUsetup.sh                    PERMISSIONS ${rwxr_x___} DESTINATION ${DESTDIR}${vcalibdir})
install(FILES ${PROJECT_SOURCE_DIR}/xen_scripts/card_vm.hvm                     PERMISSIONS ${rwxrwx___} DESTINATION ${DESTDIR}${vcalibdir})
install(FILES ${PROJECT_SOURCE_DIR}/xen_scripts/card_gfx_vm.hvm                 PERMISSIONS ${rwxrwx___} DESTINATION ${DESTDIR}${vcalibdir})
install(FILES ${PROJECT_SOURCE_DIR}/xen_scripts/windows_card_gfx_vm.hvm         PERMISSIONS ${rwxrwx___} DESTINATION ${DESTDIR}${vcalibdir})
install(FILES ${PROJECT_SOURCE_DIR}/xen_scripts/vca_start_card_domu.sh          PERMISSIONS ${rwxr_x___} DESTINATION ${DESTDIR}${sbindir})
install(FILES ${PROJECT_SOURCE_DIR}/bash_completion/vcactl                      PERMISSIONS ${rw_r__r__} DESTINATION ${DESTDIR}${compl_dir})
install(FILES ${PROJECT_SOURCE_DIR}/scripts/vca_eth_ifup.sh                     PERMISSIONS ${rwxrwxr__} DESTINATION ${DESTDIR}${sbindir})
install(FILES ${PROJECT_SOURCE_DIR}/scripts/make_config.py                      PERMISSIONS ${rwxrwxr__} DESTINATION ${DESTDIR}${vcalibdir})
install(FILES ${PROJECT_SOURCE_DIR}/scripts/vca_config_upgrade.sh               PERMISSIONS ${rwxrwxr__} DESTINATION ${DESTDIR}${sbindir})
install(FILES ${PROJECT_SOURCE_DIR}/kvm_scripts/vca_start_card_kvm.sh		PERMISSIONS ${rwxr_x___} DESTINATION ${DESTDIR}${sbindir})
install(FILES ${PROJECT_SOURCE_DIR}/kvm_scripts/kvmsetup.sh			PERMISSIONS ${rwxr_x___} DESTINATION ${DESTDIR}${vcalibdir})
install(FILES ${PROJECT_SOURCE_DIR}/kvm_scripts/vca_kvmgtctl.sh			PERMISSIONS ${rwxr_x___} DESTINATION ${DESTDIR}${sbindir})
install(FILES ${PROJECT_SOURCE_DIR}/kvm_scripts/kvmgtctl_node.sh		PERMISSIONS ${rwxr_x___} DESTINATION ${DESTDIR}${vcalibdir})
install(FILES ${PROJECT_SOURCE_DIR}/etc_profile_scripts/vcausers_setup_path.sh  PERMISSIONS ${rwxr_x___} DESTINATION ${DESTDIR}${etcprofiledir})
install(FILES ${PROJECT_SOURCE_DIR}/tools/vca_image_resize.sh			PERMISSIONS ${rwxr_x___} DESTINATION ${DESTDIR}${sbindir})
install(FILES ${PROJECT_SOURCE_DIR}/tools/vcainfo				PERMISSIONS ${rwxr_x___} DESTINATION ${DESTDIR}${sbindir})
install(FILES ${PROJECT_SOURCE_DIR}/tools/vcanodeinfo.sh			PERMISSIONS ${rwxr_x___} DESTINATION ${DESTDIR}${vcalibdir})
install(FILES ${PROJECT_SOURCE_DIR}/vcactl.1.gz					PERMISSIONS ${rwxr_x___} DESTINATION ${DESTDIR}${manualdir})

SET(CPACK_GENERATOR "DEB")
SET(CPACK_PACKAGE_VENDOR "Intel Corporation")
SET(CPACK_DEBIAN_PACKAGE_MAINTAINER "Intel Corporation") #required
SET(CPACK_PACKAGE_VERSION ${PKG_VER} )
message(STATUS "CPACK_PACKAGE_VERSION = ${CPACK_PACKAGE_VERSION}")

#SET(CPACK_PACKAGE_FILE_NAME "daemon-vca-${CPACK_PACKAGE_VERSION}")
# CPACK_PACKAGE_FILE_NAME=${CPACK_PACKAGE_NAME}-${CPACK_PACKAGE_VERSION}-${CPACK_SYSTEM_NAME}.
# CPACK_PACKAGE_NAME=PROJECT name
# CPACK_SYSTEM_NAME=CMAKE_SYSTEM_NAME= return of 'uname -s'
SET(CPACK_PACKAGE_NAME "daemon-vca")
SET(CPACK_DEBIAN_PACKAGE_ARCHITECTURE "amd64")	# why not set by default?
SET(CPACK_SYSTEM_NAME ${CPACK_DEBIAN_PACKAGE_ARCHITECTURE} )
# For DEB: conffiles, preinst, postinst, prerm, postrm:
SET(PKG_SCRIP_NAME "${PROJECT_SOURCE_DIR}/pkg_scripts")
set(CPACK_DEBIAN_PACKAGE_CONTROL_EXTRA
    "${PKG_SCRIP_NAME}/preinst"
	"${PKG_SCRIP_NAME}/postinst"
	"${PKG_SCRIP_NAME}/prerm"
	"${PKG_SCRIP_NAME}/postrm")

# Ubuntu 22.04/Jammy runtime dependencies.  The original package pinned
# Ubuntu 16.04-era Boost 1.58 libraries and used python2; both are obsolete.
if("x_${OS}" STREQUAL "x_UBUNTU" OR "x_${OS}" STREQUAL "x_DEBIAN")
	set(CPACK_DEBIAN_PACKAGE_DEPENDS
		"bridge-utils, mtools, libboost-date-time1.74.0, libboost-filesystem1.74.0, libboost-system1.74.0, libboost-thread1.74.0, pciutils, ipcalc, gdisk, coreutils, findutils, e2fsprogs, kpartx, mawk, mount, python3")
else()
	set(CPACK_DEBIAN_PACKAGE_DEPENDS
		"bridge-utils, mtools, boost-date-time, boost-filesystem, boost-system, boost-thread, pciutils, ipcalc, gdisk, coreutils, findutils, e2fsprogs, kpartx, mawk, mount, python3")
endif()

INCLUDE(CPack)

# adding target "clean_cmake_files" to clean-up cmake generated files
add_custom_target(clean_cmake_files)
add_custom_command(TARGET clean_cmake_files
COMMAND ${CMAKE_COMMAND} -E remove ${PROJECT_SOURCE_DIR}/CMakeCache.txt
                                   ${PROJECT_SOURCE_DIR}/cmake_install.cmake
                                   ${PROJECT_SOURCE_DIR}/install_manifest.txt
                                   ${PROJECT_SOURCE_DIR}/Makefile
COMMAND ${CMAKE_COMMAND} -E remove_directory ${PROJECT_SOURCE_DIR}/CMakeFiles)

# unset variables to make sure that next cmake generation will use correct one
unset(MODULES_SRC CACHE)
