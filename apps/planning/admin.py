from django.contrib import admin
from .models import Employee, Qualification, ShiftTemplate, Vacation


@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):
    list_display = ['user']
    filter_horizontal = ['qualifications']


admin.site.register([Qualification, ShiftTemplate, Vacation])
