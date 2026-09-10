from django.urls import path, reverse_lazy
from . import views

app_name = 'library'

urlpatterns = [
    # CRUD Album
    path('', views.AlbumListView.as_view(), name='album_list'),
    path('album/<int:pk>/', views.AlbumDetailView.as_view(), name='album_detail'),
    path('album/nuovo/', views.AlbumCreateView.as_view(), name='album_create'),
    path('album/<int:pk>/modifica/', views.AlbumUpdateView.as_view(), name='album_update'),
    path('album/<int:pk>/elimina/', views.AlbumDeleteView.as_view(), name='album_delete'),

    # Canzone (Traccia)
    path('canzone/<int:pk>/', views.CanzoneDetailView.as_view(), name='canzone_detail'),
    path('canzone/<int:pk>/modifica/', views.CanzoneUpdateView.as_view(), name='canzone_update'),

    # CRUD Artista
    path('artisti/', views.ArtistaListView.as_view(), name='artista_list'),
    path('artisti/<int:pk>/', views.ArtistaDetailView.as_view(), name='artista_detail'),
    path('artisti/nuovo/', views.ArtistaCreateView.as_view(), name='artista_create'),
    path('artisti/<int:pk>/modifica/', views.ArtistaUpdateView.as_view(), name='artista_update'),
    path('artisti/<int:pk>/elimina/', views.ArtistaDeleteView.as_view(), name='artista_delete'),
    path('artisti/<int:pk>/dettagli/', views.ArtistaMetadataView.as_view(), name='artista_metadata'),

    # MusicBrainz
    path('musicbrainz/', views.musicbrainz_search, name='musicbrainz_search'),
    path('musicbrainz/import/<str:mbid>/', views.musicbrainz_import, name='musicbrainz_import'),
    path('musicbrainz/preview/<str:mbid>/', views.musicbrainz_preview, name='musicbrainz_preview'),

    # TheAudioDB
    path('theaudiodb/', views.theaudiodb_search, name='theaudiodb_search'),
    path('theaudiodb/import/<str:artist_id>/', views.theaudiodb_import, name='theaudiodb_import'),

    # CSV Upload/Export
    path('csv-upload/', views.csv_upload, name='csv_upload'),
    path('csv-export/', views.csv_export, name='csv_export'),
    # API
    path('api/search-cover/', views.api_search_cover, name='api_search_cover'),
    path('api/rate/<str:item_type>/<int:item_id>/', views.api_rate_item, name='api_rate_item'),
    path('api/canzone/<int:pk>/save_lyrics/', views.api_save_lyrics, name='api_save_lyrics'),
    path('api/search/', views.api_global_search, name='api_search'),

    # Profilo, Ricerca & Auth
    path('cerca/', views.GlobalSearchView.as_view(), name='search'),
    path('registrazione/', views.RegisterView.as_view(), name='register'),
    path('profilo/', views.UserProfileView.as_view(), name='profile'),
    path('login/', views.LoginView.as_view(template_name='library/login.html'), name='login'),
    path('logout/', views.LogoutView.as_view(next_page='library:login'), name='logout'),
    path('cambia-password/', views.PasswordChangeView.as_view(template_name='library/profile.html', success_url=reverse_lazy('library:album_list')), name='password_change'),

    # Admin Users
    path('admin-users/', views.AdminUserListView.as_view(), name='admin_users'),
    path('admin-users/<int:pk>/elimina/', views.admin_user_delete, name='admin_user_delete'),
    path('admin-users/<int:pk>/password/', views.admin_user_change_password, name='admin_user_password'),
]
