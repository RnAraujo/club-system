from django import forms
from .models import Club, Directive, MissionaryDistrict


# ====================== CLUB ======================

class ClubForm(forms.ModelForm):
    class Meta:
        model = Club
        fields = ['district', 'name', 'zone']
        labels = {
            'district': 'Distrito Misionero',
            'name': 'Nombre del club',
            'zone': 'Zona',
        }
        help_texts = {
            'name': 'Debe ser único dentro del distrito seleccionado.',
            'zone': 'Número de zona (1, 2, 3, ...)',
        }
        widgets = {
            'district': forms.Select(attrs={'class': 'form-select'}),
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej.: Club Bethel',
                'autocomplete': 'off',
            }),
            'zone': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 1,
                'max': 99,
                'placeholder': 'Ej.: 1',
                'inputmode': 'numeric',
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['district'].empty_label = '— Selecciona un distrito —'
        self.fields['district'].queryset = MissionaryDistrict.objects.order_by('name')


# ====================== DIRECTIVA ======================

class DirectiveForm(forms.ModelForm):
    class Meta:
        model = Directive
        fields = ['club', 'first_name', 'last_name', 'position', 'phone', 'dni']
        labels = {
            'club': 'Club',
            'first_name': 'Nombres',
            'last_name': 'Apellidos',
            'position': 'Cargo',
            'phone': 'Celular',
            'dni': 'DNI',
        }
        help_texts = {
            'position': 'Un cargo solo puede estar ocupado por una persona por club.',
            'dni': 'Documento Nacional de Identidad (8 dígitos).',
            'phone': 'Opcional. Número de contacto.',
        }
        widgets = {
            'club': forms.Select(attrs={'class': 'form-select'}),
            'first_name': forms.TextInput(attrs={
                'class': 'form-control', 'placeholder': 'Ej.: Juan', 'autocomplete': 'off',
            }),
            'last_name': forms.TextInput(attrs={
                'class': 'form-control', 'placeholder': 'Ej.: Pérez', 'autocomplete': 'off',
            }),
            'position': forms.Select(attrs={'class': 'form-select'}),
            'phone': forms.TextInput(attrs={
                'class': 'form-control', 'placeholder': 'Ej.: 999888777', 'inputmode': 'tel',
            }),
            'dni': forms.TextInput(attrs={
                'class': 'form-control', 'placeholder': '8 dígitos',
                'maxlength': 8, 'inputmode': 'numeric', 'autocomplete': 'off',
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['club'].queryset = (
            Club.objects.select_related('district').order_by('district__name', 'zone', 'name')
        )


# ====================== DISTRITO ======================

class MissionaryDistrictForm(forms.ModelForm):
    class Meta:
        model = MissionaryDistrict
        fields = ['name']
        labels = {'name': 'Nombre del Distrito Misionero'}
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej.: Distrito Lima Norte',
                'autocomplete': 'off',
            }),
        }