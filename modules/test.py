import json
import random  # Aggiungi l'import di random


def ricetta_realizzabile(ricetta, disp):
    """
    Controlla se la ricetta è realizzabile con gli ingredienti attualmente disponibili.
    """
    flag = False
    for ingrediente, quantita_richiesta in ricetta["ingredients"].items():
        if (disp.get(ingrediente, 0) < quantita_richiesta) and disp.get(ingrediente, 0) != 0: #ingrediente sicuramente presente ma non in quantità sufficiente
            return False  # Se un ingrediente non è sufficiente, la ricetta non è realizzabile
        elif disp.get(ingrediente, 0) != 0:
            flag = True
    if flag:
        return True
    return False

def calcola_punteggio(ricetta, disp):
    score = 0
    for ing in ricetta["ingredients"]:
        if ing in disp and disp[ing] != 0:
            score += ricetta["ingredients"][ing]
    return score

def aggiorna_ingredienti(disp, ricetta):
    """
    Aggiorna il dizionario degli ingredienti disponibili sottraendo la quantità usata.
    """
    
    for k in disp:
        if(disp.get(k)!=0):
            disp[k] = disp.get(k)-ricetta["ingredients"].get(k,0)
            print(k)
            print(disp[k])

    
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



# Simuliamo un dizionario di ingredienti disponibili (quantità in grammi o ml)
# N.B.: Se abbiamo unità diverse, vanno convertite in un’unità coerente. 
#TODO da passsare nella JSON con la POST
ingredienti_disponibili = {
    "carrots":10,
    "garlic":6
    # grammi
    # Non abbiamo avocado, basilico, microgreens, ecc. Quindi potremmo comunque considerarli 0.
    # Se un ingrediente manca completamente, non potremo realizzare la ricetta se serve >0 di quello.
}

# ===== PARSE DEL JSON =====
with open('modules/recipes.json' , "r") as json_data:
    data = json.load(json_data) 

# Per semplicità, estraiamo la lista di ricette. In questo caso, ne hai solo 1.
ricette_raw = data["receips"]["results"]

# Vogliamo ottenere una lista di ricette in forma di dizionari come:
# {
#   "title": ...,
#   "ingredients": { "carrots": 300, "celery stalks": 100, ... }
# }
# In questo caso useremo "missedIngredients" di Spoonacular 
# perché l'esempio include lì gli ingredienti necessari.

lista_ricette = []
for ricetta_raw in ricette_raw:
    nome_ricetta = ricetta_raw["title"]
    ingredienti_ricetta = {}
    
    for ing in ricetta_raw["missedIngredients"]:
        nome = ing["name"]  # es. "carrots"
        quantita = ing["amount"]  # es. 3.0
        # esempio (carrots,3.0),(tomato,4.0)
        # Per questa demo, assumiamo che "amount" sia già in grammi/ml se lo sappiamo...
        # Spoonacular spesso dà la "unit" (ad es. "cups", "oz", ecc.), e tu dovresti convertire in grammi.
        # In questa esercitazione semplifichiamo e usiamo come se fossero grammi/ml diretti.
        
        # Se l'unità NON è "servings" o "cups", potresti dover gestire conversioni ad hoc.
        # Semplificando: consideriamo quantita come "grammi" o "ml" diretti:
        ingredienti_ricetta[nome] = quantita
    
    lista_ricette.append({
        "title": nome_ricetta,
        "ingredients": ingredienti_ricetta
    })

# ===== ESECUZIONE ALGORITMO GREEDY =====
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
