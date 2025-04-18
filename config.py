from dotenv import load_dotenv
import os

load_dotenv(override=True)

def getBearerToken():
    
    key = os.getenv('BEARER_TOKEN')
    
    return key


def getMySQLUrl():
    
    key = os.getenv('URL_MYSQL')
    
    return key