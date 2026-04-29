#!/bin/sh
set -eu
dpkg-buildpackage -us -uc -b
