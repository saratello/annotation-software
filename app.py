#!/usr/bin/env python3
from flask import Flask, request, jsonify, render_template, send_file
import json
from methods import *
import time

app = Flask(__name__)
# app.run(debug=True)

arrayOfDenoised = []
arrayofTags = []
arrayofTagValues = []
# global json_file
# global phrase_list

@app.route('/')
def index():
    texts = parseText()
    return render_template('index.html', phrases=texts, filtered = False)

@app.route('/filteredRes')
def filtered_index():
    filtered = parseFilteredText()
    return render_template('index.html', phrases=filtered, filtered = True)

def parseText():
    testsite_array = []
    # global phrase_list
    # print(phrase_list)
    with open("phrases.txt") as my_file:
        testsite_array = my_file.readlines()
    
    return testsite_array

def parseFilteredText():
    testsite_array = []
    filtered_testsite_array = []

    with open('phrases.txt') as my_file:
        testsite_array = my_file.readlines()
    
    with open("data.json", 'r') as fq:
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

    # print(filtered_testsite_array)
    # for tex in testsite_array:
    return list(dict.fromkeys(filtered_testsite_array))

@app.route('/getdata/<toSend>', methods=['GET','POST'])
def data_get(toSend):
    
    if request.method == 'POST': # POST request
        print(request.get_text())  # parse as text
        return 'OK', 200
    
    else: # GET request
        # print(toSend)
        
        with open("data.json", 'r') as fq:
            try:
                dataaz = json.load(fq)
                newData = json.loads(toSend)
                for d in dataaz:
                    if(d["original"] == newData["original"]):
                        # ind = dataaz.index(d)
                        newData["raw"] = d["raw"]
                        dataaz.remove(d)
                        # dataaz.append(newData)
                        break
                        # print("The Same We need to Delete")
                dataaz.append(newData)
                with open("data.json", 'w') as f:
                    json.dump(dataaz, f, ensure_ascii = False)
                    return "Success"
            except:
                dataaz = []

@app.route('/getAnnotationStatus/<phrase>', methods=['GET','POST'])
def annotation_get(phrase):
    
    if request.method == 'POST': # POST request
        print(request.get_text())  # parse as text
        return 'OK', 200
    
    else: # GET request
        # print(toSend)
        print(phrase)
        if(checkIfAnnotated(phrase)):
            return "annotated"
        else:
            return "notAnnotated"

        # return "Success"

@app.route('/getPreviousAnnotations/<phrase>', methods=['GET','POST'])
def previous_annotation_get(phrase):
    
    if request.method == 'POST': # POST request
        print(request.get_text())  # parse as text
        return 'OK', 200
    
    else: # GET request
        print(phrase)
        with open("data.json", 'r') as fq:
            try:
                dataaz = json.load(fq)
                # find specific phrase to load it's params
                for d in dataaz:
                    if(d["original"]==phrase):
                        return json.dumps(d)
            except:
                dataaz = []

        # return "Success"

def checkIfAnnotated(phrase):
    phrasesAnnotated = []
    with open("data.json", 'r') as fq:
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
    if request.method == 'POST': # POST request
        print(request.get_text())  # parse as text
        return 'OK', 200
    else: # GET request
        new_data = json.loads(data)
        print(new_data)
        json_response = search_bar_examples(new_data["search_txt0"], gulf_tag_examples, msa_tag_examples, coda_examples, (new_data["search_txt1"], new_data["search_txt2"], new_data["search_txt3"]))
        print(json_response)
        if(new_data["search_txt3"] == "CODA Examples"):
            return json.dumps(json_response)
        else:
            return json_response

    print(json_response)

# @app.route('/inituser/<user>', methods=['GET','POST'])
# def initUser(user):
#     print(user)

#     global phrase_list
#     global json_file

#     json_file = user+".json"
#     print("USER IS : ",user)
#     if(user == "christian"):
#         phrase_list = "./corpus/shami_0.txt"
#     elif(user == "carine"):
#         phrase_list = "./corpus/shami_1.txt"
#     elif(user == "wiaam"):
#         phrase_list = "./corpus/shami_2.txt"
#     elif(user == "sara"):
#         phrase_list = "./corpus/shami_3.txt"
#     print(phrase_list)

#     return "OK"

# @app.route('/begin')
# def begin():
#     time.sleep(1)

@app.route('/download')
def download():
    return send_file("./data.json", as_attachment=True, cache_timeout=0)

with open('gulf_tag_examples.json') as f_gulf, \
    open('coda_examples.json') as f_coda, \
    open('msa_tag_examples.json') as f_msa:
        gulf_tag_examples = json.load(f_gulf)
        coda_examples = json.load(f_coda)
        msa_tag_examples = json.load(f_msa)

if __name__ == '__main__':
    app.run(host='0.0.0.0')