# Music Library

## About This Project

**Music Library** is a feature-rich, responsive web application built with Python and Django. It is designed to help users manage, organize, and explore their personal music collection. 

Key features include:
- **Comprehensive Library Management:** Store and manage detailed information about your favorite Albums and Artists.
- **External API Integrations:** Seamlessly search and import high-quality metadata, album covers, and artist biographies using integrations with the **MusicBrainz** and **TheAudioDB** APIs.
- **Advanced Filtering & Sorting:** Easily find what you are looking for by grouping albums by artist, sorting by release year or title, and filtering by physical format (Vinyl, CD, Digital, etc.).
- **Modern User Interface:** A highly customized, responsive front-end featuring dynamic Grid and List views, pagination, and a built-in Light/Dark mode toggle.
- **CSV Data Import:** Quickly bulk-upload your existing music collection through a CSV upload tool.
- **User Ratings & Authentication:** Create an account to securely save your library and rate your favorite albums and artists.


---

## Struttura dei File del Progetto

```text
music_library/
├── manage.py                  # Entrypoint standard di Django
├── pyproject.toml / uv.lock   # Dipendenze e virtual environment manager (uv)
├── db.sqlite3                 # Database SQLite locale
├── README.md                  # Questo file
│
├── core/                      # Progetto Django in senso stretto (settaggi globali)
│   ├── settings.py            # Configurazioni generali, database, app installate
│   ├── urls.py                # Rotte principali e inclusione di library/
│   ├── wsgi.py / asgi.py      # Entrypoint per server
│   └── __init__.py
│
├── library/                   # L'app Django principale del progetto
│   ├── models.py              # I modelli del database (Artista, Album, Canzone, ecc.)
│   ├── views.py               # Le logiche e le class-based view
│   ├── forms.py               # ModelForm per le interazioni con i modelli
│   ├── urls.py                # Rotte specifiche dell'app
│   ├── admin.py               # Registrazione dei modelli per l'admin panel
│   ├── tests.py               # Test automatici
│   │
│   ├── static/                # File statici
│   │   ├── css/style.css      # Foglio di stile CSS personalizzato
│   │   └── scripts/main.js    # Script JavaScript (es. per interazioni)
│   │
│   └── templates/library/     # Template HTML dell'app
│       ├── base.html          # Il template base da cui ereditano gli altri
│       ├── album_*.html       # CRUD e viste per gli Album
│       ├── artista_*.html     # CRUD e viste per gli Artisti
│       ├── canzone_*.html     # CRUD per le Canzoni
│       ├── search.html        # Vista per la ricerca
│       ├── csv_upload.html    # Upload in blocco tramite CSV
│       ├── musicbrainz_*.html # Ricerca su API esterne
│       └── login.html / register.html # Autenticazione utente
│
└── media/                     # File caricati dagli utenti a runtime
    ├── album/                 # Copertine degli album
    └── artisti/               # Immagini del profilo degli artisti
```

---

## Struttura del Database

[Visualizza lo schema Entità-Relazione interattivo su Mermaid Live](https://mermaid.live/edit#pako:eNq9VttO20AQ_ZXVSpVACpQQQojfUggV4hIECQ8okjWxJ8609q67XqeUhH_pY_-DH-s6ELDjDVhIrZ_snTmzZ8_MznjGPekjdziqI4JAQTRUQ8HM8-kTu8IQ7kkKYgONQuPSNLjuXrH5fGtrPl-8u5dXveOTsy5z2JBPgG3UnfrmkJfc5Yx1rvon1_3OwpNEgooSDz8HmOjsJUNerEOefRmcfwB30-v33Py2mMSKogqYlw2rIg47F7e9i-46TE7Zr6hAeRMCdp4m5EH4ou2SaenUcToahcZ1lcWTx7N7noEnhSYU6yicowYfNLGNS9AalWDdzs3mGhrn3X7nqLMi5OMf5mPiKdJaMr9EbMllNUSeYy4ErITI1yF5mNUhshupaQ3FUp6VQU3xTblW8mxHrJyjlOkyKkf9CMck6Il81-RDP_5myDpaKxqlr2dZlNJs-ZU9JDQjn12e5hcTAxMBS039C4jQYsIIKLSsx5AkP6XyLaYxqUS7a-KFYLGZskGdFXf24n6TJPAl8ENegEJzqHw8mIIGtdbgpipcDZUp4pp4x6cmIYPT1-QV6CyrozITIYsH13in2Yik6ZNjAguAoggCI4cbKzmmUK7naSe4KMXK9Ew5yfIeIIR008QjbWPoyRiVJmGzjaWKQEt3TKYnSeuGsXQVhghJQZeRlCHzKTBbhuiC9yOlRJtIJWpmZ2MoKlBRm-WVe1-dbFGkESrpagWeZ81UWbuR4W-QfqqgqNwi69qMGps7hKM0eoN2qXNWzm42Hqa2OzmFUCq0cbHJa2dTXc0Ps_FA3Ju29wabQst-n4mPHkUQsjg1_yJBQOXbtfhLKVdXZXly8-A_0HmncgqD5t_TsaeL13igyOeOVinWuLlUZsCYTz7LHIZcT9C0SJ7NQR_Ud9N4RYaJQdxKGS1hSqbBhDtjCBPzlcbZ3Hj-3XxxQeGjOpSGPXcO9huLGNyZ8TvuNPaa2-3GwUGrsduu79Sb-zX-izt7LbPYau609nfbjfZes_FQ4_eLTXe2D8y6eertnd12s9VuPfwFrUhQDg)

Il progetto è basato su diverse tabelle (modelli) principali:

- **User & UserProfile**: Gestiscono l'autenticazione degli utenti e memorizzano il loro avatar (con fallback a Gravatar).
- **Artista**: Raccoglie i dati degli artisti salvati dall'utente (nome, biografia, foto profilo).
- **Album**: Salva i dettagli delle release (titolo, anno di uscita, formato fisico/digitale) collegandoli al proprio `Artista`.
- **Canzone**: Rappresenta le singole tracce musicali (con durata e numero traccia) appartenenti a un `Album`.
- **MetadatoArtista / MetadatoCanzone**: Tabelle chiave-valore per permettere l'aggiunta di infinite proprietà flessibili (es. "Ruolo: Cantante", "Strumento: Chitarra").
- **VotoAlbum / VotoArtista / VotoCanzone**: Gestiscono le recensioni e i rating (da 0.5 a 5 stelle) assegnati dall'utente.

---

## Installation & Setup

This project uses [uv](https://github.com/astral-sh/uv), an extremely fast Python package and project manager. 

### Prerequisites
- **Python:** version `>= 3.14`
- **uv:** Follow the [uv installation guide](https://docs.astral.sh/uv/getting-started/installation/) if you don't have it installed on your system.

### Dependencies
The project relies on the following main Python libraries (automatically managed by `uv`):
- `Django >= 6.1.1` (Web framework)
- `Pillow >= 11.0.0` (Image processing for covers/avatars)
- `requests >= 2.32.0` (For external API calls to MusicBrainz/TheAudioDB)

### Step-by-step Guide

1. **Clone the repository**
   Open your terminal and clone the project to your local machine:
   ```bash
   git clone https://github.com/itsmrma/uni-musiclib-project
   cd uni-musiclib-project
   ```

2. **Install dependencies with `uv`**
   Run the following command to automatically create a virtual environment and install all required dependencies listed in the `pyproject.toml` and `uv.lock` files:
   ```bash
   uv sync
   ```

3. **Apply Database Migrations**
   Initialize the SQLite database by running the Django migrations:
   ```bash
   uv run manage.py migrate
   ```

4. **Create a Superuser (Optional but recommended)**
   To access the Django admin panel and have full permissions, create an admin account:
   ```bash
   uv run manage.py createsuperuser
   ```

5. **Start the Development Server**
   Launch the local web server:
   ```bash
   uv run manage.py runserver
   ```

6. **Test it on your PC**
   Open your favorite web browser and navigate to:
   [http://127.0.0.1:8000/](http://127.0.0.1:8000/)

   You can now create an account, log in, and start adding music to your new library!

---
*This is a university project developed for UNIMORE (Università degli Studi di Modena e Reggio Emilia).*
