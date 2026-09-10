from django.contrib import admin
from .models import Artista, Album, Canzone, VotoAlbum, VotoArtista, VotoCanzone

class CanzoneInline(admin.TabularInline):
    model = Canzone
    extra = 1


@admin.register(Artista)
class ArtistaAdmin(admin.ModelAdmin):
    list_display = ('nome',)
    search_fields = ('nome',)


@admin.register(Album)
class AlbumAdmin(admin.ModelAdmin):
    list_display = ('titolo', 'artista', 'anno_uscita', 'tipo_release', 'formato_fisico')
    list_filter = ('anno_uscita', 'tipo_release', 'formato_fisico')
    search_fields = ('titolo', 'artista__nome')
    inlines = [CanzoneInline]


@admin.register(Canzone)
class CanzoneAdmin(admin.ModelAdmin):
    list_display = ('titolo', 'album', 'numero_traccia', 'durata')
    list_filter = ('album',)
    search_fields = ('titolo',)


@admin.register(VotoAlbum)
class VotoAlbumAdmin(admin.ModelAdmin):
    list_display = ('utente', 'album', 'punteggio')
    list_filter = ('punteggio',)

@admin.register(VotoArtista)
class VotoArtistaAdmin(admin.ModelAdmin):
    list_display = ('utente', 'artista', 'punteggio')
    list_filter = ('punteggio',)

@admin.register(VotoCanzone)
class VotoCanzoneAdmin(admin.ModelAdmin):
    list_display = ('utente', 'canzone', 'punteggio')
    list_filter = ('punteggio',)

