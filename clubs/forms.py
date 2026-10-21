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

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user

        if user and not user.is_admin:
            if user.club_id:
                # Registrador: el club se fija y NO se puede modificar
                self.fields['club'].queryset = Club.objects.filter(pk=user.club_id)
                self.fields['club'].initial = user.club_id
                self.fields['club'].disabled = True   # 👈 CLAVE
            else:
                # Registrador sin club: no puede crear directiva
                self.fields['club'].queryset = Club.objects.none()
                self.fields['club'].disabled = True
        else:
            # Admin: puede elegir cualquier club
            self.fields['club'].queryset = (
                Club.objects.select_related('district')
                .order_by('district__name', 'zone', 'name')
            )

    def clean_club(self):
        """Defensa final: si el usuario no es admin, siempre devuelve su club."""
        if self.user and not self.user.is_admin and self.user.club_id:
            return self.user.club
        return self.cleaned_data.get('club')

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