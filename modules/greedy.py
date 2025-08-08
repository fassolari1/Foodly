def greedy_select_recipes(receips_data, user_ingredients):
    
    #return receips_data

    # Convertiamo la lista di ingredienti dell'utente in un dizionario:
    # Esempio: {"carrots": 2, "tomato": 2}
    stock = {}
    for ing in user_ingredients:
        name = ing["name"].lower()
        stock[name] = stock.get(name, 0) + ing["quantity"]
        
    
    # POSSIBILE strategia di ordinamento: ricette che richiedono
    # la maggior somma di "missedIngredients.amount"
    # (oppure potresti ordinarle dal minor numero di ingredienti da "comprare" al maggiore, ecc.)
    
    # Calcoliamo un peso = somma di "amount" (così priorizziamo ricette che consumano più ingredienti)
    # e salviamo la ricetta insieme al suo "peso".
    receips_with_score = []
    for recipe in receips_data:
        # Somma delle quantità di missedIngredients
        total_amount = sum(mi.get("amount", 0) for mi in recipe.get("missedIngredients", []))
        receips_with_score.append((recipe, total_amount))


    # Ordiniamo in base a total_amount in ordine decrescente
    receips_with_score.sort(key=lambda x: x[1], reverse=True)
    

    selected_recipes = []
    
    # Ora, iteriamo in ordine greedily
    for (recipe, _) in receips_with_score:
        missed_ings = recipe.get("missedIngredients", [])
        # Verifichiamo se possiamo "coprire" tutti gli ingredienti mancanti
        can_prepare = True
        for mi in missed_ings:
            needed_name = mi["name"].lower()  # semplificazione
            needed_amount = int(mi.get("amount", 0))
            if stock.get(needed_name, 0) < needed_amount:
                can_prepare = False
                break
        
            # Se la ricetta si può preparare con gli ingredienti a disposizione, la selezioniamo
            if can_prepare:
                selected_recipes.append(recipe)
                # Aggiorniamo lo stock detraendo le quantità usate

    
    return selected_recipes