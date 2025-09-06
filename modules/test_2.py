import json
import random

"""
1. Get dei valori di conversione per tutti gli ingredienti (grams, cups, units) dalla tabella "ingredients" e creo un dizionario di conversione
         {ingrediete1 : {grams_for_units : ..., grams_for_cups : ...}, ingrediete2 : {grams_for_units : ..., grams_for_cups : ...}}
    Funzione "Converti" che dato nome ingrediente, quantità e unità di misura ritorna la quantità in grammi:
    prendendo il corrispettivo valore "factor" e "to" (cups, units, o grams) da conversioni.json data un unità di misura,
    poi moltiplica "facrtor" * quantità e se "to" è cups o units converte in grams moltiplicando per il valore di "grams_for_cups" o "s" dal dizionario di conversione
2. Creazione Lista Ricette:
    Estraggo da recipes.json le ricette e per ognuna estraggo gli ingredienti, le quantità richieste (ammount) e l'unità di misura (unit)
3. Ricetta Realizzabile:
    Confronto se grammi disponibili in dispensa di ogni ingrediente >= grammi richiesti in ricetta dello stesso ingrediente (eseguendo la conversione di quel ingrediente in ricetta)
4. Score:
    Somma dei grammi richiesti per ogni ingrediente che è presente in dispensa (anche qui eseguo la conversione degli ingredieti in ricetta che coincidono con quelli in dispensa)
5. Prendo quella con Score più alto e Rimuovo la ricetta scelta dal set di ricette_valutabili
6. Aggiorno dispensa sottraendo i grammi usati
7. Reitero fino ad avere nessun ingrediente in dispensa o nessuna ricetta realizzabile
"""

# ===== CARICAMENTO DATI DI CONVERSIONE =====
with open('modules/conversioni.json', 'r') as f_conv:
    conversioni = json.load(f_conv)

# Dizionario di conversione per ogni ingrediente
# Verrà passato da app.py mediante chiamata al DB alla tabella "ingredients"
# Formato: {ingrediente: {"grams_for_units": valore, "grams_for_cups": valore}}
dizionario_conversione = {}

def converti_a_grammi(nome_ingrediente, quantita, unita_misura):
    """
    Converte una quantità di ingrediente nella sua unità di misura in grammi.
    
    Args:
        nome_ingrediente (str): Nome dell'ingrediente
        quantita (float): Quantità dell'ingrediente
        unita_misura (str): Unità di misura (es. "cups", "units", "grams", ecc.)
    
    Returns:
        float: Quantità in grammi
    """
    # Normalizza l'unità di misura
    unita_normalizzata = unita_misura.lower().strip()
    
    # Se l'unità non è nelle conversioni, l'ingrediente non esiste (valore 0)
    if unita_normalizzata not in conversioni:
        return 0
    
    conversione = conversioni[unita_normalizzata]
    factor = conversione["factor"]
    to = conversione["to"]
    
    # Applica il fattore di conversione
    quantita_convertita = factor * quantita
    
    # Se "to" è grams, restituisci direttamente
    if to == "grams":
        return quantita_convertita
    
    # Se "to" è cups o units, converti in grammi usando il dizionario
    if nome_ingrediente not in dizionario_conversione:
        # Se l'ingrediente non è nel dizionario, restituisce 0
        return 0
    
    valori_conversione = dizionario_conversione[nome_ingrediente]
    
    if to == "cups":
        return quantita_convertita * valori_conversione["grams_for_cups"]
    elif to == "units":
        return quantita_convertita * valori_conversione["grams_for_units"]
    
    # Fallback: restituisci la quantità convertita
    return quantita_convertita

def ricetta_realizzabile(ricetta, disp):
    """
    Controlla se la ricetta è realizzabile con gli ingredienti attualmente disponibili.
    Confronta i grammi disponibili in dispensa con i grammi richiesti nella ricetta (convertiti).
    Itera per gli ingredienti della ricetta ed esegue la conversione dei soli ingredienti 
    della ricetta che sono anche nella dispensa.
    """
    flag = False
    
    # Itera per gli ingredienti della ricetta (lista di dizionari)
    for ingrediente_ricetta in ricetta["ingredients"]:
        nome = ingrediente_ricetta["name"]
        quantita_richiesta = ingrediente_ricetta["amount"]
        unita = ingrediente_ricetta["unit"]
        
        #TODO inserire il like nel nome
        # Esegui la conversione solo per ingredienti che sono anche nella dispensa
        if nome in disp and disp[nome] > 0: 
            # Converte la quantità richiesta in grammi
            grammi_richiesti = converti_a_grammi(nome, quantita_richiesta, unita)
            grammi_disponibili = disp[nome]
            
            # Se non abbiamo abbastanza di questo ingrediente, la ricetta non è realizzabile
            if grammi_disponibili < grammi_richiesti and grammi_richiesti > 0:
                return False
            else:
                flag = True
    
    return flag


def calcola_punteggio(ricetta, disp):
    """
    Calcola il punteggio della ricetta sommando i grammi richiesti per ogni ingrediente 
    che è presente in dispensa (convertendo le quantità in grammi).
    """
    score = 0
    for ingrediente_ricetta in ricetta["ingredients"]:
        nome = ingrediente_ricetta["name"]
        quantita_richiesta = ingrediente_ricetta["amount"]
        unita = ingrediente_ricetta["unit"]
        
        #TODO inserire il like nel nome
        # Se l'ingrediente è disponibile in dispensa
        if nome in disp and disp[nome] > 0:
            # Converte la quantità richiesta in grammi e la aggiunge al punteggio
            grammi_richiesti = converti_a_grammi(nome, quantita_richiesta, unita)
            score += grammi_richiesti
    
    return score


#TODO: Aggiorno la dispensa sottrendo SOLO i grammi usati nella ricetta selezionata, cups e units vengono azzerati 
# TODO perche farò un DELETE ALL e un insert con i soli grammi rimasti
def aggiorna_ingredienti(disp, ricetta):
    """
    Aggiorna il dizionario degli ingredienti disponibili sottraendo la quantità usata.
    Sottrae SOLO i grammi usati nella ricetta selezionata.
    """
    for ingrediente_ricetta in ricetta["ingredients"]:
        nome = ingrediente_ricetta["name"]
        quantita_richiesta = ingrediente_ricetta["amount"]
        unita = ingrediente_ricetta["unit"]
        
        if nome in disp and disp[nome] > 0:
            # Converte la quantità richiesta in grammi
            grammi_usati = converti_a_grammi(nome, quantita_richiesta, unita)
            
            # Sottrae i grammi usati dalla dispensa
            disp[nome] = max(0, disp[nome] - grammi_usati)
            print(f"{nome}: {disp[nome]} grammi rimasti")


def seleziona_ricette(ingredienti_disponibili, lista_ricette):
    ricette_selezionate = []

    # Per evitare di modificare la lista originale
    ricette_da_valutare = list(lista_ricette)

    while True:
        migliore_punteggio = 0
        migliore_ricetta = None
        ricette_migliori = []  # Lista per raccogliere tutte le ricette con punteggio massimo


        # Valuta tutte le ricette realizzabili
        for ricetta in ricette_da_valutare:
            if ricetta_realizzabile(ricetta, ingredienti_disponibili):
                score = calcola_punteggio(ricetta, ingredienti_disponibili)
                
                # Considera solo ricette con score > 0
                if score > 0:
                    if score > migliore_punteggio:
                        # Se troviamo un punteggio migliore, svuotiamo la lista e aggiungiamo questa ricetta
                        ricette_migliori = [ricetta]
                        migliore_punteggio = score
                    elif score == migliore_punteggio:
                        # Se troviamo una ricetta con lo stesso punteggio massimo, la aggiungiamo alla lista
                        ricette_migliori.append(ricetta)

        # Se nessuna ricetta è realizzabile, interrompi
        if not ricette_migliori:
            break
        # Seleziona casualmente una ricetta tra quelle con punteggio massimo
        migliore_ricetta = random.choice(ricette_migliori)

        # Se nessuna ricetta è realizzabile, interrompi
        if migliore_ricetta is None:
            break

        # Aggiungi la ricetta selezionata
        ricette_selezionate.append({
            "title": migliore_ricetta["title"],
            "score": migliore_punteggio,
        })
        # Aggiorna gli ingredienti disponibili
        aggiorna_ingredienti(ingredienti_disponibili, migliore_ricetta)
        # Rimuovi la ricetta scelta dal set di valutabili
        ricette_da_valutare.remove(migliore_ricetta)

    return ricette_selezionate


# ===== PARSE DEL JSON - Ricette =====
with open('modules/recipes.json' , "r") as json_data:
    data = json.load(json_data) 

ricette_raw = data["recipes"]["results"]

# Vogliamo ottenere una lista di ricette in forma di dizionari come:
# {
#   "title": ...,
#   "ingredients": [{"name": "carrots", "amount": 3.0, "unit": "cups"}, ...]
# }

lista_ricette = []
for ricetta in ricette_raw:
    nome_ricetta = ricetta["title"]
    ingredienti_ricetta = []
    
    for ing in ricetta["nutrition"]['ingredients']:
        nome = ing["name"]  # es. "carrots"
        quantita = ing["amount"]  # es. 3.0
        unit = ing["unit"]  # es. "cups", "units", "grams"
        
        # Manteniamo la struttura originale con nome, quantità e unità
        ingredienti_ricetta.append({
            "name": nome,
            "amount": quantita,
            "unit": unit
        })
    
    lista_ricette.append({
        "title": nome_ricetta,
        "ingredients": ingredienti_ricetta
    })

# ===== ESECUZIONE ALGORITMO GREEDY =====
def esegui_greedy(ingredienti_disponibili_input=None, dizionario_conversione_input=None):
    """
    Funzione wrapper per eseguire l'algoritmo greedy.
    Può essere chiamata da app.py passando ingredienti e dizionario di conversione come parametri.
    Le ricette vengono sempre prese dal JSON caricato in questo file.
    
    Args:
        ingredienti_disponibili_input (dict): Dizionario degli ingredienti disponibili
        dizionario_conversione_input (dict): Dizionario di conversione da DB
    
    Returns:
        tuple: (ricette_selezionate, ingredienti_residui)
    """
    global lista_ricette, dizionario_conversione
    
    # Gli ingredienti devono sempre essere passati come parametro
    if ingredienti_disponibili_input is None:
        raise ValueError("ingredienti disponibili è obbligatorio")
    
    # Il dizionario di conversione deve sempre essere passato come parametro
    if dizionario_conversione_input is None:
        raise ValueError("dizionario conversione è obbligatorio")
    
    # Imposta il dizionario di conversione globale
    dizionario_conversione = dizionario_conversione_input
    
    #!Capire
    ingredienti_da_usare = ingredienti_disponibili_input.copy()
    
    # Esegui l'algoritmo greedy
    risultato = seleziona_ricette(ingredienti_da_usare, lista_ricette)
    
    return risultato, ingredienti_da_usare


# TEST
# Esecuzione diretta per test (quando il file viene eseguito direttamente)
if __name__ == "__main__":
    # Per il test, carica gli ingredienti dal file JSON (solo per testing)
    print("MODALITÀ TEST: Caricamento ingredienti da ingredienti.json per test locale")
    
    # Dizionario di conversione di prova per il test
    dizionario_test = {
        "carrots": {"grams_for_units": 61, "grams_for_cups": 122},
        "potato": {"grams_for_units": 150, "grams_for_cups": 200},
        "celery stalks": {"grams_for_units": 40, "grams_for_cups": 100},
        "onion": {"grams_for_units": 110, "grams_for_cups": 160},
        "tomato": {"grams_for_units": 123, "grams_for_cups": 180}
    }
    
    try:
        with open('modules/ingredienti.json', 'r') as f_ing:
            _pantry = json.load(f_ing)
        
        ingredienti_test = {}
        for item in _pantry.get("data", []):
            nome = item.get("name_ingredient")
            grams = item.get("grams", 0) or 0
            if nome:
                if nome in ingredienti_test:
                    ingredienti_test[nome] += grams
                else:
                    ingredienti_test[nome] = grams
        
        risultato, ingredienti_finali = esegui_greedy(ingredienti_test, dizionario_test)
        
        # Stampa di prova
        if risultato:
            print("Ricette selezionate (in ordine di scelta greedy):")
            for r in risultato:
                print(f" - {r['title']} (punteggio: {r['score']})")
        else:
            print("Nessuna ricetta realizzabile con gli ingredienti.")

        print("\nIngredienti residui dopo la selezione:")
        print(ingredienti_finali)
        
    except FileNotFoundError:
        print("File ingredienti.json non trovato. In produzione, gli ingredienti vengono passati da app.py")
    except Exception as e:
        print(f"Errore durante il test: {e}")
        print("In produzione, gli ingredienti vengono sempre passati da app.py")
