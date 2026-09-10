from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator


class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    avatar = models.ImageField(upload_to='utenti/avatar/', blank=True, null=True)
    avatar_url = models.URLField(blank=True, default='')

    def __str__(self):
        return f"Profilo di {self.user.username}"

    def get_avatar_url(self):
        if self.avatar:
            return self.avatar.url
        if self.avatar_url:
            return self.avatar_url
            
        # Fallback a Gravatar
        if self.user and self.user.email:
            import hashlib
            import urllib.parse
            email = self.user.email.strip().lower().encode('utf-8')
            hash_email = hashlib.md5(email).hexdigest()
            # d=404 causes gravatar to return 404 if no image exists, but we want a default icon if not found
            # Actually, standard behavior is to pass d=mp for a default avatar, but user said "se c'è ovviamente".
            # We can use d=mp so we always get an image, or we can use d=404. Let's use d=mp to have a nice fallback or 404 if we want to handle it in template.
            # I will use d=mp to just show the mystery person if they don't have gravatar.
            # But the user said "se mette l'email, va a prendere la foto profilo da gravatar (se c'è ovviamente)". 
            # I'll return the gravatar URL with d=identicon or d=mp. Wait, if it doesn't exist, we can use d=404 and in the template handle it? 
            # No, if d=404, the image tag will break. Let's just use d=mp (mystery person).
            return f"https://www.gravatar.com/avatar/{hash_email}?d=mp&s=150"
            
        return ""


class Artista(models.Model):
    """Rappresenta un artista musicale."""
    user = models.ForeignKey(User, on_delete=models.CASCADE, default=1, related_name='artisti')
    nome = models.CharField(max_length=255)
    biografia = models.TextField(blank=True, default='')
    immagine_profilo = models.ImageField(
        upload_to='artisti/profilo/',
        blank=True,
        null=True,
    )

    class Meta:
        ordering = ['nome']
        verbose_name_plural = 'Artisti'

    def __str__(self):
        return self.nome


class Album(models.Model):
    """Rappresenta un album musicale con tipo release e formato fisico."""

    class TipoRelease(models.TextChoices):
        ALBUM = 'album', 'Album'
        CONCERTO = 'concerto', 'Concerto'

    class FormatoFisico(models.TextChoices):
        CD = 'cd', 'CD'
        VINILE = 'vinile', 'Vinile'
        DVD = 'dvd', 'DVD'
        BLURAY = 'bluray', 'Blu-Ray'

    user = models.ForeignKey(User, on_delete=models.CASCADE, default=1, related_name='album_personali')
    titolo = models.CharField(max_length=255)
    artista = models.ForeignKey(
        Artista,
        on_delete=models.CASCADE,
        related_name='album',
    )
    anno_uscita = models.IntegerField(
        validators=[MinValueValidator(1900), MaxValueValidator(2100)],
    )
    copertina = models.ImageField(
        upload_to='album/copertine/',
        blank=True,
        null=True,
    )
    tipo_release = models.CharField(
        max_length=10,
        choices=TipoRelease.choices,
        default=TipoRelease.ALBUM,
        verbose_name='Tipo di release',
    )
    formato_fisico = models.CharField(
        max_length=10,
        choices=FormatoFisico.choices,
        blank=True,
        default='',
        verbose_name='Formato fisico',
    )
    digitale_acquistato = models.BooleanField(
        default=False,
        verbose_name='Digitale Acquistato'
    )


    class Meta:
        ordering = ['-anno_uscita', 'titolo']
        verbose_name_plural = 'Album'

    def __str__(self):
        return f"{self.titolo} — {self.artista.nome}"

    @property
    def formato_display(self):
        """Restituisce il label del formato fisico o stringa vuota."""
        if self.formato_fisico:
            return self.get_formato_fisico_display()
        return ''

    @property
    def durata_totale_minuti(self):
        """Calcola la durata totale dell'album in minuti."""
        from django.db.models import Sum
        totale = self.canzoni.aggregate(Sum('durata'))['durata__sum']
        if totale:
            return int(totale.total_seconds()) // 60
        return 0


class Canzone(models.Model):
    """Rappresenta una canzone (traccia) all'interno di un album."""
    titolo = models.CharField(max_length=255)
    album = models.ForeignKey(
        Album,
        on_delete=models.CASCADE,
        related_name='canzoni',
    )
    durata = models.DurationField(
        help_text='Durata nel formato HH:MM:SS',
        blank=True,
        null=True,
    )
    numero_traccia = models.PositiveIntegerField(default=1)
    testo = models.TextField(
        blank=True,
        null=True,
        verbose_name="Testo"
    )

    class Meta:
        ordering = ['numero_traccia']
        verbose_name_plural = 'Canzoni'

    def __str__(self):
        return f"{self.numero_traccia}. {self.titolo}"

    @property
    def durata_formattata(self):
        if not self.durata:
            return ""
        s = int(self.durata.total_seconds())
        return f"{s // 60:02d}:{s % 60:02d}"


class MetadatoArtista(models.Model):
    artista = models.ForeignKey(
        Artista, 
        on_delete=models.CASCADE, 
        related_name='metadati'
    )
    chiave = models.CharField(max_length=100)
    valore = models.CharField(max_length=255)

    class Meta:
        verbose_name_plural = "Metadati Artista"
        unique_together = ('artista', 'chiave', 'valore')

    def __str__(self):
        return f"{self.chiave}: {self.valore}"


class MetadatoCanzone(models.Model):
    canzone = models.ForeignKey(
        Canzone, 
        on_delete=models.CASCADE, 
        related_name='metadati'
    )
    chiave = models.CharField(max_length=100)
    valore = models.CharField(max_length=255)

    class Meta:
        verbose_name_plural = "Metadati Canzone"
        unique_together = ('canzone', 'chiave', 'valore')

    def __str__(self):
        return f"{self.chiave}: {self.valore}"


class VotoAlbum(models.Model):
    """Voto (0.5-5 stelle) di un utente per un album."""
    utente = models.ForeignKey(User, on_delete=models.CASCADE, related_name='voti_album')
    album = models.ForeignKey(Album, on_delete=models.CASCADE, related_name='voti')
    punteggio = models.DecimalField(
        max_digits=2, decimal_places=1,
        validators=[MinValueValidator(0.5), MaxValueValidator(5.0)],
        help_text='Punteggio da 0.5 a 5.0 stelle',
    )

    class Meta:
        unique_together = ('utente', 'album')
        verbose_name_plural = 'Voti Album'

    def __str__(self):
        return f"{self.utente.username} → {self.album.titolo}: {self.punteggio}★"


class VotoArtista(models.Model):
    """Voto (0.5-5 stelle) di un utente per un artista."""
    utente = models.ForeignKey(User, on_delete=models.CASCADE, related_name='voti_artista')
    artista = models.ForeignKey(Artista, on_delete=models.CASCADE, related_name='voti')
    punteggio = models.DecimalField(
        max_digits=2, decimal_places=1,
        validators=[MinValueValidator(0.5), MaxValueValidator(5.0)],
        help_text='Punteggio da 0.5 a 5.0 stelle',
    )

    class Meta:
        unique_together = ('utente', 'artista')
        verbose_name_plural = 'Voti Artisti'

    def __str__(self):
        return f"{self.utente.username} → {self.artista.nome}: {self.punteggio}★"


class VotoCanzone(models.Model):
    """Voto (0.5-5 stelle) di un utente per una canzone."""
    utente = models.ForeignKey(User, on_delete=models.CASCADE, related_name='voti_canzone')
    canzone = models.ForeignKey(Canzone, on_delete=models.CASCADE, related_name='voti')
    punteggio = models.DecimalField(
        max_digits=2, decimal_places=1,
        validators=[MinValueValidator(0.5), MaxValueValidator(5.0)],
        help_text='Punteggio da 0.5 a 5.0 stelle',
    )

    class Meta:
        unique_together = ('utente', 'canzone')
        verbose_name_plural = 'Voti Canzoni'

    def __str__(self):
        return f"{self.utente.username} → {self.canzone.titolo}: {self.punteggio}★"

