import csv
import io
import re
import time
from datetime import timedelta
from urllib.parse import quote

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from django.contrib import messages
from django.db import transaction
from django.db.models import OuterRef, Subquery
from django.shortcuts import render, get_object_or_404, redirect
from django.core.files.base import ContentFile
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView, TemplateView
from django.urls import reverse, reverse_lazy
from django.http import JsonResponse, HttpResponse
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth.views import LoginView, LogoutView, PasswordChangeView
from django.contrib.auth import login
from django.contrib.auth.models import User
from PIL import Image

from .models import Artista, Album, Canzone, MetadatoCanzone, MetadatoArtista, UserProfile, VotoAlbum, VotoArtista, VotoCanzone
from .forms import (
    AlbumForm, 
    ArtistaForm, 
    MusicBrainzSearchForm, 
    TheAudioDBSearchForm,
    CSVUploadForm, 
    CanzoneFormSet,
    MetadatoCanzoneFormSet,
    CanzoneForm,
    UserProfileForm,
    UserRegistrationForm
)

# ---------------------------------------------------------------------------
# MusicBrainz — Configurazione HTTP con retry
# ---------------------------------------------------------------------------
MUSICBRAINZ_BASE = 'https://musicbrainz.org/ws/2'
COVERART_BASE = 'https://coverartarchive.org'
MB_HEADERS = {
    'User-Agent': 'MusicLibraryDjango/1.0 (music-library-app)',
    'Accept': 'application/json',
}


def _get_mb_session():
    """Crea una sessione requests con retry automatico per MusicBrainz."""
    session = requests.Session()
    retry_strategy = Retry(
        total=3,
        backoff_factor=1,
        status_forcelist=[429, 500, 502, 503, 504],
    )
    adapter = HTTPAdapter(max_retries=retry_strategy)
    session.mount('https://', adapter)
    session.mount('http://', adapter)
    session.headers.update(MB_HEADERS)
    return session


# ===========================================================================
# CRUD Album — Class-Based Views
# ===========================================================================

class AlbumListView(LoginRequiredMixin, ListView):
    model = Album
    template_name = 'library/album_list.html'
    context_object_name = 'albums'
    paginate_by = 25

    def get(self, request, *args, **kwargs):
        # Salviamo/aggiorniamo le preferenze correnti nella sessione
        if request.GET:
            prefs = {
                'sort': request.GET.get('sort', ''),
                'groupby': request.GET.get('groupby', ''),
                'f_anno': request.GET.get('f_anno', ''),
                'f_tipo': request.GET.get('f_tipo', ''),
                'f_formato': request.GET.get('f_formato', ''),
                'per_page': request.GET.get('per_page', ''),
            }
            # Rimuoviamo i valori vuoti
            prefs = {k: v for k, v in prefs.items() if v}
            request.session['album_list_prefs'] = prefs

        # Se non ci sono parametri GET, proviamo a caricare dalla sessione
        elif 'album_list_prefs' in request.session:
            prefs = request.session['album_list_prefs']
            if any(prefs.values()):
                from urllib.parse import urlencode
                return redirect(f"{request.path}?{urlencode(prefs)}")
            
        return super().get(request, *args, **kwargs)

    def get_paginate_by(self, queryset):
        try:
            return int(self.request.GET.get('per_page', self.paginate_by))
        except ValueError:
            return self.paginate_by

    def get_queryset(self):
        qs = super().get_queryset().filter(user=self.request.user)
        
        # Annotate user vote
        qs = qs.annotate(
            user_voto=Subquery(
                VotoAlbum.objects.filter(album=OuterRef('pk'), utente=self.request.user).values('punteggio')[:1]
            )
        )
        
        # Filtri
        f_anno = self.request.GET.get('f_anno')
        f_tipo = self.request.GET.get('f_tipo')
        f_formato = self.request.GET.get('f_formato')
        
        if f_anno:
            qs = qs.filter(anno_uscita=f_anno)
        if f_tipo:
            qs = qs.filter(tipo_release=f_tipo)
        if f_formato:
            if f_formato == 'none':
                qs = qs.filter(formato_fisico='')
            else:
                qs = qs.filter(formato_fisico=f_formato)
        
        # Ordinamento
        sort_by = self.request.GET.get('sort', '-anno_uscita')
        group_by_artist = self.request.GET.get('groupby') == 'artista'
        
        if group_by_artist:
            qs = qs.order_by('artista__nome', sort_by)
        elif sort_by in ('-anno_uscita', 'anno_uscita', 'titolo', 'artista__nome'):
            qs = qs.order_by(sort_by)
            
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['current_sort'] = self.request.GET.get('sort', '-anno_uscita')
        ctx['group_by_artist'] = self.request.GET.get('groupby') == 'artista'
        ctx['per_page'] = self.request.GET.get('per_page', str(self.paginate_by))
        
        # Passiamo i filtri attivi al contesto
        ctx['f_anno'] = self.request.GET.get('f_anno', '')
        ctx['f_tipo'] = self.request.GET.get('f_tipo', '')
        ctx['f_formato'] = self.request.GET.get('f_formato', '')
        
        # Anni disponibili per la select
        ctx['anni_disponibili'] = Album.objects.values_list('anno_uscita', flat=True).distinct().order_by('-anno_uscita')
        
        return ctx

def get_dominant_color(image_field):
    """Calcola il colore medio (dominante) da un ImageField usando Pillow."""
    if not image_field or not hasattr(image_field, 'path'):
        return None
    try:
        with Image.open(image_field.path) as img:
            # Converte in RGB e ridimensiona a 1x1 per ottenere il colore medio
            img = img.convert('RGB')
            img = img.resize((1, 1), resample=0)
            dominant_color = img.getpixel((0, 0))
            return f"{dominant_color[0]}, {dominant_color[1]}, {dominant_color[2]}"
    except Exception:
        return None

class AlbumDetailView(LoginRequiredMixin, DetailView):
    model = Album
    template_name = 'library/album_detail.html'
    context_object_name = 'album'

    def get_queryset(self):
        return super().get_queryset().filter(user=self.request.user)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['canzoni'] = self.object.canzoni.annotate(
            user_voto=Subquery(
                VotoCanzone.objects.filter(canzone=OuterRef('pk'), utente=self.request.user).values('punteggio')[:1]
            )
        )
        user_voto = self.object.voti.filter(utente=self.request.user).first()
        ctx['user_voto'] = user_voto.punteggio if user_voto else 0
        ctx['post_social'] = self.object.post_social.all()
        ctx['dominant_color'] = get_dominant_color(self.object.copertina)
        return ctx


class AlbumCreateView(LoginRequiredMixin, CreateView):
    model = Album
    form_class = AlbumForm
    template_name = 'library/album_form.html'
    success_url = reverse_lazy('library:album_list')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['page_title'] = 'Nuovo Album'
        if self.request.POST:
            ctx['canzoni_formset'] = CanzoneFormSet(self.request.POST)
        else:
            ctx['canzoni_formset'] = CanzoneFormSet()
        return ctx

    def form_valid(self, form):
        context = self.get_context_data()
        canzoni_formset = context['canzoni_formset']
        if canzoni_formset.is_valid():
            form.instance.user = self.request.user
            self.object = form.save()
            canzoni_formset.instance = self.object
            canzoni_formset.save()
            return redirect(self.success_url)
        else:
            return self.render_to_response(self.get_context_data(form=form))


class AlbumUpdateView(LoginRequiredMixin, UpdateView):
    model = Album
    form_class = AlbumForm
    template_name = 'library/album_form.html'
    success_url = reverse_lazy('library:album_list')

    def get_queryset(self):
        return super().get_queryset().filter(user=self.request.user)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['page_title'] = 'Modifica Album'
        if self.request.POST:
            ctx['canzoni_formset'] = CanzoneFormSet(self.request.POST, instance=self.object)
        else:
            ctx['canzoni_formset'] = CanzoneFormSet(instance=self.object)
        return ctx

    def form_valid(self, form):
        context = self.get_context_data()
        canzoni_formset = context['canzoni_formset']
        if canzoni_formset.is_valid():
            self.object = form.save()
            canzoni_formset.instance = self.object
            canzoni_formset.save()
            return redirect('library:album_detail', pk=self.object.pk)
        else:
            return self.render_to_response(self.get_context_data(form=form))


class AlbumDeleteView(LoginRequiredMixin, DeleteView):
    model = Album
    template_name = 'library/album_confirm_delete.html'
    success_url = reverse_lazy('library:album_list')

    def get_queryset(self):
        return super().get_queryset().filter(user=self.request.user)


# ===========================================================================
# CRUD Artista — Class-Based Views
# ===========================================================================

class ArtistaListView(LoginRequiredMixin, ListView):
    model = Artista
    template_name = 'library/artista_list.html'
    context_object_name = 'artisti'
    paginate_by = 25

    def get_paginate_by(self, queryset):
        try:
            return int(self.request.GET.get('per_page', self.paginate_by))
        except ValueError:
            return self.paginate_by

    def get_queryset(self):
        qs = super().get_queryset().filter(user=self.request.user)
        return qs.annotate(
            user_voto=Subquery(
                VotoArtista.objects.filter(artista=OuterRef('pk'), utente=self.request.user).values('punteggio')[:1]
            )
        ).order_by('nome')
        
    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['per_page'] = self.request.GET.get('per_page', str(self.paginate_by))
        return ctx


class ArtistaDetailView(LoginRequiredMixin, DetailView):
    model = Artista
    template_name = 'library/artista_detail.html'
    context_object_name = 'artista'

    def get_queryset(self):
        return super().get_queryset().filter(user=self.request.user)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['albums'] = self.object.album.all().annotate(
            user_voto=Subquery(
                VotoAlbum.objects.filter(album=OuterRef('pk'), utente=self.request.user).values('punteggio')[:1]
            )
        ).order_by('-anno_uscita')
        ctx['dominant_color'] = get_dominant_color(self.object.immagine_profilo)
        user_voto = self.object.voti.filter(utente=self.request.user).first()
        ctx['user_voto'] = user_voto.punteggio if user_voto else 0
        return ctx


class ArtistaMetadataView(LoginRequiredMixin, DetailView):
    model = Artista
    template_name = 'library/artista_metadata.html'
    context_object_name = 'artista'

    def get_queryset(self):
        return super().get_queryset().filter(user=self.request.user)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['metadati'] = self.object.metadati.all()
        return ctx


class ArtistaCreateView(LoginRequiredMixin, CreateView):
    model = Artista
    form_class = ArtistaForm
    template_name = 'library/artista_form.html'
    success_url = reverse_lazy('library:artista_list')

    def form_valid(self, form):
        form.instance.user = self.request.user
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['page_title'] = 'Nuovo Artista'
        return ctx


class ArtistaUpdateView(LoginRequiredMixin, UpdateView):
    model = Artista
    form_class = ArtistaForm
    template_name = 'library/artista_form.html'

    def get_queryset(self):
        return super().get_queryset().filter(user=self.request.user)
    success_url = reverse_lazy('library:artista_list')

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['page_title'] = 'Modifica Artista'
        return ctx


class ArtistaDeleteView(LoginRequiredMixin, DeleteView):
    model = Artista
    template_name = 'library/artista_confirm_delete.html'
    success_url = reverse_lazy('library:artista_list')

    def get_queryset(self):
        return super().get_queryset().filter(user=self.request.user)


# ===========================================================================
# MusicBrainz — Ricerca e importazione
# ===========================================================================

def musicbrainz_search(request):
    """Mostra form di ricerca e restituisce risultati da MusicBrainz."""
    form = MusicBrainzSearchForm(request.GET or None)
    results = []

    if form.is_valid():
        titolo = form.cleaned_data['titolo']
        session = _get_mb_session()
        try:
            resp = session.get(
                f'{MUSICBRAINZ_BASE}/release/',
                params={'query': f'release:{titolo}', 'fmt': 'json', 'limit': 20},
                timeout=30,
            )
            resp.raise_for_status()
            data = resp.json()
            for release in data.get('releases', []):
                artist_name = ''
                if release.get('artist-credit'):
                    artist_name = release['artist-credit'][0].get('name', 'Sconosciuto')
                    
                # Parsing della data più accurato
                anno_str = release.get('date', '')
                if not anno_str:
                    # Tenta con il release-group se la date è vuota (es. Love Yourself)
                    anno_str = release.get('release-group', {}).get('first-release-date', '')
                
                anno = anno_str[:4] if anno_str else 'N/D'

                results.append({
                    'mbid': release['id'],
                    'titolo': release.get('title', ''),
                    'artista': artist_name,
                    'anno': anno,
                    'country': release.get('country', ''),
                })
        except requests.RequestException as e:
            error_msg = f'Errore nella ricerca MusicBrainz: {e}'
            if request.GET.get('ajax') == '1':
                return JsonResponse({'error': error_msg}, status=503)
            messages.error(request, error_msg)

    if request.GET.get('ajax') == '1':
        return JsonResponse({'results': results})

    return render(request, 'library/musicbrainz_search.html', {
        'form': form,
        'results': results,
    })


def musicbrainz_preview(request, mbid):
    """API endpoint per recuperare asincronamente la tracklist di un album."""
    session = _get_mb_session()
    try:
        resp = session.get(
            f'{MUSICBRAINZ_BASE}/release/{mbid}',
            params={'inc': 'recordings', 'fmt': 'json'},
            timeout=10,
        )
        resp.raise_for_status()
        release = resp.json()
        
        tracks = []
        for medium in release.get('media', []):
            for track in medium.get('tracks', []):
                length_ms = track.get('length') or track.get('recording', {}).get('length')
                durata = "N/D"
                if length_ms:
                    s = int(length_ms) // 1000
                    durata = f"{s // 60:02d}:{s % 60:02d}"
                    
                tracks.append({
                    'position': track.get('position', ''),
                    'title': track.get('title', ''),
                    'duration': durata
                })
        
        return JsonResponse({'tracks': tracks})
    except requests.RequestException as e:
        return JsonResponse({'error': str(e)}, status=400)


@login_required
def musicbrainz_import(request, mbid):
    """Importa un album da MusicBrainz dato il suo MBID (release ID)."""
    is_ajax = request.GET.get('ajax') == '1'
    session = _get_mb_session()

    try:
        # 1. Recupera dettagli release
        resp = session.get(
            f'{MUSICBRAINZ_BASE}/release/{mbid}',
            params={'inc': 'recordings+artists+work-rels+artist-rels+recording-level-rels', 'fmt': 'json'},
            timeout=20,
        )
        resp.raise_for_status()
        release = resp.json()
    except requests.RequestException as e:
        if is_ajax:
            return JsonResponse({'error': f'Errore nel recupero dati MusicBrainz: {e}'}, status=503)
        messages.error(request, f'Errore nel recupero dati MusicBrainz: {e}')
        return redirect('library:musicbrainz_search')

    # 2. Crea o recupera artista
    artist_name = 'Sconosciuto'
    if release.get('artist-credit'):
        artist_name = release['artist-credit'][0].get('name', 'Sconosciuto')

    artista = Artista.objects.filter(nome__iexact=artist_name, user=request.user).first()
    if not artista:
        artista = Artista.objects.create(nome=artist_name, user=request.user)

    # 3. Anno di uscita
    anno_str = release.get('date', '')
    if not anno_str:
        anno_str = release.get('release-group', {}).get('first-release-date', '')
        
    anno = 2000
    if anno_str:
        try:
            anno = int(anno_str[:4])
        except (ValueError, IndexError):
            pass
            
    # 4. Crea album
    album = Album.objects.create(
        user=request.user,
        titolo=release.get('title', 'Senza titolo'),
        artista=artista,
        anno_uscita=anno,
    )

    # 5. Scarica copertina da Cover Art Archive con fallback
    time.sleep(1)
    try:
        cover_resp = session.get(
            f'{COVERART_BASE}/release/{mbid}/front',
            timeout=10,
            allow_redirects=True,
        )
        if cover_resp.status_code == 200:
            filename = f'{mbid}.jpg'
            album.copertina.save(filename, ContentFile(cover_resp.content), save=True)
        else:
            # Fallback al release-group
            rg_id = release.get('release-group', {}).get('id')
            if rg_id:
                time.sleep(1)
                cover_resp_rg = session.get(
                    f'{COVERART_BASE}/release-group/{rg_id}/front',
                    timeout=10,
                    allow_redirects=True,
                )
                if cover_resp_rg.status_code == 200:
                    filename = f'{rg_id}.jpg'
                    album.copertina.save(filename, ContentFile(cover_resp_rg.content), save=True)
    except requests.RequestException:
        pass  # Copertina non disponibile

    # 6. Crea le tracce
    for medium in release.get('media', []):
        for track in medium.get('tracks', []):
            length_ms = track.get('length') or track.get('recording', {}).get('length')
            durata = None
            if length_ms:
                durata = timedelta(milliseconds=int(length_ms))

            canzone = Canzone.objects.create(
                titolo=track.get('title', 'Senza titolo'),
                album=album,
                numero_traccia=track.get('position', 1),
                durata=durata,
            )
            
            # Estrai relazioni (produttori, compositori, ecc.)
            for rel in track.get('recording', {}).get('relations', []):
                rel_type = rel.get('type', '')
                target_name = rel.get('artist', {}).get('name') or rel.get('work', {}).get('title') or ''
                if rel_type and target_name:
                    MetadatoCanzone.objects.get_or_create(
                        canzone=canzone,
                        chiave=rel_type.capitalize(),
                        valore=target_name
                    )

    msg = f'Album "{album.titolo}" di {artista.nome} importato con successo! ({album.canzoni.count()} tracce)'
    
    if is_ajax:
        return JsonResponse({
            'success': True,
            'message': msg,
            'redirect_url': reverse('library:album_detail', kwargs={'pk': album.pk}),
        })

    messages.success(request, msg)
    return redirect('library:album_detail', pk=album.pk)


# ===========================================================================
# TheAudioDB - Ricerca e importazione artisti

def theaudiodb_search(request):
    """Mostra form di ricerca e restituisce risultati da TheAudioDB per gli artisti."""
    form = TheAudioDBSearchForm(request.GET or None)
    results = []

    if form.is_valid():
        nome = form.cleaned_data['nome']
        try:
            resp = requests.get(
                'https://www.theaudiodb.com/api/v1/json/2/search.php',
                params={'s': nome},
                timeout=10,
            )
            resp.raise_for_status()
            data = resp.json()
            
            artists = data.get('artists')
            if artists:
                for artist in artists[:5]:
                    results.append({
                        'id': artist.get('idArtist'),
                        'nome': artist.get('strArtist', ''),
                        'immagine': artist.get('strArtistThumb', ''),
                        'biografia': artist.get('strBiography', ''),
                        'genere': artist.get('strGenre', ''),
                        'nazione': artist.get('strCountry', ''),
                    })
        except requests.RequestException as e:
            error_msg = f'Errore nella ricerca TheAudioDB: {e}'
            if request.GET.get('ajax') == '1':
                return JsonResponse({'error': error_msg}, status=503)
            messages.error(request, error_msg)

    if request.GET.get('ajax') == '1':
        return JsonResponse({'results': results})

    return render(request, 'library/theaudiodb_search.html', {
        'form': form,
        'results': results,
    })

@login_required
def theaudiodb_import(request, artist_id):
    """Importa o aggiorna un artista da TheAudioDB dato il suo idArtist."""
    is_ajax = request.GET.get('ajax') == '1'

    try:
        resp = requests.get(
            'https://www.theaudiodb.com/api/v1/json/2/artist.php',
            params={'i': artist_id},
            timeout=10,
        )
        resp.raise_for_status()
        data = resp.json()
        
        artists = data.get('artists')
        if not artists:
            raise ValueError("Artista non trovato su TheAudioDB.")
        
        artist_data = artists[0]
        nome = artist_data.get('strArtistAlternate') or artist_data.get('strArtist', 'Sconosciuto')
        
        # Cerca artista esistente o crea nuovo
        artista = Artista.objects.filter(nome__iexact=nome, user=request.user).first()
        if not artista:
            artista = Artista.objects.create(nome=nome, user=request.user)
            
        # Aggiorna biografia
        biografia = artist_data.get('strBiography')
        if biografia:
            artista.biografia = biografia
            
        # Scarica immagine profilo
        immagine_url = artist_data.get('strArtistThumb')
        if immagine_url:
            img_resp = requests.get(immagine_url, timeout=10)
            if img_resp.status_code == 200:
                filename = f"{artist_id}.jpg"
                artista.immagine_profilo.save(filename, ContentFile(img_resp.content), save=False)
                
        artista.save()
        
        # Salva metadati aggiuntivi
        extra_fields = {
            'Sito Web': artist_data.get('strWebsite'),
            'Genere': artist_data.get('strGenre'),
            'Anno Formazione': artist_data.get('intFormedYear'),
            'Paese': artist_data.get('strCountry'),
            'Etichetta': artist_data.get('strLabel'),
            'Stile': artist_data.get('strStyle'),
            'Mood': artist_data.get('strMood'),
        }
        for chiave, valore in extra_fields.items():
            if valore and str(valore).strip() and str(valore).strip() != '0':
                MetadatoArtista.objects.update_or_create(
                    artista=artista,
                    chiave=chiave,
                    defaults={'valore': str(valore).strip()}
                )
        
        msg = f'Artista "{artista.nome}" importato/aggiornato con successo!'
        
        if is_ajax:
            return JsonResponse({
                'success': True,
                'message': msg,
                'redirect_url': reverse('library:artista_detail', kwargs={'pk': artista.pk}),
            })
            
        messages.success(request, msg)
        return redirect('library:artista_detail', pk=artista.pk)
        
    except (requests.RequestException, ValueError) as e:
        error_msg = f'Errore nel recupero dati TheAudioDB: {e}'
        if is_ajax:
            return JsonResponse({'error': error_msg}, status=503)
        messages.error(request, error_msg)
        return redirect('library:theaudiodb_search')




# ===========================================================================
# CSV Upload
# ===========================================================================

@login_required
def csv_upload(request):
    """Upload di un file CSV per importare album nel database."""
    form = CSVUploadForm()

    if request.method == 'POST':
        form = CSVUploadForm(request.POST, request.FILES)
        if form.is_valid():
            file_csv = request.FILES['file_csv']
            try:
                decoded = file_csv.read().decode('utf-8')
                reader = csv.DictReader(io.StringIO(decoded))

                count = 0
                errors = []
                for i, row in enumerate(reader, start=2):
                    try:
                        nome_artista = row.get('artista', '').strip()
                        if not nome_artista:
                            errors.append(f'Riga {i}: artista mancante.')
                            continue

                        titolo = row.get('titolo', '').strip()
                        if not titolo:
                            errors.append(f'Riga {i}: titolo mancante.')
                            continue

                        anno = row.get('anno_uscita', '').strip()
                        try:
                            anno = int(anno)
                        except (ValueError, TypeError):
                            errors.append(f'Riga {i}: anno_uscita non valido "{anno}".')
                            continue

                        artista = Artista.objects.filter(nome__iexact=nome_artista, user=request.user).first()
                        if not artista:
                            artista = Artista.objects.create(nome=nome_artista, user=request.user)

                        tipo = row.get('tipo_release', '').strip().lower()
                        if tipo not in ('album', 'concerto'):
                            tipo = 'album'

                        formato = row.get('formato_fisico', '').strip().lower()
                        formati_validi = ('cd', 'vinile', 'dvd', 'bluray')
                        if formato not in formati_validi:
                            formato = ''

                        album = Album.objects.create(
                            user=request.user,
                            titolo=titolo,
                            artista=artista,
                            anno_uscita=anno,
                            tipo_release=tipo,
                            formato_fisico=formato,
                        )
                        
                        canzoni_str = row.get('canzoni', '').strip()
                        if canzoni_str:
                            canzoni_list = [c.strip() for c in canzoni_str.split('|') if c.strip()]
                            for idx, c_titolo in enumerate(canzoni_list, start=1):
                                Canzone.objects.create(
                                    album=album,
                                    titolo=c_titolo,
                                    numero_traccia=idx
                                )
                        count += 1
                    except Exception as e:
                        errors.append(f'Riga {i}: {e}')

                if count:
                    messages.success(request, f'{count} album importati con successo!')
                if errors:
                    messages.warning(request, 'Alcuni errori: ' + ' | '.join(errors[:5]))

            except Exception as e:
                messages.error(request, f'Errore nella lettura del CSV: {e}')

    return render(request, 'library/csv_upload.html', {'form': form})

@login_required
def csv_export(request):
    """Esporta la libreria in CSV."""
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="libreria.csv"'
    
    writer = csv.writer(response)
    writer.writerow(['titolo', 'artista', 'anno_uscita', 'tipo_release', 'formato_fisico', 'canzoni'])
    
    for album in Album.objects.filter(user=request.user).order_by('artista__nome', 'titolo'):
        canzoni = album.canzoni.all().order_by('numero_traccia')
        canzoni_str = '|'.join([c.titolo for c in canzoni])
        writer.writerow([
            album.titolo,
            album.artista.nome,
            album.anno_uscita,
            album.tipo_release,
            album.formato_fisico,
            canzoni_str
        ])
    return response

class CanzoneDetailView(LoginRequiredMixin, DetailView):
    model = Canzone
    template_name = 'library/canzone_detail.html'
    context_object_name = 'canzone'

    def get_queryset(self):
        return super().get_queryset().filter(album__user=self.request.user)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        user_voto = self.object.voti.filter(utente=self.request.user).first()
        ctx['user_voto'] = user_voto.punteggio if user_voto else 0
        return ctx


class CanzoneUpdateView(LoginRequiredMixin, UpdateView):
    model = Canzone
    form_class = CanzoneForm
    template_name = 'library/canzone_form.html'

    def get_queryset(self):
        return super().get_queryset().filter(album__user=self.request.user)

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        if self.request.POST:
            data['metadati'] = MetadatoCanzoneFormSet(self.request.POST, instance=self.object)
        else:
            data['metadati'] = MetadatoCanzoneFormSet(instance=self.object)
        return data

    def form_valid(self, form):
        context = self.get_context_data()
        metadati = context['metadati']
        with transaction.atomic():
            self.object = form.save()
            if metadati.is_valid():
                metadati.instance = self.object
                metadati.save()
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('library:canzone_detail', kwargs={'pk': self.object.pk})


def api_search_cover(request):
    """
    Cerca una copertina su MusicBrainz.
    Richiede ?q=TitoloAlbum o ?q=NomeArtista e ?type=album|artista.
    """
    query = request.GET.get('q', '')
    artist = request.GET.get('artist', '')
    search_type = request.GET.get('type', 'album')
    
    if not query:
        return JsonResponse({'error': 'Query mancante'}, status=400)
        
    session = _get_mb_session()
    try:
        if search_type == 'album':
            mb_query = f"release:{quote(query)}"
            if artist and artist != '---------' and artist.lower() != 'sconosciuto':
                mb_query += f"%20AND%20artist:{quote(artist)}"
                
            mb_url = f"https://musicbrainz.org/ws/2/release/?query={mb_query}&fmt=json&limit=10"
            response = session.get(mb_url, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            urls = []
            
            for release in data.get('releases', []):
                if len(urls) >= 5:
                    break
                    
                rel_id = release['id']
                rg_id = release.get('release-group', {}).get('id')
                
                # Check CoverArtArchive
                found = False
                for entity_type, entity_id in [('release', rel_id), ('release-group', rg_id)]:
                    if not entity_id or found: continue
                    caa_url = f"http://coverartarchive.org/{entity_type}/{entity_id}/front"
                    # Fast check
                    try:
                        caa_resp = session.head(caa_url, allow_redirects=True, timeout=2)
                        if caa_resp.status_code == 200:
                            urls.append(caa_resp.url)
                            found = True
                    except Exception:
                        pass
            
            if urls:
                return JsonResponse({'urls': urls})
                
        elif search_type == 'artista':
            adb_url = 'https://www.theaudiodb.com/api/v1/json/2/search.php'
            response = requests.get(adb_url, params={'s': query}, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            urls = []
            if data.get('artists'):
                for artist in data['artists'][:5]:
                    img = artist.get('strArtistThumb')
                    if img and img not in urls:
                        urls.append(img)
                        
            if urls:
                return JsonResponse({'urls': urls})
                
        return JsonResponse({'error': 'Nessuna immagine trovata'}, status=404)
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


# ===========================================================================
# Profilo Utente & Autenticazione
# ===========================================================================

class UserProfileView(LoginRequiredMixin, UpdateView):
    model = UserProfile
    form_class = UserProfileForm
    template_name = 'library/profile.html'
    success_url = reverse_lazy('library:album_list')

    def get_object(self, queryset=None):
        profile, created = UserProfile.objects.get_or_create(user=self.request.user)
        return profile

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['page_title'] = 'Il mio Profilo'
        return ctx


# ===========================================================================
# Pannello di Gestione Utenti (Solo Admin)
# ===========================================================================

class AdminUserListView(UserPassesTestMixin, ListView):
    model = User
    template_name = 'library/admin_users.html'
    context_object_name = 'utenti'
    
    def test_func(self):
        return self.request.user.is_superuser

    def get_queryset(self):
        return User.objects.all().order_by('username')


@login_required
def admin_user_delete(request, pk):
    if not request.user.is_superuser:
        messages.error(request, "Non hai i permessi per eseguire questa azione.")
        return redirect('library:album_list')
        
    user_to_delete = get_object_or_404(User, pk=pk)
    if user_to_delete == request.user:
        messages.error(request, "Non puoi eliminare il tuo stesso account.")
    else:
        user_to_delete.delete()
        messages.success(request, f"Utente {user_to_delete.username} eliminato con successo.")
        
    return redirect('library:admin_users')


@login_required
def admin_user_change_password(request, pk):
    if not request.user.is_superuser:
        messages.error(request, "Non hai i permessi per eseguire questa azione.")
        return redirect('library:album_list')
        
    user_to_change = get_object_or_404(User, pk=pk)
    
    if request.method == 'POST':
        new_password = request.POST.get('new_password')
        if new_password:
            error = None
            if len(new_password) < 8:
                error = "La password deve contenere almeno 8 caratteri."
            elif not re.search(r'\d', new_password):
                error = "La password deve contenere almeno un numero."
            elif not re.search(r'[^A-Za-z0-9\s]', new_password):
                error = "La password deve contenere almeno un simbolo."
                
            if error:
                return render(request, 'library/admin_password_change.html', {
                    'utente': user_to_change,
                    'page_title': f'Cambia Password per {user_to_change.username}',
                    'error': error
                })
                
            user_to_change.set_password(new_password)
            user_to_change.save()
            messages.success(request, f"Password per {user_to_change.username} aggiornata con successo.")
            return redirect('library:admin_users')
        else:
            messages.error(request, "La password non può essere vuota.")
            
    return render(request, 'library/admin_password_change.html', {
        'utente': user_to_change,
        'page_title': f'Cambia Password per {user_to_change.username}'
    })


class RegisterView(CreateView):
    template_name = 'library/register.html'
    form_class = UserRegistrationForm
    success_url = reverse_lazy('library:album_list')

    def form_valid(self, form):
        response = super().form_valid(form)
        user = form.instance
        login(self.request, user, backend='library.backends.EmailOrUsernameModelBackend')
        
        # Create UserProfile to ensure avatar/gravatar can be accessed
        UserProfile.objects.get_or_create(user=user)
        
        messages.success(self.request, f"Benvenuto {user.username}! Il tuo account è stato creato.")
        return response

@login_required
def api_rate_item(request, item_type, item_id):
    if request.method == 'POST':
        try:
            import json
            data = json.loads(request.body)
            punteggio = float(data.get('punteggio', 0))
            if not (0.5 <= punteggio <= 5.0):
                return JsonResponse({'error': 'Punteggio non valido'}, status=400)
            
            if item_type == 'album':
                album = get_object_or_404(Album, pk=item_id)
                voto, created = VotoAlbum.objects.update_or_create(
                    utente=request.user,
                    album=album,
                    defaults={'punteggio': punteggio}
                )
            elif item_type == 'artista':
                artista = get_object_or_404(Artista, pk=item_id)
                voto, created = VotoArtista.objects.update_or_create(
                    utente=request.user,
                    artista=artista,
                    defaults={'punteggio': punteggio}
                )
            elif item_type == 'canzone':
                canzone = get_object_or_404(Canzone, pk=item_id)
                voto, created = VotoCanzone.objects.update_or_create(
                    utente=request.user,
                    canzone=canzone,
                    defaults={'punteggio': punteggio}
                )
            else:
                return JsonResponse({'error': 'Tipo non valido'}, status=400)
                
            return JsonResponse({'success': True, 'punteggio': punteggio})
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    return JsonResponse({'error': 'Metodo non consentito'}, status=405)

@login_required
def api_save_lyrics(request, pk):
    if request.method == 'POST':
        try:
            import json
            data = json.loads(request.body)
            testo = data.get('testo', '').strip()
            
            canzone = get_object_or_404(Canzone, pk=pk)
            # Ensure the user owns the song's album
            if canzone.album.user != request.user:
                return JsonResponse({'error': 'Non autorizzato'}, status=403)
                
            canzone.testo = testo
            canzone.save()
            return JsonResponse({'success': True})
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    return JsonResponse({'error': 'Metodo non consentito'}, status=405)

# ===========================================================================
# Ricerca Globale
# ===========================================================================

class GlobalSearchView(LoginRequiredMixin, TemplateView):
    template_name = 'library/search.html'

@login_required
def api_global_search(request):
    query = request.GET.get('q', '').strip()
    if not query:
        return JsonResponse({'artisti': [], 'album': [], 'canzoni': []})
        
    # Search Artisti
    artisti_qs = Artista.objects.filter(user=request.user, nome__icontains=query)[:5]
    artisti_data = []
    for a in artisti_qs:
        artisti_data.append({
            'id': a.pk,
            'nome': a.nome,
            'url': reverse('library:artista_detail', args=[a.pk]),
            'image_url': a.immagine_profilo.url if a.immagine_profilo else ''
        })
        
    # Search Album
    album_qs = Album.objects.filter(user=request.user, titolo__icontains=query)[:5]
    album_data = []
    for al in album_qs:
        album_data.append({
            'id': al.pk,
            'titolo': al.titolo,
            'artista': al.artista.nome,
            'url': reverse('library:album_detail', args=[al.pk]),
            'image_url': al.copertina.url if al.copertina else ''
        })
        
    # Search Canzoni
    from django.db.models import Q
    
    # 1. Trova per titolo
    canzoni_titolo_qs = Canzone.objects.filter(
        album__user=request.user, titolo__icontains=query
    )[:10]
    
    # 2. Trova per testo (escludendo quelle già trovate per titolo)
    canzoni_testo_qs = Canzone.objects.filter(
        album__user=request.user, testo__icontains=query
    ).exclude(id__in=canzoni_titolo_qs.values_list('id', flat=True))[:10]
    
    def get_snippet(text, q, context=40):
        if not text: return ""
        idx = text.lower().find(q.lower())
        if idx == -1: return ""
        start = max(0, idx - context)
        end = min(len(text), idx + len(q) + context)
        prefix = "..." if start > 0 else ""
        suffix = "..." if end < len(text) else ""
        return prefix + text[start:end].replace('\n', ' ').strip() + suffix

    canzoni_data = []
    for c in canzoni_titolo_qs:
        canzoni_data.append({
            'id': c.pk,
            'titolo': c.titolo,
            'album': c.album.titolo,
            'artista': c.album.artista.nome,
            'url': reverse('library:canzone_detail', args=[c.pk]),
            'snippet': '', # per la ricerca tramite titolo lo snippet non serve in genere, o può essere vuoto
            'image_url': c.album.copertina.url if c.album.copertina else ''
        })
        
    canzoni_testo_data = []
    for c in canzoni_testo_qs:
        canzoni_testo_data.append({
            'id': c.pk,
            'titolo': c.titolo,
            'album': c.album.titolo,
            'artista': c.album.artista.nome,
            'url': reverse('library:canzone_detail', args=[c.pk]),
            'snippet': get_snippet(c.testo, query),
            'image_url': c.album.copertina.url if c.album.copertina else ''
        })
        
    return JsonResponse({
        'artisti': artisti_data,
        'album': album_data,
        'canzoni': canzoni_data,
        'canzoni_testo': canzoni_testo_data
    })
