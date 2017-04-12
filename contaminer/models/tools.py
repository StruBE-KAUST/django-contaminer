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
Additional fields for ContaBase and ContaMiner.

This module provides various custom models used in ContaBase and ContaMiner
models.
"""

from django.db import models
from django.core.exceptions import ValidationError

class UpperCaseCharField(models.CharField):
    """CharField limited to UpperCase characters."""

    description = "Upper case string"

    def __init__(self, *args, **kwargs):
        """Create a new UpperCaseCharField."""
        super(UpperCaseCharField, self).__init__(*args, **kwargs)

    def pre_save(self, model_instance, add):
        """Set the value in UPPERCASE before saving."""
        value = super(UpperCaseCharField, self).pre_save(model_instance, add)
        return value.upper()


class PercentageField(models.IntegerField):
    """IntegerField limited to 0 to 100."""

    description = "An integer between 0 and 100"

    def __init__(self, *args, **kwargs):
        """Create a new PercentageField."""
        super(PercentageField, self).__init__(*args, **kwargs)

    def pre_save(self, model_instance, add):
        """Check the validity of the field before saving."""
        value = super(PercentageField, self).pre_save(model_instance, add)
        if (value < 0 or value > 100) and value is not None:
            raise ValidationError("Invalid percentage: " + str(value))
        return value
