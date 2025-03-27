import requests
from requests.auth import HTTPDigestAuth

def receipsCore(spoonecularToken):
    url = "https://api.spoonacular.com/recipes/complexSearch"
        
    # Passiamo il token tramite header, ad esempio con "X-Api-Key"

    # Eventuali altri parametri possono essere passati separatamente (es. 'number' per il numero di risultati)
    params = {
        'apiKey': spoonecularToken,
        'number': 100,
        'offset': 200,
        'fillIngredients': True,
    }
    
    # Effettuiamo la richiesta GET, includendo autenticazione digest, headers e parametri
    response = requests.get(url, params=params, verify=True)
    
    if response.ok:
        return response.json()
    
        for key, value in data.items():
            return ("{} : {}".format(key, value))
    else:
        return response.raise_for_status()

