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

## This script communicates with the script temrinate.sh on the webserver to 
## complete a job.

# Copy this script to the ContaMiner installation on the cluster, overwrite 
# existing finish.sh script, and change the path to the finish_webserver.sh
# script
path_terminate="webserver/contaminer/finish_webserver.sh"

job_name=$(basename $(dirname "$1"))
job_id=$(echo "$job_name" | sed 's/contaminer_\([0-9]*\)/\1/')
ssh webserver "sh $path_terminate $job_id"