from django import forms
from .models import Qualification, ShiftTemplate, Vacation


class TemplateForm(forms.ModelForm):
    class Meta:
        model = ShiftTemplate
        fields = ['name', 'start', 'end', 'description']
        widgets = {'start': forms.TimeInput(format='%H:%M', attrs={'type': 'time'}),
                   'end': forms.TimeInput(format='%H:%M', attrs={'type': 'time'})}

    def clean(self):
        data = super().clean()
        if data.get('start') and data.get('end') and data['end'] <= data['start']:
            raise forms.ValidationError('Das Ende muss nach dem Beginn liegen. Nachtvorlagen folgen später.')
        return data


class QualificationForm(forms.ModelForm):
    class Meta:
        model = Qualification
        fields = ['name', 'description']


class VacationForm(forms.ModelForm):
    class Meta:
        model = Vacation
        fields = ['employee', 'start', 'end']
        labels = {'employee': 'Mitarbeitende'}
        widgets = {'start': forms.DateInput(attrs={'type': 'date'}),
                   'end': forms.DateInput(attrs={'type': 'date'})}

    def clean(self):
        data = super().clean()
        if data.get('start') and data.get('end') and data['end'] < data['start']:
            raise forms.ValidationError('Das Urlaubsende darf nicht vor dem Beginn liegen.')
        return data
