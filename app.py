import mysql.connector 
from flask import Flask, jsonify, request
from flask_cors import CORS
from modules.recipes import recipesCore
from modules.greedy import greedy_select_recipes

app = Flask(__name__)
cors = CORS(app, resources={r"/api/*": {"origins": "*"}})

# Definiamo il token atteso (idealmente memorizzato in una variabile d'ambiente per maggiore sicurezza)
VALID_TOKEN = "qwerty"

def validate_bearer_token(auth_header):
    if auth_header and auth_header.startswith("Bearer "):
        token = auth_header.split(" ")[1]
        if token == VALID_TOKEN:
            return token
    return None


@app.route('/api/v1/getGreedy', methods=['POST'])

def sendRequestGreedy():
    auth_header = request.headers.get('Authorization')
    token = validate_bearer_token(auth_header)
    if token is None:
        return jsonify(status='KO', message='Bearer token is not present or invalid', code=401)
    
    data = request.get_json()
    spoonecularToken = data.get('spoonecularToken') if data else None
    
    if not spoonecularToken:
        return jsonify(status='KO', message='Your spoonecular token is missing', code=400)
    
    response = receipsCore(spoonecularToken)
    if response:
        receips_data = response["results"]
        best_set = greedy_select_recipes(receips_data, data.get('user_ing'))
        return jsonify(status='OK', message=best_set)
    else:
        return jsonify(status='KO', message='Something went wrong')
    
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


@app.route('/api/v1/query', methods=['POST'])
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