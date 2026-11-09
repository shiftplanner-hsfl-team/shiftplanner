"""Formulare mit serverseitiger Validierung für Vorlagen, Qualifikationen und Urlaub."""

from django import forms

from .models import Qualification, ShiftTemplate, Vacation


class DeadlineForm(forms.Form):
    """Abgabefrist eines Planungszeitraums festlegen (REQ-05)."""

    deadline = forms.DateField(
        label='Abgabefrist', widget=forms.DateInput(attrs={'type': 'date'}, format='%Y-%m-%d')
    )


class TemplateForm(forms.ModelForm):
    """Schichtvorlage anlegen oder ändern (REQ-03)."""

    class Meta:
        model = ShiftTemplate
        fields = ['name', 'start', 'end', 'description']
        widgets = {
            'start': forms.TimeInput(format='%H:%M', attrs={'type': 'time'}),
            'end': forms.TimeInput(format='%H:%M', attrs={'type': 'time'}),
        }

    def clean(self):
        """Prüft, dass das Ende nach dem Beginn liegt (REQ-03 AK 2).

        Returns:
            Bereinigte Formulardaten.

        Raises:
            ValidationError: Wenn das Ende nicht nach dem Beginn liegt.
        """
        data = super().clean()
        if data.get('start') and data.get('end') and data['end'] <= data['start']:
            raise forms.ValidationError(
                'Das Ende muss nach dem Beginn liegen. Nachtvorlagen folgen später.'
            )
        return data


class QualificationForm(forms.ModelForm):
    """Qualifikation anlegen oder ändern (REQ-02)."""

    class Meta:
        model = Qualification
        fields = ['name', 'description']


class VacationForm(forms.ModelForm):
    """Urlaub einer Person durch die Planung erfassen (REQ-14)."""

    class Meta:
        model = Vacation
        fields = ['employee', 'start', 'end']
        labels = {'employee': 'Mitarbeitende'}
        widgets = {
            'start': forms.DateInput(attrs={'type': 'date'}),
            'end': forms.DateInput(attrs={'type': 'date'}),
        }

    def clean(self):
        """Prüft, dass das Urlaubsende nicht vor dem Beginn liegt.

        Returns:
            Bereinigte Formulardaten.

        Raises:
            ValidationError: Wenn das Ende vor dem Beginn liegt.
        """
        data = super().clean()
        if data.get('start') and data.get('end') and data['end'] < data['start']:
            raise forms.ValidationError('Das Urlaubsende darf nicht vor dem Beginn liegen.')
        return data
