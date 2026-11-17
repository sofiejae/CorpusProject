# CorpusProject: Relinquishment Report Explorer

Et enkelt verktøy for å **søke i og telle ord i** NPD-rapportene om tilbakelevering av utvinningstillatelser
(relinquishment reports). Du bruker det i nettleseren, uten å skrive kode.

Verktøyet kommer med 120 rapporter som allerede er ferdig behandlet, så du kan begynne å utforske med en gang.

---

## Hva kan du bruke det til?

| Funksjon | Hva den gjør | Eksempel |
|---|---|---|
| **Concordance** | Viser alle steder et ord står, med ordene rundt | Hvordan brukes «prospect» i teksten? |
| **Word frequency** | Teller hvor mange ganger et ord forekommer | Hvor ofte står «well»? |
| **Frequent words** | Lister de vanligste ordene | Hva handler tekstene mest om? |
| **N-gram search** | Finner ordrekker som går igjen (2–6 ord) | Hvilke uttrykk starter med «licence»? |
| **Collocations** | Finner ord som ofte står *sammen med* et ord | Hvilke ord står ofte nær «well»? |
| **Metadata viewer** | Oversikt over alle dokumentene | Hvor lang er hver rapport? |

Alle tabellene kan lastes ned som CSV-fil (åpnes i Excel) med knappen **Download CSV**.

---

## Kom i gang (første gang)

Du trenger bare gjøre dette én gang.

### Steg 1: Installer Python
1. Gå til <https://www.python.org/downloads/> og last ned nyeste versjon.
2. Kjør installasjonsprogrammet.
   **Windows:** huk av for **«Add python.exe to PATH»** på første skjermbilde. Det er lett å glemme.

### Steg 2: Åpne prosjektmappen i terminalen
Terminalen er et vindu der du skriver korte kommandoer.

- **Mac:** åpne programmet *Terminal*. Skriv `cd ` (med mellomrom bak), dra prosjektmappen inn i vinduet og trykk Enter.
- **Windows:** åpne prosjektmappen i Filutforsker, klikk i adressefeltet øverst, skriv `cmd` og trykk Enter.

### Steg 3: Installer det programmet trenger
Kopier denne linjen inn i terminalen og trykk Enter. Det tar noen minutter.

```
pip install -r requirements.txt
```

> Får du feilmeldingen «pip finnes ikke»? Prøv `pip3 install -r requirements.txt` eller `python -m pip install -r requirements.txt`.

---

## Slik starter du programmet (hver gang)

1. Åpne terminalen i prosjektmappen (steg 2 over).
2. Skriv:

   ```
   streamlit run StreamlitApp.py
   ```

3. Nettleseren åpner seg av seg selv med verktøyet. Hvis ikke, åpne <http://localhost:8501>.

For å **avslutte**: lukk nettleserfanen, gå til terminalen og trykk `Ctrl + C`.

---

## Slik bruker du verktøyet

### 1. Velg analyse
I menyen til **venstre** velger du hva du vil gjøre («Choose analysis mode»).

### 2. Skriv inn søkeord
Skriv ordet i feltet. Bruk **små bokstaver** eller store, det spiller ingen rolle. Ordene er på **engelsk**,
fordi rapportene er skrevet på engelsk.

### 3. Velg dokument
Under søkefeltet kan du velge **«All documents»** (hele samlingen) eller ett enkelt dokument.

### 4. Les resultatet
Resultatet vises som en tabell. Klikk på en kolonneoverskrift for å sortere.

### Tips for hver funksjon

- **Concordance:** Du kan også søke på uttrykk, for eksempel `production licence`.
  Glidebryteren *Context window* bestemmer hvor mange ord du ser på hver side.
- **Word frequency:** Viser både antall og «per 1 000 ord». Det siste er best når du sammenligner dokumenter
  av ulik lengde.
- **Frequent words:** Kryss av for *Exclude grammatical words* for å skjule småord som «the», «of» og «and».
  Da blir de innholdsrike ordene synlige.
- **N-gram search:** Et n-gram er en rekke på *n* ord. Velg *n* med glidebryteren, og om søkeordet skal stå
  først, sist eller hvor som helst. La søkefeltet stå tomt for å se de vanligste ordrekkene totalt.
- **Collocations:** *Window* sier hvor mange ord på hver side som regnes som «i nærheten».
  *logDice* og *PMI* er to måter å rangere hvor sterkt to ord hører sammen. Start med logDice.
  Den gir mest stabile resultater.
- **Metadata viewer:** Viser blant annet lisensnummer, lengde og antall ulike ord for hvert dokument.

---

## Vanlige spørsmål

**«Loaded 115 documents (5 duplicates skipped)». Mangler det noen?**
Nei. Noen rapporter ligger i samlingen under flere filnavn med nøyaktig samme tekst. Verktøyet teller bare én
av dem, ellers ville alle tall blitt for høye. Vil du heller telle alle, fjerner du haken ved
*Skip duplicate documents* i menyen til venstre.

**Kan jeg legge til egne PDF-er?**
Ja. Legg dem i mappen `Corpus/raw_data/`. Velg deretter **«PDF folder»** under *Corpus source* i menyen til venstre.
Første gang tar det noen minutter per dokument, og etterpå går det raskt. Er en PDF en skannet kopi (bilde av tekst),
trenger programmet [Tesseract](https://github.com/tesseract-ocr/tesseract) for å lese den.
På Mac installerer du det med `brew install tesseract`.

**Hva er «AI-extracted metadata»?**
En valgfri funksjon som sender begynnelsen av en rapport til OpenAI for å finne tittel, operatør og dato.
Den krever en betalt API-nøkkel og er ikke nødvendig for noe annet. Du kan trygt ignorere den.

**Siden viser ingenting / det skjedde en feil**
Sjekk at du står i riktig mappe, at du installerte alt i steg 3, og at terminalvinduet fortsatt er åpent.
Se etter en rød feilmelding i terminalen. Den forteller ofte hva som mangler.

---

## For deg som vil se under panseret

```
StreamlitApp.py      Selve nettsiden (menyer, knapper, tabeller)
my_tools/
  Corpus.py          Samlingen av dokumenter
  Document.py        Ett dokument: leser PDF, renser tekst, deler opp i ord
  TextProcessor.py   Selve analysene (konkordans, frekvens, n-gram, kollokasjoner)
  OCRProcessor.py    Leser skannede PDF-er
  GenAIClient.py     Valgfri AI-uthenting av metadata
Corpus/pickled/      Ferdig behandlede dokumenter (gjør oppstart rask)
Corpus/raw_data/     Legg egne PDF-er her
tests/               Automatiske tester: python -m unittest discover -v
```

Merk: `.pkl`-filene i `Corpus/pickled/` er Python-«pickles». Last bare inn slike filer du har laget selv eller stoler på.
