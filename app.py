import mysql.connector
import config as config
import mysql.connector
from urllib.parse import urlparse
from flask import Flask, jsonify, request
from flask_cors import CORS
from modules.recipes import recipesCore
import json
from modules.greedy import esegui_greedy


app = Flask(__name__)
app.secret_key = "ajhaskjchksjdhcakjdhcjkashk" # Chiave segreta per le sessioni #TODO: Cambiare in produzione
cors = CORS(app, resources={r"/api/*": {"origins": "*"}})
with open('modules/recipes.json' , "r") as json_data:
    data = json.load(json_data) 
#Configurazione del database MySQL
def get_db_connection():
    url = config.getMySQLUrl()
    parsed = urlparse(url)  # Lo "parsiamo"
    return mysql.connector.connect(
        host=parsed.hostname,
        port=parsed.port or 3306,
        user=parsed.username,
        password=parsed.password,
        database=parsed.path.lstrip('/')
    )


def validate_bearer_token(auth_header):
    if auth_header and auth_header.startswith("Bearer "):
        token = auth_header.split(" ")[1]
        if token == config.getBearerToken():
            return token
    return None

def get_pantry_data(id_user):
    """
    Funzione helper per recuperare i dati della dispensa dell'utente.
    Utilizzata sia da get_Pantry() che da run_greedy().
    Include il nome dell'ingrediente tramite JOIN con la tabella ingredients.
    
    Args:
        id_user (int): ID dell'utente
        
    Returns:
        dict: Risultato con status, message e data (come get_Pantry)
    """
    try:
        mydb = get_db_connection()
        mycursor = mydb.cursor()
        
        # Query con JOIN per includere il nome dell'ingrediente
        mycursor.execute("SELECT * FROM pantry WHERE id_user = %s", (id_user,))
        rows = mycursor.fetchall()
        
        if not rows:
            return {
                "status": "OK", 
                "message": "No ingredients found in pantry", 
                "data": []
            }
        
        # Converti i risultati in un dizionario chiave-valore
        column_names = [desc[0] for desc in mycursor.description]
        pantry = [dict(zip(column_names, row)) for row in rows]
        
        return {
            "status": "OK", 
            "message": "Pantry retrieved", 
            "data": pantry
        }
        
    except mysql.connector.Error as err:
        return {
            "status": "KO", 
            "message": f"Database error: {err}", 
            "data": []
        }
    finally:
        mycursor.close()

@app.route('/api/v1/getRecipes', methods=['POST'])
def sendRequest():
    auth_header = request.headers.get('Authorization')
    token = validate_bearer_token(auth_header)
    if token is None:
        return jsonify(status='KO', message='Bearer token is not present or invalid', code=401)
    
    data = request.get_json()
    spoonecularToken = data.get('spoonecularToken') if data else None
    
    if not spoonecularToken:
        return jsonify(status='KO', message='Your spoonecular token is missing', code=400)
    
    response = recipesCore(spoonecularToken)
    if response:
        return jsonify(status='OK', receips=response)
    else:
        return jsonify(status='KO', message='Something went wrong')


@app.route('/api/v1/Registration', methods=['POST'])
def registration():
    auth_header = request.headers.get('Authorization')
    token = validate_bearer_token(auth_header)
    if token is None:
        return jsonify(status='KO', message='Bearer token is not present or invalid', code=401)

    data = request.get_json()
    if not data:
        return jsonify(status='KO', message='Your data is missing', code=400)
    name = data.get('name')
    surname = data.get('surname')
    email = data.get('email')
    password = data.get('password')
    if not name or not surname or not email or not password:
        return jsonify(status='KO', message='Your data is missing', code=400)

    mydb = get_db_connection()
    mycursor = mydb.cursor()
    try:
        mycursor.execute("INSERT INTO users (name, surname, email, password) VALUES (%s, %s, %s, %s)", (name, surname, email, password))
        mydb.commit() #chiusura dell'inserimento
        
        # Recupera l'ID dell'utente appena inserito
        user_id = mycursor.lastrowid
        user_dict = {
            'id': user_id,
            'name': name,
            'surname': surname,
            'email': email
        }
        
        mycursor.close()
        return jsonify(status='OK', message='Registration completed successfully', data=user_dict)

    except mysql.connector.Error as err:
        mycursor.close()
        if err.errno == 1062: # Duplicate entry error
            return jsonify(status='KO', message='Email already exists') #409 codice di conflitto
        else:
            return jsonify(status='KO', message='Database error: {}'.format(err)) #500 codice di errore interno
    except Exception as e:
        mycursor.close()
        return jsonify(status='KO', message='An error occurred: {}'.format(e))

# Login: controlla se l'email e la password sono corretti
@app.route('/api/v1/Login', methods=['POST'])
def login():
    auth_header = request.headers.get('Authorization')
    token = validate_bearer_token(auth_header)
    
    if token is None:
        return jsonify(status='KO', message='Bearer token is not present or invalid', code=401)
    
    data = request.get_json()
    if not data:
        return jsonify(status='KO', message='Your data is missing', code=400)
    
    email = data.get('email')
    password = data.get('password')
    
    if not email:
        return jsonify(status='KO', message='Missing email', code=400)
    if not password:
        return jsonify(status='KO', message='Missing password', code=400)
    
    mydb = get_db_connection()
    mycursor = mydb.cursor()
    try:
        # Verifica se l'email esiste
        mycursor.execute("SELECT * FROM users WHERE email LIKE %s", (email,))
        user = mycursor.fetchone()  # Ritorna la prima riga o None
        
        if user is None:
            # L'email non esiste
            return jsonify(status='KO', message='Invalid email', code=401)
        
        # Verifica la password
        mycursor.execute("SELECT * FROM users WHERE email = %s AND BINARY password = %s", (email, password))
        # Utilizza BINARY per confrontare le password in modo case-sensitive
        user_with_password = mycursor.fetchone()
        
        if user_with_password is None:
            # L'email esiste ma la password è sbagliata
            return jsonify(status='KO', message='Invalid password', code=401)
        
        # Login riuscito
        # Converti i risultati in un dizionario chiave-valore
        # evita che ritorni la password
        column_names = [desc[0] for desc in mycursor.description]
        user_dict = dict(zip(column_names, user_with_password))
        
        return jsonify(status='OK', message='Login successful', data=user_dict)
    
    except mysql.connector.Error as err:
        return jsonify(status='KO', message=f'Database error: {err}', code=500)
    
    finally:
        mycursor.close()  # Chiudi il cursore


@app.route('/api/v1/GetProfile', methods=['GET'])
def get_profile():
    id_user = request.args.get('id_user')
    if not id_user:
        return jsonify(status='KO', message='Missing id_user', code=400)
    mydb = get_db_connection()
    mycursor = mydb.cursor()
    try:
        mycursor.execute("SELECT id, name, surname, email FROM users WHERE id = %s", (id_user,))
        user = mycursor.fetchone()  # Ritorna la prima riga o None
        if user is None:
            return jsonify(status='KO', message='User not found', code=404)
        
        # Converti i risultati in un dizionario chiave-valore
        column_names = [desc[0] for desc in mycursor.description]
        user_dict = dict(zip(column_names, user))
        
        return jsonify(status='OK', message='User profile retrieved', data=user_dict)
    
    except mysql.connector.Error as err:
        return jsonify(status='KO', message=f'Database error: {err}', code=500)
    
    finally:
        mycursor.close()  # Chiudi il cursore

# GetIngredients: ritorna tutti gli ingredienti dalla tabella ingredients
@app.route('/api/v1/GetIngredients', methods=['GET'])
def get_ingredients():
    auth_header = request.headers.get('Authorization')
    token = validate_bearer_token(auth_header)
    
    if token is None:
        return jsonify(status='KO', message='Bearer token is not present or invalid', code=401)
    
    mydb = get_db_connection()
    mycursor = mydb.cursor()
    try:
        mycursor.execute("SELECT * FROM ingredients")
        rows = mycursor.fetchall()
        
        if not rows:
            return jsonify(status='KO', message='No ingredients found', code=404)
        
        # Converti i risultati in un dizionario chiave-valore
        column_names = [desc[0] for desc in mycursor.description]
        ingredients = [dict(zip(column_names, row)) for row in rows]
        
        return jsonify(status='OK', message='Ingredients retrieved', data=ingredients)
    
    except mysql.connector.Error as err:
        return jsonify(status='KO', message=f'Database error: {err}', code=500)
    
    finally:
        mycursor.close()

# TODO togliere id esterno nella risposta
@app.route('/api/v1/GetPantry', methods=['GET'])
def get_Pantry():
    id_user = request.args.get('id_user')
    if not id_user:
        return jsonify(status='KO', message='Missing id_user')
    
    # Utilizza la funzione helper per recuperare i dati
    result = get_pantry_data(id_user)
    
    return jsonify(
        status=result["status"], 
        message=result["message"], 
        data=result["data"]
    )

# Add Pantry with user id, ingredient id and grams
@app.route('/api/v1/AddPantry', methods=['POST'])
def add_pantry():
    data = request.get_json()
    if not data:
        return jsonify(status='KO', message='Your data is missing')
    id_user = data.get('id_user')
    id_ingredient = data.get('id_ingredient')
    grams = data.get('grams')
    units = data.get('units')
    if not id_user:
        return jsonify(status='KO', message='Missing id_user')
    if not id_ingredient:
        return jsonify(status='KO', message='Missing id_ingredient')
    if not grams and not units:
        return jsonify(status='KO', message='Insert grams or units')
    elif grams is None and units is not None:
        default_value = 'units' #setto il default_value: per la visualizzazione a frontend dell'unità di misura
    else:
        default_value = 'g'
    
    mydb = get_db_connection()
    mycursor = mydb.cursor()
    try:
        mycursor.execute("INSERT INTO pantry (id_user, id_ingredient, units, grams, default_value) VALUES (%s, %s, %s, %s, %s)", (id_user, id_ingredient, units, grams, default_value))
        mydb.commit() #chiusura dell'inserimento
        return jsonify(status='OK', message='Ingredient added to pantry successfully')
    
    except mysql.connector.Error as err:
        return jsonify(status='KO', message=f'Database error: {err}')
    
    finally:
        mycursor.close()

# Delete Pantry with user id and optional ingredient id or Delete ALL ingredients for that user
@app.route('/api/v1/DeletePantry', methods=['DELETE'])
def delete_pantry():
    auth_header = request.headers.get('Authorization')
    token = validate_bearer_token(auth_header)
    if token is None:
        return jsonify(status='KO', message='Bearer token is not present or invalid', code=401)
    data = request.get_json()
    if not data:
        return jsonify(status='KO', message='Your data is missing', code=400)
    
    id_user = data.get('id_user')
    ingredient_id = data.get('id_ingredient')
    if not id_user:
        return jsonify(status='KO', message='Missing id_user', code=400)
    
    mydb = get_db_connection()
    mycursor = mydb.cursor()
    try:
        if ingredient_id is not None:
            # Delete specific ingredient from user's pantry
            mycursor.execute("DELETE FROM pantry WHERE id_user = %s AND id_ingredient = %s", (id_user, ingredient_id))
        else:
            # DELETE ALL ingredients from user's pantry
            mycursor.execute("DELETE FROM pantry WHERE id_user = %s", (id_user,))
        mydb.commit()
        #Controlla quante righe sono state effettivamente eliminate
        affected_rows = mycursor.rowcount
        if affected_rows > 0:
            return jsonify(status='OK', message='Ingredients deleted successfully', affected_rows=affected_rows)
        else:
            return jsonify(status='OK', message='No ingredients found to delete')
    except mysql.connector.Error as err:
        return jsonify(status='KO', message=f'Database error: {err}', code=500)
    finally:
        mycursor.close()

@app.route('/api/v1/GetGreedyRecipes', methods=['GET'])
def get_greedy_recipes():
    # Recupera l'id_user dai parametri GET
    id_user = request.args.get('id_user')
    if not id_user:
        return jsonify(status='KO', message='Missing id_user')

    # Recupera gli ingredienti utilizzando get_pantry_data() (stessa logica di get_Pantry)
    pantry_result = get_pantry_data(id_user)
    
    if pantry_result["status"] != "OK":
        return jsonify(status='KO', message=pantry_result["message"])
    
    if not pantry_result["data"]:
        return jsonify(status='KO', message='No ingredients found in pantry for this user')
    
    # Converte i dati della dispensa nel formato richiesto da test_2.py
    ingredienti_disponibili = {}
    for item in pantry_result["data"]:
        nome = item.get("name_ingredient")
        grams = item.get("grams", 0) or 0
        
        if nome and grams > 0:
            if nome in ingredienti_disponibili:
                ingredienti_disponibili[nome] += grams
            else:
                ingredienti_disponibili[nome] = grams

    if not ingredienti_disponibili:
        return jsonify(status='KO', message='No ingredients with grams found in pantry')

    # Recupera il dizionario di conversione dal database
    try:
        mydb = get_db_connection()
        mycursor = mydb.cursor()
        
        # Query per recuperare i dati di conversione dalla tabella ingredients
        mycursor.execute("SELECT name, grams_for_units, grams_for_cups FROM ingredients")
        rows = mycursor.fetchall()
        
        # Crea il dizionario di conversione
        dizionario_conversione = {}
        for row in rows:
            name, grams_for_units, grams_for_cups = row
            dizionario_conversione[name] = {
                "grams_for_units": grams_for_units or 0,
                "grams_for_cups": grams_for_cups or 0
            }
        
        mycursor.close()
        mydb.close()
        
    except mysql.connector.Error as err:
        return jsonify(status='KO', message=f'Database error retrieving conversion data: {err}')

    # Esegui l'algoritmo Greedy
    try:
        risultato, ingredienti_residui = esegui_greedy(ingredienti_disponibili, dizionario_conversione)
        
        return jsonify(
            status='OK',
            message='Greedy algorithm executed successfully',
            ricette_selezionate=risultato,
            ingredienti_residui=ingredienti_residui
        )
        
    except Exception as e:
        return jsonify(status='KO', message=f'Error executing greedy algorithm: {str(e)}')

    except FileNotFoundError:
        return jsonify(status='KO', message='recipes.json file not found')
    except Exception as e:
        return jsonify(status='KO', message=f'An error occurred: {e}')
    
    #TODO (fac.) infine chiamata a deletePantry 
    # e AddPantry per aggiungere i residui alla dispensa dell'utente però un po inutile perché se non ha trovato 


# SerchIndedients(query: SELECT * FROM ingredients WHERE name LIKE 'VAR%')
@app.route('/api/v1/SearchIngredients', methods=['GET'])
def search_ingredients():
    auth_header = request.headers.get('Authorization')
    token = validate_bearer_token(auth_header)
    
    if token is None:
        return jsonify(status='KO', message='Bearer token is not present or invalid', code=401)
    
    query = request.args.get('query')
    if not query:
        return jsonify(status='KO', message='Query parameter is missing', code=400)
    mydb = get_db_connection()
    mycursor = mydb.cursor()
    try:
        mycursor.execute("SELECT * FROM ingredients WHERE name LIKE %s", (f"%{query}%",))
        rows = mycursor.fetchall()
        
        if not rows:
            return jsonify(status='KO', message='No ingredients found', code=404)
        
        # Converti i risultati in un dizionario chiave-valore
        column_names = [desc[0] for desc in mycursor.description]
        ingredients = [dict(zip(column_names, row)) for row in rows]
        
        return jsonify(status='OK', message='Ingredients found', data=ingredients)
    
    except mysql.connector.Error as err:
        return jsonify(status='KO', message=f'Database error: {err}', code=500)
    
    finally:
        mycursor.close()

#TODO: add_selected_recipe(id_recipe, id_user)
# quando si sceglie una ricetta, si salva sia la corrispondenza in "selected_recipes" sia i dati nutrizionali in "recipes_data" e si fa una chimata diretta a quella tabella per avere i macronutrienti
@app.route('/api/v1/AddSelectedRecipe', methods=['POST'])
def add_selected_recipe():
    data = request.get_json()
    if not data:
        return jsonify(status='KO', message='Missing data', code=400)
    id_recipe = data.get('id_recipe')
    id_user = data.get('id_user')
    if not id_recipe or not id_user:
        return jsonify(status='KO', message='Missing id_recipe or id_user', code=400)
    mydb = get_db_connection()
    mycursor = mydb.cursor()
    try:
        # Inserisci relazione in selected_recipes con la data corrente
        mycursor.execute("INSERT INTO selected_recipes (id_recipe, id_user, date) VALUES (%s, %s, NOW())", (id_recipe, id_user))
        mydb.commit()
        
        # Verifica se la ricetta è già presente in recipes_data
        mycursor.execute("SELECT id_recipe FROM recipes_data WHERE id_recipe = %s", (id_recipe,))
        exists = mycursor.fetchone()
        if not exists:
            # Carica recipes.json e cerca la ricetta
            with open('modules/recipes.json', 'r') as f:
                data_json = json.load(f)
            ricette = data_json.get('receips', {}).get('results', [])
            ricetta = next((r for r in ricette if str(r.get('id')) == str(id_recipe)), None)
            if not ricetta:
                return jsonify(status='KO', message='Recipe not found in JSON', code=404)
            nutr = ricetta.get('nutrition', {})
            nutrients = nutr.get('nutrients', [])
            def get_nutrient(name):
                for n in nutrients:
                    if n.get('name') == name:
                        return n.get('amount')
                return None
            calories = get_nutrient('Calories')
            protein = get_nutrient('Protein')
            fat = get_nutrient('Fat')
            saturated_fat = get_nutrient('Saturated Fat')
            carbohydrates = get_nutrient('Carbohydrates')
            fiber = get_nutrient('Fiber')
            sugar = get_nutrient('Sugar')
            sodium = get_nutrient('Sodium')
            vegetarian = ricetta.get('vegetarian')
            vegan = ricetta.get('vegan')
            gluten_free = ricetta.get('glutenFree')
            healty_score = ricetta.get('healthScore')
            mycursor.execute("""
                INSERT INTO recipes_data (id_recipe, calories, protein, fat, saturated_fat, carbohydrates, fiber, sugar, sodium, vegetarian, vegan, gluten_free ,healty_score)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (id_recipe, calories, protein, fat, saturated_fat, carbohydrates, fiber, sugar, sodium, vegetarian, vegan, gluten_free, healty_score))
            mydb.commit()
        return jsonify(status='OK', message='Recipe added to selected_recipes and recipes_data')
    except mysql.connector.Error as err:
        return jsonify(status='KO', message=f'Database error: {err}', code=500)
    except Exception as e:
        return jsonify(status='KO', message=f'Error: {e}', code=500)
    finally:
        mycursor.close()


# GetRecipes_Data: (Kcal, Proteine, Grassi, Carboidrati, Fibre, Sodio) per ogni ricetta
@app.route('/api/v1/GetRecipe_Data', methods=['GET'])
def get_recipe_data():
    id_recipe = request.args.get('id_recipe')
    if not id_recipe:
        return jsonify(status='KO', message='Missing id_recipe', code=400)
    mydb = get_db_connection()
    mycursor = mydb.cursor()
    try:
        mycursor.execute("""
            SELECT calories, protein, fat, saturated_fat, carbohydrates, fiber, sugar, sodium, vegetarian, vegan, gluten_free
            FROM recipes_data WHERE id_recipe = %s
        """, (id_recipe))
        row = mycursor.fetchone()
        if not row:
            return jsonify(status='KO', message='Recipe not found in recipes_data', code=404)
        keys = ['calories', 'protein', 'fat', 'saturated_fat', 'carbohydrates', 'fiber', 'sugar', 'sodium', 'vegetarian', 'vegan', 'gluten_free']
        nutr_data = dict(zip(keys, row))
        return jsonify(status='OK', id_recipe=id_recipe, data=nutr_data)
    except mysql.connector.Error as err:
        return jsonify(status='KO', message=f'Database error: {err}', code=500)
    finally:
        mycursor.close()

#TODO: GetRecipes_Data: (Kcal, Proteine, Grassi, Carboidrati, Fibre, Sodio) per ogni ricetta
    # seconda chimata: somma e media di kcal, healtry score per ogni ricetta (ciclo for) delle ricette selezionate nell'ultima settimane
    # ! si calcolano medie ecc. dal DB selected_recipes, oppure si effettua una chiamata al get_recipes_data 
@app.route('/api/v1/GetRecipes_Statistic', methods=['GET'])
def get_recipes_statistic():
    id_user = request.args.get('id_user')
    if not id_user:
        return jsonify(status='KO', message='Missing id_user', code=400)
    mydb = get_db_connection()
    mycursor = mydb.cursor()
    try:
        # Prendi tutti gli id_recipe selezionati dall'utente nell'ultima settimana
        mycursor.execute("""
            SELECT id_recipe FROM selected_recipes
            WHERE id_user = %s AND date >= DATE_SUB(NOW(), INTERVAL 7 DAY)
        """, (id_user,))
        rows = mycursor.fetchall()
        if not rows:
            return jsonify(status='OK', message='No recipes selected in the last week', data={})
        
        recipe_ids = [row[0] for row in rows]
        # Per ogni id_recipe, prendi i dati nutrizionali dalla tabella recipes_data
        macronutrienti = ['calories', 'protein', 'fat', 'saturated_fat', 'carbohydrates', 'fiber', 'healty_score']
        stats = {k: [] for k in macronutrienti}
        for rid in recipe_ids:
            mycursor.execute("""
                SELECT calories, protein, fat, saturated_fat, carbohydrates, fiber, healty_score
                FROM recipes_data WHERE id_recipe = %s
            """, (rid,))
            row = mycursor.fetchone()
            if row:
                for i, k in enumerate(macronutrienti):
                    value = row[i]
                    if value is not None:
                        stats[k].append(float(value))
        # Calcola la media per ogni macronutriente
        media = {}
        for k in macronutrienti:
            values = stats[k]
            media[k] = sum(values) / len(values) if values else None
        return jsonify(status='OK', message='OK', data={
            'id_user' : id_user,
            'recipes' : len(recipe_ids),
            'average' : media
        })
    except mysql.connector.Error as err:
        return jsonify(status='KO', message=f'Database error: {err}', code=500)
    except Exception as e:
        return jsonify(status='KO', message=f'Error: {e}', code=500)
    finally:
        mycursor.close()


#TODO: LE ricette di oggi in Ricette
    #Passare random TOT ricette

#TODO in ricette si può mettere:
    # Sommario
    # Tipo di cucina (mediterranea, cinese, ecc.)
    # dettagli di dieta (vegan, vegetariana, gluten free)
    # Fasi di preparazione

    
if __name__ == "__main__":
    app.run(port=8080, debug=True)