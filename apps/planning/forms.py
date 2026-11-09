"""Formulare mit serverseitiger Validierung für Vorlagen, Qualifikationen und Urlaub."""

from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password

from .models import Employee, Qualification, ShiftTemplate, Vacation


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


class EmployeeForm(forms.Form):
    """Mitarbeitende anlegen oder bearbeiten (REQ-02, ABW-02).

    Beim Anlegen sind alle Felder außer den Qualifikationen Pflicht, inklusive
    Startpasswort. Beim Bearbeiten bleibt das Passwort leer, wenn es nicht geändert wird.
    """

    first_name = forms.CharField(label='Vorname', max_length=150)
    last_name = forms.CharField(label='Nachname', max_length=150)
    email = forms.EmailField(label='E-Mail (Anmeldename)')
    contract_type = forms.ChoiceField(
        label='Vertragsart', choices=[('', '– bitte wählen –'), *Employee.CONTRACT_TYPES]
    )
    weekly_hours = forms.DecimalField(
        label='Wochenstunden', min_value=1, max_value=48, max_digits=4, decimal_places=1
    )
    qualifications = forms.ModelMultipleChoiceField(
        label='Qualifikationen',
        queryset=Qualification.objects.order_by('pk'),
        required=False,
        widget=forms.CheckboxSelectMultiple,
    )
    password = forms.CharField(
        label='Startpasswort', widget=forms.PasswordInput(render_value=False), required=False
    )

    def __init__(self, *args, employee=None, **kwargs):
        """Initialisiert das Formular.

        Args:
            *args: Positionsargumente für ``forms.Form`` (z. B. POST-Daten).
            employee: Bestehende Person beim Bearbeiten, sonst ``None``.
            **kwargs: Weitere Argumente für ``forms.Form``.
        """
        self.employee = employee
        if employee and 'initial' not in kwargs:
            kwargs['initial'] = dict(
                first_name=employee.user.first_name,
                last_name=employee.user.last_name,
                email=employee.user.email,
                contract_type=employee.contract_type,
                weekly_hours=employee.weekly_hours,
                qualifications=list(employee.qualifications.all()),
            )
        super().__init__(*args, **kwargs)
        if employee is None:
            self.fields['password'].required = True

    def clean_email(self):
        """Prüft, dass die E-Mail-Adresse noch keinem anderen Konto gehört.

        Returns:
            E-Mail in Kleinbuchstaben.

        Raises:
            ValidationError: Wenn die Adresse bereits vergeben ist.
        """
        email = self.cleaned_data['email'].lower()
        others = User.objects.filter(username__iexact=email)
        if self.employee:
            others = others.exclude(pk=self.employee.user_id)
        if others.exists():
            raise forms.ValidationError('Diese E-Mail-Adresse ist bereits vergeben.')
        return email

    def clean_password(self):
        """Prüft das Passwort mit den Django-Passwortregeln, sofern eines angegeben ist.

        Returns:
            Passwort oder leere Zeichenkette.
        """
        password = self.cleaned_data.get('password', '')
        if password:
            validate_password(password)
        return password

    def missing_fields(self):
        """Nennt die Bezeichnungen aller fehlenden Pflichtfelder (REQ-02 AK 2).

        Returns:
            Liste der Feldbezeichnungen mit dem Fehler „required“.
        """
        return [
            self.fields[name].label
            for name, errors in self.errors.as_data().items()
            if name in self.fields and any(e.code == 'required' for e in errors)
        ]
