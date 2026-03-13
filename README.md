# Meeting Recap Agent

Agente locale che trascrive riunioni audio `.mp3` e genera un recap strutturato,
pronto per essere inviato via email ai partecipanti.

**Nessun dato esce dalla tua macchina** per la trascrizione (Whisper gira in locale).
Solo il testo trascritto viene inviato alle API di **Google Gemini 2.5 Flash-Lite** per la sintesi.

> 💡 **Costo: €0,00** — Gemini 2.5 Flash-Lite ha un free tier di 1.000 richieste/giorno.

---

## Architettura

```
audio.mp3
    │
    ▼
[Whisper — locale, GRATUITO]
    │  trascrizione testuale
    ▼
[Gemini 2.5 Flash-Lite — Pass 1]  →  Prima bozza del recap
    │
    ▼
[Gemini 2.5 Flash-Lite — Pass 2]  →  Verifica accuratezza vs trascrizione
    │
    ▼
[Gemini 2.5 Flash-Lite — Pass 3]  →  Revisione finale + formattazione email
    │
    ▼
recap.md  +  recap_debug.md (bozze intermedie)
```

---

## Setup

### 1. Prerequisiti
- Python 3.8+
- [ffmpeg](https://ffmpeg.org/download.html) installato e nel PATH (necessario per Whisper)

### 2. Ambiente virtuale e dipendenze

```bash
python -m venv .venv
.venv\Scripts\activate        # Windows
# source .venv/bin/activate   # Linux/macOS

pip install -r requirements.txt
```

### 3. Chiave API Google Gemini (GRATUITA)

```bash
cp .env.example .env
# Apri .env e inserisci la tua GEMINI_API_KEY
```

1. Vai su [aistudio.google.com/apikey](https://aistudio.google.com/apikey)
2. Crea un account Google (o accedi) → clicca **"Create API key"**
3. Copia la chiave nel file `.env`:
   ```
   GEMINI_API_KEY=AIzaSy...
   ```

> Free tier: **1.000 richieste/giorno**, **250.000 token/minuto** — più che sufficiente per uso personale.

---

## Utilizzo

### Uso base

```bash
python agent.py riunione.mp3
```

Output: `riunione_recap.md` nella stessa cartella.

### Opzioni

```bash
python agent.py riunione.mp3 --output mio_recap.md --model small
```

| Opzione | Default | Descrizione |
|---------|---------|-------------|
| `--output` / `-o` | `<nome_audio>_recap.md` | File di output |
| `--model` / `-m` | `small` | Modello Whisper: `tiny`, `base`, `small`, `medium`, `large` |

### Scelta del modello Whisper

| Modello | Dimensione | Velocità | Accuratezza |
|---------|-----------|---------|-------------|
| `tiny`  | ~39 MB  | ★★★★★ | ★★☆☆☆ |
| `base`  | ~74 MB  | ★★★★☆ | ★★★☆☆ |
| `small` | ~244 MB | ★★★☆☆ | ★★★★☆ |
| `medium`| ~769 MB | ★★☆☆☆ | ★★★★★ |
| `large` | ~1.5 GB | ★☆☆☆☆ | ★★★★★ |

Per riunioni in italiano si consiglia almeno `small`.

---

## Output

Il file `_recap.md` contiene:
- **Oggetto email** suggerito
- **Punti chiave discussi**
- **Decisioni e takeaway**
- **Open points**
- **Prossimi passi / Action items**
- Trascrizione completa in appendice

Il file `_debug.md` contiene le bozze intermedie dei 3 passaggi (utile per audit).

---

## Troubleshooting

### ❌ `ffmpeg not found` / `CreateProcess` error
Whisper richiede ffmpeg per leggere i file audio. Installalo con **winget** (metodo consigliato su Windows):

```powershell
winget install Gyan.FFmpeg
```

Poi **riapri il terminale** (serve per aggiornare il PATH), e verifica:
```powershell
ffmpeg -version
```

In alternativa, scarica manualmente da [gyan.dev/ffmpeg/builds](https://www.gyan.dev/ffmpeg/builds/) → estrai in `C:\ffmpeg` → aggiungi `C:\ffmpeg\bin` alle variabili d'ambiente di sistema (PATH).

---

### ❌ `FutureWarning: google.generativeai is deprecated`
Questo warning è già risolto nel codice: la versione attuale usa `google.genai`.
Se compare ancora, reinstalla le dipendenze:
```bash
pip install -r requirements.txt
```

---

### ❌ `GEMINI_API_KEY non trovata`
Assicurati di aver creato il file `.env` con la chiave (vedi Setup punto 3).

---

### ❌ `404 Not Found` — modello non disponibile
Il modello `gemini-2.5-flash-lite` potrebbe non essere ancora disponibile nella tua regione.
Apri `agent.py` e cambia la riga:
```python
GEMINI_MODEL = "gemini-2.5-flash-lite"
```
con uno di questi fallback:
```python
GEMINI_MODEL = "gemini-2.5-flash"   # più potente, stesso free tier
GEMINI_MODEL = "gemini-2.0-flash"   # alternativa stabile
```

---

### ⚠️ Trascrizione imprecisa
Usa un modello Whisper più grande:
```bash
python agent.py riunione.mp3 --model medium
```
