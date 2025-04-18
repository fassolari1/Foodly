import mysql.connector
import config as config
import mysql.connector
from urllib.parse import urlparse
from flask import Flask, jsonify, request
from flask_cors import CORS
from modules.recipes import recipesCore
from modules.greedy import greedy_select_recipes

app = Flask(__name__)
cors = CORS(app, resources={r"/api/*": {"origins": "*"}})

# Configurazione del database MySQL
url = config.getMySQLUrl()
parsed = urlparse(url)     # Lo parsiamo
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


if __name__ == "__main__":
    app.run(port=8080, debug=True)