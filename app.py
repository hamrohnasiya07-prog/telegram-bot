from flask import Flask, jsonify
import requests, datetime

API="https://script.google.com/macros/s/AKfycbzll_uznQE4MYgfjHu4wc26rzlPsR9wPPwj4k761CiOWFKPLf4IcCYfmHveJh_Nxhl5/exec"

app = Flask(__name__)

@app.route("/")
def home():
    return "<h2>CRM Dashboard ishlayapti</h2>"

@app.route("/data")
def data():
    today=datetime.datetime.now().strftime("%Y-%m-%d")
    r=requests.get(API,params={"type":"daily_all","date":today})
    return jsonify(r.json())

app.run(host="0.0.0.0",port=8000)
