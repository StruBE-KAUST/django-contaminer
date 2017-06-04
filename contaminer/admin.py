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

"""This module set what you see in the admin pages of Django."""

from django.contrib import admin

from .models.contabase import Category
from .models.contabase import Contaminant
from .models.contabase import Pack
from .models.contabase import Model
from .models.contabase import Reference
from .models.contabase import Suggestion
from .models.contaminer import Job
from .models.contaminer import Task

admin.site.register(Category)
admin.site.register(Contaminant)
admin.site.register(Pack)
admin.site.register(Model)

class JobAdmin(admin.ModelAdmin):
    readonly_fields = ("submission_date",)

admin.site.register(Job, JobAdmin)
admin.site.register(Task)
admin.site.register(Reference)
admin.site.register(Suggestion)
