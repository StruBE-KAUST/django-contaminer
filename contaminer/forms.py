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

"""
    This module provides the forms for the ContaMiner application
"""

import logging

from django import forms
from django.utils import text
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Field, HTML, Fieldset
from crispy_forms.bootstrap import StrictButton, Tab, TabHolder

class UploadStructure(forms.Form):
    """ Form to upload a mtz or cif file """

    job_name = forms.CharField(max_length = 50, required = False)
    structure_file = forms.FileField()
    confidential = forms.BooleanField(
            label = "Make your job confidential",
            required = False)

    def __init__(self, *args, **kwargs):
        log = logging.getLogger(__name__)
        log.debug("Entering function")

        request = kwargs.pop("request")

        grouped_contaminants = {}
        if kwargs.has_key("grouped_contaminants"):
            log.debug("List of contaminants is provided")
            grouped_contaminants = kwargs.pop("grouped_contaminants")

        super(UploadStructure, self).__init__(*args, **kwargs)

        self.helper = FormHelper()
        self.helper.layout = Layout(
                TabHolder(
                    Tab('File',
                        Field(
                            'job_name',
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

        if request.user.is_authenticated():
            self.helper.layout[0][0].append("confidential")
            self.fields['email'] = forms.EmailField(
                    initial = request.user.email,
                    required = True
                    )
        else:
            self.fields['email'] = forms.EmailField(
                    required = True
                    )

        for category in grouped_contaminants.keys():
            log.debug("Category found : " + str(category))

            initial = (category.selected_by_default)

            title = "<h3 onclick=\"toggle_all('" \
                    + text.slugify(category) + "')\">" \
                    + str(category) \
                    + " <button type=\"button\" class=\"btn btn-primary "\
                    + "btn-xs\">" \
                    + "Toggle all" \
                    + "</button></h3>"

            fields = []
            for contaminant in grouped_contaminants[category]:
                self.fields[contaminant.uniprot_ID] = forms.BooleanField(
                        label = contaminant.short_name + " - " +\
                                contaminant.long_name,
                        required = False,
                        initial = initial,
                        )
                fields.append(contaminant.uniprot_ID)
            self.helper.layout[0][1].append(Fieldset(title,*fields,
                css_class=text.slugify(category)))

        log.debug("Exiting function")
