from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from marshmallow import Schema, fields, ValidationError
import threading
import requests
import os
import time


app = Flask(__name__)
app.config.from_object(os.environ.get('FLASK_ENV') or 'config.DevelopmentConfig')
db = SQLAlchemy(app)


# Defining the Items model
class Items(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    item = db.Column(db.String(50), nullable=False)
    status = db.Column(db.String(50), nullable=False)


# Defining the Marshmallow schema for validation
class ItemsSchema(Schema):
    item = fields.String(required=True, validate=lambda x: x in ['book', 'pen', 'folder', 'bag'])

# task 1:-
# Defining the API endpoint
@app.route('/items', methods=['POST'])
def add_item():
    # this Parse's the request body
    request_data = request.get_json()

    # Validate's the request body using Marshmallow schema
    try:
        validated_data = ItemsSchema().load(request_data)
    except ValidationError as err:
        return jsonify({'error': err.messages}), 400

    # Insert's the new item into the database
    new_item = Items(item=validated_data['item'], status='pending')
    db.session.add(new_item)
    db.session.commit()

    # Prepare's the response
    response_data = {
        'item': new_item.item,
        'status': new_item.status,
        'id': new_item.id
    }

    # Send's the response with 200 status code
    return jsonify(response_data), 200


# task 2 :-


# Defining a custom Thread class to store the response
class ResponseThread(threading.Thread):
    def __init__(self, delay_value):
        super().__init__()
        self.delay_value = delay_value
        self.response = None

    def run(self):
        url = f'https://httpbin.org/delay/{self.delay_value}'
        self.response = requests.get(url).content

# Defining the API endpoint
@app.route('/trigger', methods=['GET'])
def trigger_requests():
    # Get's the delay_value from the query parameter
    delay_value = request.args.get('delay_value')
    if delay_value is None:
        return jsonify({'error': 'delay_value parameter is required'}), 400

    # Defining the list of threads to trigger the GET requests
    threads = [ResponseThread(delay_value) for i in range(5)]

    # Start's the threads to trigger the GET requests
    start_time = time.time()
    for thread in threads:
        thread.start()

    # Wait's for all threads to complete and collect the response bodies
    response_bodies = []
    for thread in threads:
        thread.join()
        response_bodies.append(thread.response.decode('utf-8'))

    # Calculate's the total time taken for all requests
    time_taken = time.time() - start_time

    # Send the response with 200 status code
    response_data = {'time_taken': f'{time_taken:.2f}', 'response_bodies': response_bodies}
    return jsonify(response_data), 200


if __name__ == '__main__':
    app.run(debug=True)