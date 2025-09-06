import json
import random  # Aggiungi l'import di random

"""
1. Get dei valori di conversione per tutti gli ingredienti (grams, cups, units)
    Creo una funzione di conversione che prende l'ingrediente (for ing in ricetta["ingredients"].items()) prende l'unità presente nella ricetta di misura e se:
    - g, mg, kg -> grams, 0.001*grams, 1000*grams
    - cup, cups -> cups
    - medium, large, small, sliced, units, ecc. -> units
    - altro (TBSP, disk, un pizzico, un bicchiere, un pugno, ecc) -> 0
2. Ricetta Realizzabile:
    Confronto se grammi disponibili in dispensa di ogni ingrediente >= grammi richiesti in ricetta dello stesso ingrediente
3. Score:
    Somma dei grammi richiesti per ogni ingrediente che è presente in dispensa
4. Prendo quella con Score più alto
5. Aggiorno dispensa sottraendo i grammi usati
6. Reitero
"""

#TODO Convertire tutto a grammi e conforntare con quelli disponibili
def ricetta_realizzabile(ricetta, disp):
    """Controlla se la ricetta è realizzabile con gli ingredienti """
    flag = False
    for ingrediente, info in ricetta["ingredients"].items():
        quantita_richiesta = info.get("amount", 0) or 0
        unita_richiesta = (info.get("unit") or "").lower()

        # Recupera quantità disponibile a seconda della unit richiesta
        data_ing = disp.get(ingrediente, {})
        if not isinstance(data_ing, dict):  # fallback se struttura non aggiornata
            data_ing = {"grams": data_ing, "cups": 0, "units": 0}

        if unita_richiesta == "medium" or "large" or "small" or "units":
            disponibile = data_ing.get("units", 0)
        else:
            disponibile = 0
            
        if disponibile != 0 and disponibile < quantita_richiesta:
            return False  # ingrediente presente ma non sufficiente
        elif disponibile != 0:
            flag = True  # almeno un ingrediente presente in quantità sufficiente

    return flag

#TODO: Converto tutto in grammi
def calcola_punteggio(ricetta, disp):
    """Punteggio = somma quantità (grammi) richieste per gli ingredienti disponibili (stessa logica unit)."""
    score = 0
    for ing, info in ricetta["ingredients"].items():
        amount = info.get("amount", 0) or 0
        unit_req = (info.get("unit") or "").lower()
        data_ing = disp.get(ing, {})
        if not isinstance(data_ing, dict):
            data_ing = {"grams": data_ing, "cups": 0, "units": 0}
        # Verifica disponibilità sulla unit corretta
        if unit_req == "grams" and data_ing.get("grams", 0) != 0:
            score += amount
        elif unit_req == "cups" and data_ing.get("cups", 0) != 0:
            score += amount
        elif unit_req != "grams" and unit_req != "cups" and data_ing.get("units", 0) != 0:
            score += amount
    return score

#TODO: Aggiorno la dispensa sottrendo SOLO i grammi usati nella ricetta selezionata, cups e units vengono azzerati 
# TODO perche farò un DELETE ALL e un insert con i soli grammi rimasti
def aggiorna_ingredienti(disp, ricetta):
    for ingrediente, info in ricetta["ingredients"].items():
        amount = info.get("amount", 0) or 0
        unit_req = (info.get("unit") or "").lower()
        data_ing = disp.get(ingrediente)
        if not data_ing or not isinstance(data_ing, dict):
            continue
        if unit_req == "grams":
            data_ing["grams"] = max(0, data_ing.get("grams", 0) - amount)
        elif unit_req == "cups":
            data_ing["cups"] = max(0, data_ing.get("cups", 0) - amount)
        else:
            data_ing["units"] = max(0, data_ing.get("units", 0) - amount)


def seleziona_ricette(ingredienti_disponibili, lista_ricette):
    ricette_selezionate = []

    # Per evitare di modificare la lista originale
    ricette_da_valutare = list(lista_ricette)

    while True:
        migliore_punteggio = -float('inf') # -∞
        migliore_ricetta = None
        ricette_migliori = []  # Lista per raccogliere tutte le ricette con punteggio massimo


        # Valuta tutte le ricette realizzabili
        for ricetta in ricette_da_valutare:
            if ricetta_realizzabile(ricetta, ingredienti_disponibili):
                score = calcola_punteggio(ricetta, ingredienti_disponibili)
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



# Carica gli ingredienti disponibili dal file JSON (somma i grammi per ingrediente)
# Struttura attesa di ingredienti.json:
# {
#   "data": [ {"name_ingredient": "carrots", "grams": 1403.0, ...}, ... ],
#   ...
# }
with open('modules/ingredienti.json', 'r') as f_ing:
    _pantry = json.load(f_ing)

#TODO Devo tenere solo i grammi di ogni ingrediente in Pantry
# Dizionario dettagliato: per ogni ingrediente conserva somma di grams, cups e units
ingredienti_dettaglio = {}
for _item in _pantry.get('data', []):
    nome = _item.get('name_ingredient')
    if not nome:
        continue
    entry = ingredienti_dettaglio.setdefault(nome, {
        'grams': 0.0,
        'cups': 0.0,
        'units': 0.0,
    })
    entry['grams'] += (_item.get('grams') or 0)
    entry['cups'] += (_item.get('cups') or 0)
    entry['units'] += (_item.get('units') or 0)

# Dizionario usato dall'algoritmo (struttura completa per unità)
ingredienti_disponibili = ingredienti_dettaglio

# (Opzionale) Debug:
# print('Dettaglio ingredienti:', ingredienti_dettaglio)
# print('Disponibili (grams):', ingredienti_disponibili)


# ===== PARSE DEL JSON =====
with open('modules/recipes.json' , "r") as json_data:
    data = json.load(json_data) 

# Per semplicità, estraiamo la lista di ricette. In questo caso, ne hai solo 1.
ricette_raw = data["recipes"]["results"]

# Vogliamo ottenere una lista di ricette in forma di dizionari come:
# {
#   "title": ...,
#   "ingredients": { "carrots": 300, "celery stalks": 100, ... }
# }

lista_ricette = []
for ricetta_raw in ricette_raw:
    nome_ricetta = ricetta_raw["title"]
    ingredienti_ricetta = {}

    for ing in ricetta_raw["nutrition"]["ingredients"]:
        nome = ing.get("name")
        quantita = ing.get("amount")
        unita = ing.get("unit")
        if not nome:
            continue
        ingredienti_ricetta[nome] = {
            "amount": quantita,
            "unit": unita
        }

    lista_ricette.append({
        "title": nome_ricetta,
        "ingredients": ingredienti_ricetta
    })

risultato = seleziona_ricette(ingredienti_disponibili, lista_ricette)

# Stampa di prova
if risultato:
    print("Ricette selezionate (in ordine di scelta greedyl):")
    for r in risultato:
        print(f" - {r['title']} (punteggio: {r['score']})")
else:
    print("Nessuna ricetta realizzabile con gli ingredienti attuali.")

print("\nIngredienti residui dopo la selezione:")
print(ingredienti_disponibili)
