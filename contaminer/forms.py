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

"""This module provides the forms for the ContaMiner application."""

import logging

from django import forms
from django.utils import text
from django.core.exceptions import ObjectDoesNotExist

from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Field, Fieldset
from crispy_forms.bootstrap import StrictButton, Tab, TabHolder

from .models.contabase import ContaBase
from .models.contabase import Category
from .models.contabase import Contaminant


class SubmitJobForm(forms.Form):
    """Upload a mtz or cif file and select contaminants to test."""

    name = forms.CharField(
            label="Job name",
            max_length=50,
            required=False)
    diffraction_data = forms.FileField()
    confidential = forms.BooleanField(
        label="Make your job confidential",
        required=False)

    custom_models = forms.FileField(
        widget=forms.ClearableFileInput(
            attrs={'multiple': True}),
        required=False)

    def __init__(self, *args, **kwargs):
        """Create a new form."""
        log = logging.getLogger(__name__)
        log.debug("Enter")

        # Pop user if given
        user = None
        if "user" in kwargs:
            user = kwargs.pop("user")

        super(SubmitJobForm, self).__init__(*args, **kwargs)

        self.helper = FormHelper()
        self.helper.layout = Layout(
            TabHolder(
                Tab('File',
                    Field(
                        'name',
                        'diffraction_data',
                        'email_address'
                    )),
                Tab('Contaminants',),
                Tab('Advanced',
                    Field(
                        'custom_models'
                    ),
                ),
            ),
            StrictButton(
                '<span class="ladda-label">Submit</span>',
                type="submit",
                css_class="btn btn-primary ladda-button submit_button",
                data_style="expand-right",
            )
        )

        # Add confidential button and pre-fill e-mail if user if logged in
        if user and user.is_authenticated():
            self.helper.layout[0][0].append("confidential")
            self.fields['email_address'] = forms.EmailField(
                initial=user.email,
                required=True)
        else:
            self.fields['email_address'] = forms.EmailField(
                required=True)

        # Add contaminants selection to form
        try:
            contabase = ContaBase.get_current()
            categories = Category.objects.filter(
                contabase=contabase)
        except ObjectDoesNotExist:
            categories = []

        for category in categories:
            log.debug("Category found : " + str(category))

            initial = (category.selected_by_default)

            title = "<h3 onclick=\"toggle_all('" \
                    + text.slugify(category) + "')\">" \
                    + category.name \
                    + " <button type=\"button\" class=\"btn btn-primary "\
                    + "btn-xs\">" \
                    + "Toggle all" \
                    + "</button></h3>"

            fields = []
            for contaminant in Contaminant.objects.filter(category=category):
                self.fields[contaminant.uniprot_id] = forms.BooleanField(
                    label=contaminant.short_name +" - "+ contaminant.long_name,
                    required=False,
                    initial=initial)
                fields.append(contaminant.uniprot_id)
            self.helper.layout[0][1].append(Fieldset(
                title,
                *fields,
                css_class=text.slugify(category)))

        log.debug("Exit")
