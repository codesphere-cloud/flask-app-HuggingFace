from flask import Flask, jsonify, request
import requests
from bs4 import BeautifulSoup
import json
import os
import re
import nltk
from nltk.corpus import words, stopwords
from huggingface_hub import ModelCard

nltk.download('stopwords')
nltk.download('words')

app = Flask(__name__)

def clean_text(text):
    # Entferne escaped characters
    text = re.sub(r'\\.', ' ', text)

    # Entferne Links
    text = re.sub(r'http\S+|www\S+|https\S+', '', text, flags=re.MULTILINE)

    # Entferne alles zwischen ``` und ```
    text = re.sub(r'```.*?```', '', text, flags=re.DOTALL)

    # Entferne Wörter aus zwei Buchstaben, die keine Stopwords in Englisch sind
    stop_words = set(stopwords.words('english'))
    words = text.split()
    words = [word for word in words if len(word) > 2 or word.lower() in stop_words]

    # Setze die bereinigten Wörter wieder zu einem Text zusammen
    clean_text = ' '.join(words)
	
	# Entferne übrige Sonderzeichen
    clean_text = re.sub(r'[^A-Za-z0-9\s]', '', clean_text)
	
	# Entferne führende und abschließende Leerzeichen
    clean_text = clean_text.strip()

    return clean_text

@app.route('/get_trending_models', methods=['GET'])
def get_trending_models():
    url = 'https://huggingface.co/models?sort=trending'
    response = requests.get(url)

    if response.status_code == 200:
        html_content = response.text
        soup = BeautifulSoup(html_content, 'html.parser')

        trending_models = []

        # Extrahiere die Namen und Links der ersten 10 Modelle
        model_cards = soup.find_all('article', class_='overview-card-wrapper')
        for card in model_cards[:10]:
            model_info = {}
            model_info['name'] = card.find('h4', class_='text-md').text.strip()
            model_info['link'] = 'https://huggingface.co' + card.find('a')['href']           

            trending_models.append(model_info)

        return jsonify(trending_models)
    else:
        return jsonify({'error': f"Fehler beim Abrufen der Seite. Statuscode: {response.status_code}"})


@app.route('/get_model_card', methods=['GET'])
def get_model_card():
    model_name = request.args.get('model_name')

    if not model_name:
        return jsonify({'error': 'Modellname fehlt in der Anfrage'})

    try:
        card = ModelCard.load(model_name)
        model_card_content = card.content

        # Extrahiere die ersten 100 Wörter
        words = model_card_content.split()
        model_card_content_first_100_words = ' '.join(words[:600])

        # Entfernen Sie die Zeichen, die für JSON-Zeichen entkommen müssen
        model_card_content_without_escaped_chars = clean_text(model_card_content_first_100_words)
        
		
		
        response_data = {
            'text': model_card_content_without_escaped_chars
        }

        return jsonify(response_data)
    except Exception as e:
        return jsonify({'error': f"Fehler beim Laden der Model Card: {str(e)}"})

	
if __name__ == '__main__':
    app.run(debug=True, port=3000)
