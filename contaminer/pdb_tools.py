# -*- coding : utf-8 -*-

##    Copyright (C) 2017 King Abdullah University of Science and Technology
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

"""Module to manage a PDB files."""

import re

class PDBHandler:
    """A class to extract information from a PDB file."""
    
    def __init__(self, pdb_filename):
        self.pdb_filename = pdb_filename

    # See http://www.wwpdb.org/documentation/file-format
    def get_r_free(self):
        """
        Give the R free value of the PDB file, or `None` if it is not found.
        Raise a `ValueError` if the given R free value is not a number
        """
        r_free_lines = []
        regex = re.compile(r'FREE R VALUE +: *(\d+\.?\d*)')
        with open(self.pdb_filename) as f:
            for line in f:
                try:
                    command = line[0:6]
                    number = line[7:10]
                    description = line[11:]
                except IndexError:
                    # Line does not follow the full line format
                    # Continue to next line
                    continue

                if "REMARK" in command:
                    match = regex.search(description)
                    if match:
                        try:
                            value = float(match.group(1))
                        except ValueError:
                            raise ValueError("Mal formed line: " + line)

                        return value
        # No R FREE line has been found
        return None
