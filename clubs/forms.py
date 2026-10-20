from django import forms
from .models import Club, Directive


def _style(fields):
    for f in fields.values():
        f.widget.attrs['class'] = 'input'


class ClubForm(forms.ModelForm):
    class Meta:
        model = Club
        fields = ['name', 'zone']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        _style(self.fields)


class DirectiveForm(forms.ModelForm):
    class Meta:
        model = Directive
        fields = ['club', 'first_name', 'last_name', 'position', 'phone', 'dni']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        _style(self.fields)