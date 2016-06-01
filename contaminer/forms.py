# -*- coding : utf-8 -*-

##    Copyright (C) 2015 Hungler Arnaud
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

"""
    This module provides the forms for the ContaMiner application
"""

from django import forms
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Field, HTML
from crispy_forms.bootstrap import StrictButton, Tab, TabHolder

class UploadStructure(forms.Form):
    """
        Form to upload a mtz or cif file
    """
    def __init__(self, *args, **kwargs):
        grouped_contaminants = {}
        if kwargs.has_key("grouped_contaminants"):
            grouped_contaminants = kwargs.pop("grouped_contaminants")

        super(UploadStructure, self).__init__(*args, **kwargs)

        self.helper = FormHelper()
        self.helper.layout = Layout(
                TabHolder(
                    Tab('File',
                        Field(
                            'name',
                            'structure_file',
                            'email'
                        ),
                    ),
                    Tab('Contaminants',
                    ),
                ),
                StrictButton(
                    '<span class="ladda-label">Submit</span>',
                    type="submit",
                    css_class="btn btn-primary ladda-button submit_button",
                    data_style="expand-right",
                )
            )

        for category in grouped_contaminants.keys():
            self.helper.layout[0][1].append(HTML("<h3>" + str(category) +
            "</h3>"))
            for contaminant in grouped_contaminants[category]:
                initial = False
                initial = (category == "Protein in E.Coli")
                self.fields[contaminant.uniprot_ID] = forms.BooleanField(
                        label = contaminant.short_name + " - " +\
                                contaminant.long_name,
                        required = False,
                        initial = initial)
                self.helper.layout[0][1].append(contaminant.uniprot_ID)

    name = forms.CharField(max_length = 50, required = False)
    structure_file = forms.FileField()
    email = forms.EmailField(required = True)
