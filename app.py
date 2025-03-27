from flask import Flask, jsonify, request
from flask_cors import CORS
from modules.receips import receipsCore
from modules.greeady import greedy_select_recipes

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


@app.route('/api/v1/getGreeady', methods=['POST'])

def sendRequestGreeady():
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
    
@app.route('/api/v1/getReceips', methods=['POST'])

def sendRequest():
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
        return jsonify(status='OK', receips=response)
    else:
        return jsonify(status='KO', message='Something went wrong')

if __name__ == "__main__":
    app.run(port=8080, debug=True)