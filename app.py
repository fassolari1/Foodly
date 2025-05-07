import mysql.connector
import config as config
import mysql.connector
from urllib.parse import urlparse
from flask import Flask, jsonify, request, session
from flask_cors import CORS
from modules.recipes import recipesCore
from modules.greedy import greedy_select_recipes

app = Flask(__name__)
app.secret_key = "ajhaskjchksjdhcakjdhcjkashk" # Chiave segreta per le sessioni #TODO: Cambiare in produzione
cors = CORS(app, resources={r"/api/*": {"origins": "*"}})

#Configurazione del database MySQL
url = config.getMySQLUrl()
parsed = urlparse(url)     #Lo "parsiamo"
mydb = mysql.connector.connect(
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

    mycursor = mydb.cursor()
    try:
        mycursor.execute("INSERT INTO users (name, surname, email, password) VALUES (%s, %s, %s, %s)", (name, surname, email, password))
        mydb.commit() #chiusura dell'inserimento

    except mysql.connector.Error as err:
        if err.errno == 1062: # Duplicate entry error
            return jsonify(status='KO', message='Email already exists', code=409) #409 codice di conflitto
        else:
            return jsonify(status='KO', message='Database error: {}'.format(err), code=500) #500 codice di errore interno
    except Exception as e:
        return jsonify(status='KO', message='An error occurred: {}'.format(e), code=500)
    
    mycursor.close()
    return jsonify(status='OK', message='Registration completed successfully')


#chiamata di Test per utenti
@app.route('/api/v1/testUsers', methods=['POST'])
def test():
    mydb = mysql.connector.connect(
    host="foodlydb.cdyqekyui42m.eu-north-1.rds.amazonaws.com",
    user="admin",
    password="xinvUq-fygwa6-sibfih",
    database="foodly"
    )

    mycursor = mydb.cursor()
    mycursor.execute("SELECT * FROM users")
    myresult = mycursor.fetchall()

    return jsonify(myresult)


# Login: controlla se l'email e la password sono corrette
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
    
    mycursor = mydb.cursor()
    try:
        # Verifica se l'email esiste
        mycursor.execute("SELECT * FROM users WHERE email = %s", (email,))
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
        # Salva le informazioni dell'utente nella sessione
        session['id_user'] = user_with_password[0]  # Supponendo che il primo campo sia l'ID utente
        session['email'] = user_with_password[3]    # Supponendo che il quarto campo sia l'email

        # Converti i risultati in un dizionario chiave-valore
        # TODO evita che ritorni la password
        column_names = [desc[0] for desc in mycursor.description]
        user_dict = dict(zip(column_names, user_with_password))
        
        return jsonify(status='OK', message='Login successful', user=user_dict)
    
    except mysql.connector.Error as err:
        return jsonify(status='KO', message=f'Database error: {err}', code=500)
    
    finally:
        mycursor.close()  # Chiudi il cursore


@app.route('/api/v1/GetProfile', methods=['GET'])
def get_profile():
    if 'id_user' not in session:
        return jsonify(status='KO', message='User not logged in', code=401)
    
    id_user = session['id_user']
    email = session['email']
    
    # Esegui una query per recuperare il profilo dell'utente
    mycursor = mydb.cursor()
    try:
        mycursor.execute("SELECT * FROM users WHERE id = %s AND email = %s", (id_user, email))
        user = mycursor.fetchone()  # Ritorna la prima riga o None
        if user is None:
            return jsonify(status='KO', message='User not found', code=404)
        
        # Converti i risultati in un dizionario chiave-valore
        # TODO evita che ritorni la password
        column_names = [desc[0] for desc in mycursor.description]
        user_dict = dict(zip(column_names, user))
        
        return jsonify(status='OK', message='User profile retrieved', user=user_dict)
    
    except mysql.connector.Error as err:
        return jsonify(status='KO', message=f'Database error: {err}', code=500)
    
    finally:
        mycursor.close()  # Chiudi il cursore


@app.route('/api/v1/GetPantry', methods=['GET'])
def get_Pantry():
    if 'id_user' not in session:
        return jsonify(status='KO', message='User not logged in', code=401)
    
    id_user = session['id_user']
    
    # Esegui una query per recuperare la dispensa dell'utente
    mycursor = mydb.cursor()
    try:
        mycursor.execute("SELECT * FROM pantry WHERE id_user = %s", (id_user,))
        rows = mycursor.fetchall()
        if not rows:
            return jsonify(status='KO', message='No ingredients found in pantry', code=404)
        
        # Converti i risultati in un dizionario chiave-valore
        column_names = [desc[0] for desc in mycursor.description]
        pantry = [dict(zip(column_names, row)) for row in rows]
        
        return jsonify(status='OK', message='Pantry retrieved', id_user=id_user, pantry=pantry)
    
    except mysql.connector.Error as err:
        return jsonify(status='KO', message=f'Database error: {err}', code=500)
    
    finally:
        mycursor.close()


#COMPLETE: Login, Get Profile (dell'utente passato tramite ID, loggato), GetPantry
#TODO: Greedy, SerchIndedients(query: SELECT * FROM ingredients WHERE name LIKE 'VAR%')
#(?) DB: AGGIUNGERE Grammi a PANTRY, aggiungere ShoppingList
#TODO

if __name__ == "__main__":
    app.run(port=8080, debug=True)