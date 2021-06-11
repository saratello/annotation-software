#!/usr/bin/env python3
from flask import Flask, request, render_template
import json
import methods
import os
from shutil import rmtree

with open('./config.json') as f:
    config = json.load(f)

USER = config['current_annotator']

gulf_tag_examples = {}
coda_examples = {}
msa_tag_examples = {}


app = Flask(__name__)
# app.run(debug=True)

arrayOfDenoised = []
arrayofTags = []
arrayofTagValues = []

@app.route('/')
def index():
    return render_template('home.html')


@app.route('/annotator/<auth_key>', methods=['GET', 'POST'])
def annotator(auth_key):
    if request.method == 'POST':
        auth_key = request.form['auth_key']
        repo_dir = os.path.join(os.getcwd(), f'annotations')
        global gulf_tag_examples, coda_examples, msa_tag_examples
        resources = methods.clone_repo(repo_dir=repo_dir,
                                       username=config['usernames'][USER],
                                       auth_key=auth_key.strip(),
                                       annotator_name=USER.lower())
        gulf_tag_examples, coda_examples, msa_tag_examples = resources
        
        repo_dir = os.path.join(os.getcwd(), f'annotations')
        texts = methods.get_single_annotations_file(assigned_corpus_index=0,
                                                    repo_dir=repo_dir,
                                                    annotator_name=USER.lower())
        return render_template('index.html', phrases=texts, filtered=False)
    else:
        return 'OK', 200

@app.route('/filteredRes')
def filtered_index():
    filtered = parseFilteredText()
    return render_template('index.html', phrases=filtered, filtered = True)


def parseFilteredText():
    filtered_testsite_array = []
    
    with open(f"./annotations/annotations_{USER.lower()}.json", 'r') as fq:
        try:
            dataaz = json.load(fq)
            for d in dataaz:
                segments = d["segments"]
                for seg in segments:
                    for s in seg:
                        if(s["flag"] == "flag"):
                            filtered_testsite_array.append(d["original"])
                            continue
                        else:
                            continue
        except:
            dataaz = []
    return list(dict.fromkeys(filtered_testsite_array))

@app.route('/getdata/<toSend>', methods=['GET','POST'])
def data_get(toSend):
    
    if request.method == 'POST': 
        print(request.get_text())
        return 'OK', 200
    
    else: 
        with open(f"./annotations/annotations_{USER.lower()}.json", 'r') as fq:
            try:
                dataaz = json.load(fq)
                newData = json.loads(toSend)
                for d in dataaz:
                    if(d["original"] == newData["original"]):
                        newData["raw"] = d["raw"]
                        dataaz.remove(d)
                        break
                dataaz.append(newData)
                with open(f"./annotations/annotations_{USER.lower()}.json", 'w') as f:
                    json.dump(dataaz, f, ensure_ascii = False)
                    return "Success"
            except:
                dataaz = []

@app.route('/getAnnotationStatus/<phrase>', methods=['GET','POST'])
def annotation_get(phrase):
    
    if request.method == 'POST': 
        print(request.get_text())
        return 'OK', 200
    
    else: 
        print(phrase)
        if(checkIfAnnotated(phrase)):
            return "annotated"
        else:
            return "notAnnotated"

@app.route('/getPreviousAnnotations/<phrase>', methods=['GET','POST'])
def previous_annotation_get(phrase):
    
    if request.method == 'POST': 
        print(request.get_text())
        return 'OK', 200
    
    else: 
        print(phrase)
        with open(f"./annotations/annotations_{USER.lower()}.json", 'r') as fq:
            try:
                dataaz = json.load(fq)
                # find specific phrase to load its params
                for d in dataaz:
                    if(d["original"]==phrase):
                        return json.dumps(d)
            except:
                dataaz = []

def checkIfAnnotated(phrase):
    phrasesAnnotated = []
    with open(f"./annotations/annotations_{USER.lower()}.json", 'r') as fq:
        try:
            dataaz = json.load(fq)
            print(dataaz)
            for d in dataaz:
                phrasesAnnotated.append((d["original"]))

            if (phrase in phrasesAnnotated):
                return True
            else:
                return False
        except:
            dataaz = {}            

@app.route('/getSearch/<data>', methods=['GET','POST'])
def get_search(data):
    if request.method == 'POST': 
        print(request.get_text())
        return 'OK', 200
    else: 
        new_data = json.loads(data)
        print(new_data)
        json_response = methods.search_bar_examples(new_data["search_txt0"], gulf_tag_examples, msa_tag_examples, coda_examples, (new_data["search_txt1"], new_data["search_txt2"], new_data["search_txt3"]))
        print(json_response)
        if(new_data["search_txt3"] == "CODA Examples"):
            return json.dumps(json_response)
        else:
            return json_response


@app.route('/getSearchPreviousAnnotations/<data>', methods=['GET', 'POST'])
def get_search_previous_annotations(data):
    if request.method == 'POST':  
        dataaz = methods.get_merged_json(repo_dir=os.path.join(os.getcwd(), f'annotations'),
                                         annotator_name=USER.lower())
        new_data = request.form
        filtered = methods.search_bar_previous_annotations(new_data["search_txt4"], dataaz, (
            new_data["search_txt5"], new_data["search_txt6"], new_data["search_txt7"], new_data["search_txt8"]))
        print(filtered)

        return render_template('index.html', phrases=filtered, filtered=True)
    else:  
        print(request.get_text())
        return 'OK', 200
        

@app.route('/sync/<data>', methods=['GET', 'POST'])
def sync(data):
    if request.method == 'POST':
        return 'OK', 200
    else:
        new_data = json.loads(data)
        methods.sync_annotations(
            repo_dir=os.path.join(os.getcwd(), f'annotations'),
            annotator_name=USER.lower(),
            )

# if os.path.exists('./annotations'):
#     rmtree('./annotations')

if __name__ == '__main__':
    app.run(host='0.0.0.0')
