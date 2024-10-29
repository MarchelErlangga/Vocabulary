from flask import Flask, request, render_template, redirect, url_for, jsonify
from pymongo import MongoClient
import requests
from datetime import datetime
from bson import ObjectId
import os
from os.path import join, dirname
from dotenv import load_dotenv

dotenv_path = join(dirname(__file__), '.env')
load_dotenv(dotenv_path)

MONGODB_URI = os.environ.get("MONGODB_URI")
DB_NAME =  os.environ.get("DB_NAME")

client = MongoClient(MONGODB_URI)
db = client[DB_NAME]


app = Flask(__name__)


password = 'sparta'
cxn_str = f'mongodb://test:{password}@cluster0-shard-00-00.czmlq.mongodb.net:27017,cluster0-shard-00-01.czmlq.mongodb.net:27017,cluster0-shard-00-02.czmlq.mongodb.net:27017/?ssl=true&replicaSet=atlas-2vaaub-shard-0&authSource=admin&retryWrites=true&w=majority&appName=Cluster0'
client = MongoClient(cxn_str)

db = client.dbsparta_plus_week2
word_collection = db['words'] 

@app.route('/')
def main():
    words_result = db.words.find({}, {'_id': False})
    words = []
    for word in words_result:
        definition = word['definitions'][0]['shortdef']
        definition = definition if type(definition) is str else definition[0]
        words.append({
            'word': word['word'],
            'definition': definition,
        })
    msg = request.args.get('msg')
    return render_template(
        'index.html',
        words=words, msg=msg
    ) 

@app.route('/detail/<keyword>')
def detail(keyword):
    api_key = '95a007a4-0bc7-45ed-969c-4e57df8d8bda'
    url = f'https://www.dictionaryapi.com/api/v3/references/collegiate/json/{keyword}?key={api_key}'
    response = requests.get(url)
    definitions = response.json()
    if not definitions:
        return render_template(
            'error.html',
            keyword=keyword,
            suggestions=None,
            msg=f'Could not find the word, "{keyword}".'
        )
    
    if type(definitions[0]) is str:
        suggestions = definitions
        return render_template(
            'error.html',
            keyword=keyword,
            suggestions=suggestions,
            msg=f'Could not find the word, "{keyword}", did you mean one of these words?'
        )


    status = request.args.get('status_give', 'new')
    return render_template(
        'detail.html',
        word=keyword,
        definitions=definitions,
        status=status
    )

@app.route('/api/save_word', methods=['POST'])
def save_word():
    json_data = request.get_json()
    word = json_data.get('word_give')
    definitions = json_data.get('definitions_give')
    doc = {
        'word': word,
        'definitions': definitions,
        'date': datetime.now().strftime('%Y%m%d'),
    }
    db.words.insert_one(doc)
    return jsonify({
        'result': 'success',
        'msg': f'the word, {word}, was saved!!!',
    })

@app.route('/api/delete_word', methods=['POST'])
def delete_word():
    word = request.form.get('word_give')
    db.words.delete_one({'word': word})
    db.examples.delete_many({'word': word})
    return jsonify({
        'result': 'success',
        'msg': f'the word {word} was deleted'
    })

@app.route('/api/get_exs', methods=['GET'])
def get_exs():
    word = request.args.get('word_give')
    word_doc = word_collection.find_one({"word": word})
    if word_doc:
        examples = [{"id": str(ex["_id"]), "text": ex["text"]} for ex in word_doc["examples"]]
        return jsonify({'result': 'success', 'examples': examples})
    else:
        return jsonify({'result': 'error', 'message': 'Word not found'})

@app.route('/api/save_ex', methods=['POST'])
def save_ex():
    word = request.form.get('word')
    new_example_text = request.form.get('example_text')
    
    word_collection.update_one(
        {"word": word},
        {"$push": {"examples": {"_id": ObjectId(), "text": new_example_text}}}
    )
    return jsonify({'result': 'success'})

@app.route('/api/delete_ex', methods=['POST'])
def delete_ex():
    word = request.form.get('word')
    ex_id = request.form.get('id')
    
    word_collection.update_one(
        {"word": word},
        {"$pull": {"examples": {"_id": ObjectId(ex_id)}}}
    )
    return jsonify({'result': 'success'})

if __name__ == '__main__':
    app.run('0.0.0.0', port=5000, debug=True)