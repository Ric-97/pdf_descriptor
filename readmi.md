# PDF Descriptor with AI Vision - Documentazione Tecnica

## Panoramica

PDF Descriptor è un'applicazione web basata su Streamlit che utilizza l'intelligenza artificiale per analizzare documenti PDF e generare descrizioni dettagliate in italiano. L'applicazione supporta sia l'elaborazione nativa dei PDF tramite Anthropic Claude (con capacità di visione) che l'analisi testuale tramite OpenAI.

## Caratteristiche Principali

### 1. Supporto Multi-Provider
- **Anthropic (Claude)**: Elaborazione nativa PDF con analisi visuale e testuale
- **OpenAI (GPT-4)**: Analisi basata su estrazione del testo

### 2. Modelli Supportati

#### Anthropic Claude:
- **Claude Opus 4** (`claude-opus-4-20250514`): Il modello più potente per analisi complesse
- **Claude Sonnet 4** (`claude-sonnet-4-20250514`): Bilanciamento ottimale tra prestazioni e costo
- **Claude Sonnet 3.7** (`claude-3-7-sonnet-20250219`): Versione precedente stabile
- **Claude 3.5 Sonnet** (`claude-3-5-sonnet-20241022`): Modello di generazione precedente
- **Claude 3.5 Haiku** (`claude-3-5-haiku-20241022`): Il più veloce ed economico

#### OpenAI:
- **GPT-4o**: Modello ottimizzato per l'analisi testuale

### 3. Limiti Tecnici
- **Dimensione file**: Massimo 32MB
- **Numero pagine**: Massimo 100 pagine
- **Token output**: Fino a 8192 token per risposta

## Architettura del Sistema

### Dipendenze
```python
streamlit          # Framework UI web
anthropic          # SDK per Claude API
openai             # SDK per OpenAI API
PyPDF2            # Estrazione testo da PDF
base64            # Encoding file per API
zipfile           # Creazione archivi risultati
```

### Flusso di Elaborazione

#### 1. Input e Validazione
```
Utente → Upload PDF → Validazione dimensioni/pagine → Selezione provider/modello
```

#### 2. Elaborazione Anthropic (Native PDF)
```
PDF → Base64 encoding → API Claude (document type) → Analisi visuale + testuale → Descrizione
```

#### 3. Elaborazione OpenAI
```
PDF → PyPDF2 estrazione testo → API GPT-4 → Analisi testuale → Descrizione
```

#### 4. Output
```
Descrizione → ZIP file (PDF originale + descrizione.txt) → Download
```

## Funzioni Principali

### `extract_text_from_pdf(pdf_file)`
Estrae il testo completo da un PDF utilizzando PyPDF2.

**Parametri:**
- `pdf_file`: File PDF caricato

**Ritorna:**
- `full_text`: Testo estratto con separatori di pagina
- `num_pages`: Numero totale di pagine

### `encode_pdf_to_base64(pdf_file)`
Converte il PDF in stringa base64 per l'invio tramite API.

**Parametri:**
- `pdf_file`: File PDF da codificare

**Ritorna:**
- Stringa base64 del PDF

### `analyze_pdf_with_anthropic(api_key, pdf_file, model_choice)`
Invia il PDF all'API Anthropic per l'analisi nativa.

**Parametri:**
- `api_key`: Chiave API Anthropic
- `pdf_file`: File PDF da analizzare
- `model_choice`: Modello Claude selezionato

**Processo:**
1. Codifica PDF in base64
2. Crea messaggio con tipo "document"
3. Invia richiesta con prompt italiano specifico
4. Gestisce errori di rate limit e generici

### `analyze_with_openai_text(api_key, pdf_text)`
Analizza il testo estratto utilizzando OpenAI GPT-4.

**Parametri:**
- `api_key`: Chiave API OpenAI
- `pdf_text`: Testo estratto dal PDF

**Ritorna:**
- Descrizione generata da GPT-4

### `create_zip_with_results(pdf_file, description_text, provider, model_name)`
Crea un archivio ZIP contenente il PDF originale e la descrizione.

**Contenuto ZIP:**
- `original_[nomefile].pdf`: PDF originale
- `descrizione_[provider]_[modello]_[nomefile].txt`: Descrizione generata

### `calculate_tokens(num_pages)`
Calcola l'utilizzo stimato di token per l'elaborazione nativa PDF.

**Formula di calcolo:**
- **Token testuali**: ~2250 token/pagina
- **Token immagine**: ~1600 token/pagina
- **Token output**: ~500 token/pagina (max 8192)

## Interfaccia Utente

### Layout Principale
1. **Header**: Titolo e descrizione dell'applicazione
2. **Provider Selection**: Dropdown per scegliere tra Anthropic e OpenAI
3. **Model Selection**: Radio button per selezione modello (solo Anthropic)
4. **API Key Input**: Campo password per chiave API
5. **File Upload**: Area upload PDF con validazione
6. **Metrics Display**: Mostra dimensione file e numero pagine
7. **Token Analysis**: Analisi dettagliata token (solo Anthropic)
8. **Process Button**: Avvia l'analisi
9. **Results Section**: Preview e download risultati

### Componenti Aggiuntivi
- **Model Tips**: Suggerimenti in base al modello selezionato
- **Instructions Expander**: Guida rapida all'uso
- **Technical Details Expander**: Informazioni tecniche approfondite

## Prompt di Analisi

Il prompt utilizzato per l'analisi richiede:
1. Numerazione chiara delle pagine
2. Descrizione dettagliata del contenuto testuale
3. Analisi di grafici, tabelle, immagini e diagrammi
4. Evidenziazione delle informazioni chiave
5. Mantenimento della struttura originale
6. Output completo in italiano

## Gestione Errori

### Errori Gestiti:
1. **File troppo grande**: >32MB
2. **Troppe pagine**: >100 pagine
3. **Rate limit API**: Messaggio specifico con retry
4. **Errori generici API**: Log dettagliato dell'errore
5. **Errori estrazione testo**: Fallback o notifica utente

## Performance e Ottimizzazioni

### Ottimizzazioni Implementate:
1. **Spinner durante elaborazione**: Feedback visivo all'utente
2. **Preview limitato**: Solo primi 2000 caratteri per performance UI
3. **Calcolo token preventivo**: Stima costi prima dell'elaborazione
4. **Gestione memoria**: Reset seek(0) per riutilizzo file buffer

### Considerazioni Performance:
- L'elaborazione nativa PDF è più lenta ma più accurata
- Haiku 3.5 offre il miglior rapporto velocità/costo
- File grandi possono richiedere diversi minuti

## Sicurezza

### Misure di Sicurezza:
1. **API Key nascosta**: Input type="password"
2. **No storage API key**: Chiave non salvata localmente
3. **Validazione input**: Controlli su dimensione e formato
4. **Sanitizzazione nomi file**: Nei file ZIP generati

## Deployment e Configurazione

### Requisiti Sistema:
- Python 3.8+
- Memoria RAM: Minimo 4GB consigliati
- Connessione internet stabile

### Installazione:
```bash
pip install streamlit anthropic openai PyPDF2
```

### Avvio Applicazione:
```bash
streamlit run pdf_analyzer.py
```

### Variabili Ambiente (Opzionali):
```bash
export ANTHROPIC_API_KEY="your-key"
export OPENAI_API_KEY="your-key"
```

## Flusso Dettagliato Chiamate API

### Anthropic Claude - Elaborazione Nativa PDF

#### 1. Preparazione della Richiesta
```python
# Il PDF viene codificato in base64
pdf_base64 = encode_pdf_to_base64(pdf_file)

# Struttura del messaggio API
message = {
    "role": "user",
    "content": [
        {
            "type": "document",
            "source": {
                "type": "base64",
                "media_type": "application/pdf",
                "data": pdf_base64  # PDF completo codificato
            }
        },
        {
            "type": "text",
            "text": "Prompt di analisi in italiano..."
        }
    ]
}
```

#### 2. Chiamata API
```python
# Singola chiamata all'API Anthropic
response = client.messages.create(
    model="claude-sonnet-4-20250514",  # o altro modello selezionato
    max_tokens=8192,
    messages=[message]
)
```

#### 3. Flusso Completo Anthropic
```
1. Utente carica PDF
2. Sistema valida dimensioni (max 32MB, 100 pagine)
3. PDF → Base64 encoding
4. Creazione messaggio con:
   - Tipo "document" con PDF base64
   - Prompt testuale con istruzioni
5. SINGOLA chiamata API a Claude
6. Claude elabora simultaneamente:
   - Contenuto testuale del PDF
   - Analisi visuale di ogni pagina
7. Risposta con descrizione completa
8. Creazione ZIP con risultati
```

### OpenAI GPT-4 - Elaborazione Testuale

#### 1. Estrazione Testo
```python
# Prima il testo viene estratto localmente
pdf_reader = PyPDF2.PdfReader(pdf_file)
full_text = ""
for i, page in enumerate(pdf_reader.pages):
    page_text = page.extract_text()
    full_text += f"\n\n--- Pagina {i+1} ---\n{page_text}"
```

#### 2. Chiamata API
```python
# Singola chiamata all'API OpenAI
response = client.chat.completions.create(
    model="gpt-4o",
    messages=[{
        "role": "user",
        "content": prompt + full_text  # Testo estratto incluso nel prompt
    }],
    max_tokens=8192
)
```

#### 3. Flusso Completo OpenAI
```
1. Utente carica PDF
2. PyPDF2 estrae tutto il testo (elaborazione locale)
3. Testo estratto + prompt → formattazione messaggio
4. SINGOLA chiamata API a GPT-4
5. GPT-4 analizza solo il testo (no immagini/grafici)
6. Risposta con descrizione testuale
7. Creazione ZIP con risultati
```

### Differenze Chiave tra i Provider

| Aspetto | Anthropic | OpenAI |
|---------|-----------|---------|
| Numero chiamate API | 1 | 1 |
| Preprocessing | Solo encoding Base64 | Estrazione testo con PyPDF2 |
| Dati inviati | PDF completo (testo + immagini) | Solo testo estratto |
| Capacità analisi | Testo + elementi visivi | Solo testo |
| Token utilizzati | ~3100-4600 per pagina | ~2250 per pagina |

### Note Importanti sul Flusso API

1. **Nessun loop o chiamate multiple**: Entrambi i provider ricevono una singola chiamata API per l'intero documento
2. **Elaborazione atomica**: L'intero PDF viene processato in una singola richiesta
3. **Timeout handling**: Le chiamate API hanno timeout generosi per PDF grandi
4. **Error handling**: In caso di errore, l'intera operazione fallisce (no partial processing)

## Troubleshooting

### Problemi Comuni:

**1. "Rate limit reached"**
- Soluzione: Attendere 60 secondi e riprovare
- Alternativa: Usare modello con rate limit più alto

**2. "Error extracting text from PDF"**
- Causa: PDF corrotto o con encoding speciale
- Soluzione: Provare con provider Anthropic per analisi nativa

**3. "File size exceeds limit"**
- Soluzione: Comprimere PDF o dividerlo in parti

**4. Download ZIP non funziona**
- Causa: Browser blocking o estensioni
- Soluzione: Disabilitare ad-blocker o provare altro browser

## Contatti e Supporto

Sviluppato da: Digital Solutions and Platform

Per segnalazioni o richieste di funzionalità, contattare il team di sviluppo.

---

*Ultima versione: Gennaio 2025*