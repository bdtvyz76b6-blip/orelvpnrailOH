from flask import Flask, request
import json

app = Flask(__name__)


@app.route("/webhook/cashera", methods=["POST"])
def cashera():

    data = request.json

    print("CASHeRA WEBHOOK:")
    print(json.dumps(data, indent=4, ensure_ascii=False))

    return "OK", 200