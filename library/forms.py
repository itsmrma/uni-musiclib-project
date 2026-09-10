import requests
from django import forms
from django.core.files.base import ContentFile
from urllib.parse import urlparse
import os

from .models import Album, Artista, Canzone, MetadatoCanzone


def download_image_from_url(url):
    """Scarica un'immagine da un URL e restituisce un ContentFile e il nome file."""
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        
        # Cerca di indovinare l'estensione o usa .jpg come fallback
        parsed_url = urlparse(url)
        ext = os.path.splitext(parsed_url.path)[1]
        if not ext:
            ext = '.jpg'
            
        # Genera un nome file base
        filename = f"downloaded_image{ext}"
        return ContentFile(response.content), filename
    except requests.RequestException:
        return None, None


class ArtistaForm(forms.ModelForm):
    """Form per creare e modificare un Artista."""
    
    immagine_url = forms.URLField(
        required=False,
        label="Oppure incolla URL immagine",
        widget=forms.URLInput(attrs={
            'class': 'form-input',
            'placeholder': 'https://esempio.com/foto.jpg',
        })
    )

    class Meta:
        model = Artista
        fields = ['nome', 'biografia', 'immagine_profilo']
        widgets = {
            'nome': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'Nome artista',
            }),
            'biografia': forms.Textarea(attrs={
                'class': 'form-input',
                'placeholder': 'Biografia (opzionale)',
                'rows': 4,
            }),
            'immagine_profilo': forms.ClearableFileInput(attrs={
                'class': 'form-input',
            }),
        }

    def save(self, commit=True):
        instance = super().save(commit=False)
        immagine_url = self.cleaned_data.get('immagine_url')
        
        # Se c'è un URL ma NON è stato caricato un file manualmente
        if immagine_url and not self.cleaned_data.get('immagine_profilo'):
            content_file, filename = download_image_from_url(immagine_url)
            if content_file:
                instance.immagine_profilo.save(filename, content_file, save=False)
                
        if commit:
            instance.save()
        return instance


class AlbumForm(forms.ModelForm):
    """Form per creare e modificare un Album."""
    
    immagine_url = forms.URLField(
        required=False,
        label="Oppure incolla URL copertina",
        widget=forms.URLInput(attrs={
            'class': 'form-input',
            'placeholder': 'https://esempio.com/copertina.jpg',
        })
    )

    class Meta:
        model = Album
        fields = [
            'titolo',
            'artista',
            'anno_uscita',
            'copertina',
            'tipo_release',
            'formato_fisico',
            'digitale_acquistato',
        ]
        widgets = {
            'titolo': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'Titolo album',
            }),
            'artista': forms.Select(attrs={
                'class': 'form-input',
            }),
            'anno_uscita': forms.NumberInput(attrs={
                'class': 'form-input',
                'placeholder': 'Es. 2024',
                'min': 1900,
                'max': 2100,
            }),
            'copertina': forms.ClearableFileInput(attrs={
                'class': 'form-input',
            }),
            'tipo_release': forms.RadioSelect(attrs={
                'class': 'form-radio',
                'id': 'id_tipo_release',
            }),
            'formato_fisico': forms.Select(attrs={
                'class': 'form-input',
                'id': 'id_formato_fisico',
            }),
            'digitale_acquistato': forms.CheckboxInput(attrs={
                'class': 'form-checkbox',
            }),
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        if user:
            self.fields['artista'].queryset = Artista.objects.filter(user=user)

    def save(self, commit=True):
        instance = super().save(commit=False)
        immagine_url = self.cleaned_data.get('immagine_url')
        
        # Se c'è un URL ma l'utente NON ha caricato un nuovo file
        if immagine_url and 'copertina' not in self.changed_data:
            content_file, filename = download_image_from_url(immagine_url)
            if content_file:
                if instance.copertina:
                    instance.copertina.delete(save=False)
                instance.copertina.save(filename, content_file, save=False)
                
        if commit:
            instance.save()
        return instance


class CanzoneForm(forms.ModelForm):
    """Form per modificare le singole canzoni nell'inline formset."""
    class Meta:
        model = Canzone
        fields = ['numero_traccia', 'titolo', 'durata']
        widgets = {
            'numero_traccia': forms.NumberInput(attrs={'class': 'form-input', 'style': 'width: 70px;'}),
            'titolo': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Titolo traccia'}),
            'durata': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'MM:SS', 'style': 'width: 100px;'}),
        }
        
    def clean_durata(self):
        durata_str = self.cleaned_data.get('durata')
        if not durata_str:
            return None
        # Django DurationField si aspetta timedelta o stringhe come "HH:MM:SS"
        # Se l'utente inserisce "03:45" (MM:SS), dobbiamo convertirlo
        import datetime
        from django.core.exceptions import ValidationError
        
        if isinstance(durata_str, datetime.timedelta):
            return durata_str
            
        durata_str = str(durata_str).strip()
        parts = durata_str.split(':')
        try:
            if len(parts) == 2:  # MM:SS
                m, s = map(int, parts)
                return datetime.timedelta(minutes=m, seconds=s)
            elif len(parts) == 3:  # HH:MM:SS
                h, m, s = map(int, parts)
                return datetime.timedelta(hours=h, minutes=m, seconds=s)
        except ValueError:
            raise ValidationError("Formato non valido. Usa MM:SS o HH:MM:SS")
            
        return durata_str


# Creazione del formset per le canzoni
CanzoneFormSet = forms.inlineformset_factory(
    Album,
    Canzone,
    form=CanzoneForm,
    extra=1,
    can_delete=True
)

MetadatoCanzoneFormSet = forms.inlineformset_factory(
    Canzone, MetadatoCanzone, 
    fields=['chiave', 'valore'], 
    extra=1, 
    can_delete=True,
    widgets={
        'chiave': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'es. Compositore'}),
        'valore': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'es. Hans Zimmer'}),
    }
)

from .models import MetadatoArtista

MetadatoArtistaFormSet = forms.inlineformset_factory(
    Artista, MetadatoArtista, 
    fields=['chiave', 'valore'], 
    extra=1, 
    can_delete=True,
    widgets={
        'chiave': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'es. Ruolo'}),
        'valore': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'es. Cantante'}),
    }
)

class MusicBrainzSearchForm(forms.Form):
    """Form per cercare un album su MusicBrainz."""
    titolo = forms.CharField(
        max_length=255,
        widget=forms.TextInput(attrs={
            'class': 'form-input',
            'placeholder': 'Cerca un album su MusicBrainz...',
            'autofocus': True,
        }),
        label='Titolo Album',
    )


class TheAudioDBSearchForm(forms.Form):
    """Form per cercare un artista su TheAudioDB."""
    nome = forms.CharField(
        max_length=255,
        widget=forms.TextInput(attrs={
            'class': 'form-input',
            'placeholder': 'Cerca un artista su TheAudioDB...',
            'autofocus': True,
        }),
        label='Nome Artista',
    )


class CSVUploadForm(forms.Form):
    """Form per l'upload di un file CSV contenente album."""
    file_csv = forms.FileField(
        widget=forms.ClearableFileInput(attrs={
            'class': 'form-input',
            'accept': '.csv',
        }),
        label='File CSV',
    )


class UserProfileForm(forms.ModelForm):
    """Form per aggiornare l'avatar e l'email dell'utente."""
    
    email = forms.EmailField(
        required=False,
        label="Indirizzo Email",
        widget=forms.EmailInput(attrs={
            'class': 'form-input',
            'placeholder': 'La tua email per Gravatar',
        }),
        help_text="Usato anche per recuperare l'immagine da Gravatar e per il login."
    )
    
    avatar_url_input = forms.URLField(
        required=False,
        label="Oppure incolla URL immagine",
        widget=forms.URLInput(attrs={
            'class': 'form-input',
            'placeholder': 'https://esempio.com/avatar.jpg',
        })
    )

    class Meta:
        from .models import UserProfile
        model = UserProfile
        fields = ['avatar']
        widgets = {
            'avatar': forms.ClearableFileInput(attrs={
                'class': 'form-input',
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.user:
            self.fields['email'].initial = self.instance.user.email

    def save(self, commit=True):
        instance = super().save(commit=False)
        avatar_url_input = self.cleaned_data.get('avatar_url_input')
        
        # 1. Update user email
        new_email = self.cleaned_data.get('email')
        if new_email is not None and instance.user:
            instance.user.email = new_email
            if commit:
                instance.user.save()
        
        # 2. Check manual image URL upload
        if avatar_url_input and 'avatar' not in self.changed_data:
            content_file, filename = download_image_from_url(avatar_url_input)
            if content_file:
                if instance.avatar:
                    instance.avatar.delete(save=False)
                instance.avatar.save(filename, content_file, save=False)
                instance.avatar_url = avatar_url_input
                
        # 3. Check Gravatar
        if commit:
            instance.save()
            # If no manual avatar or avatar_url, we rely on the `get_avatar_url` method in model/template to use gravatar
        return instance


import re
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm

class UserRegistrationForm(UserCreationForm):
    email = forms.EmailField(
        required=False,
        label="Indirizzo Email",
        help_text="Opzionale. Usato per recuperare l'immagine da Gravatar e per il login.",
        widget=forms.EmailInput(attrs={
            'class': 'form-input',
            'placeholder': 'La tua email',
        })
    )

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ("username", "email")
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs['class'] = 'form-input'
        self.fields['password1'].help_text = ''
        self.fields['password2'].label = 'Conferma Password'
        self.fields['password2'].help_text = 'Inserisci nuovamente la password per conferma.'
        self.error_messages['password_mismatch'] = 'Le due password inserite non coincidono.'

    def clean_password1(self):
        password = self.cleaned_data.get('password1')
        errors = []
        if not password or len(password) < 8:
            errors.append("La password deve contenere almeno 8 caratteri.")
        if not password or not re.search(r'\d', password):
            errors.append("La password deve contenere almeno un numero.")
        if not password or not re.search(r'[^a-zA-Z0-9\s]', password):
            errors.append("La password deve contenere almeno un simbolo.")
        if errors:
            raise forms.ValidationError(errors)
        return password

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if email:
            if not re.match(r'^[^@\s]+@[^@\s]+\.[^@\s]+$', email):
                raise forms.ValidationError("Inserisci un indirizzo email valido.")
        return email

    def validate_password_for_user(self, user, password_field_name="password2"):
        # I requisiti di password (almeno 8 caratteri, un numero e un simbolo)
        # sono gestiti esplicitamente in clean_password1.
        pass
