#!/bin/sh

##    Copyright (C) 2016 Hungler Arnaud
##
##    This program is free software; you can redistribute it and/or modify
##    it under the terms of the GNU General Public License as published by
##    the Free Software Foundation; either version 2 of the License, or
##    (at your option) any later version.
##
##    This program is distributed in the hope that it will be useful,
##    but WITHOUT ANY WARRANTY; without even the implied warranty of
##    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
##    GNU General Public License for more details.
##
##    You should have received a copy of the GNU General Public License along
##    with this program; if not, write to the Free Software Foundation, Inc.,
##    51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.
##
## finish.sh version 1.0.0
## Example script called when a job is completed

apps_dir=$(dirname $(readlink -f $0))
website_dir=$(awk -F "= " '/website_dir/ {print $2}' "$apps_dir/config.ini")
. "$website_dir"venv/bin/activate
python "$website_dir"manage.py terminate $1
echo "yes" | python "$website_dir"manage.py collectstatic
