import os
from flask import Flask, request, jsonify, abort
from sqlalchemy import exc
import json
from flask_cors import CORS

from .database.models import db_drop_and_create_all, setup_db, Drink
from .auth.auth import AuthError, requires_auth

app = Flask(__name__)
setup_db(app)
CORS(app)

db_drop_and_create_all()


# ROUTES

@app.route('/drinks', methods=['GET'])
# Implement endpoint GET /drinks
def get_drinks():
    """ Public permission"""
    drinks = Drink.query.all()

    return jsonify({
        'success': True,
        'drinks': [drink.short() for drink in drinks]
    }), 200


@app.route('/drinks-detail')
@requires_auth('get:drinks-detail')
def get_drink_detail(token):
    drinks = Drink.query.all()

    return jsonify({
        'success': True,
        'drinks': [drink.long() for drink in drinks]
    }), 200


@app.route('/drinks', methods=['POST'])
@requires_auth('post:drinks')
def create_drink(token):
    if request.data:
        new_drink_data = json.loads(request.data.decode('utf-8'))
        new_drink = Drink(title=new_drink_data['title'], recipe=json.dumps(new_drink_data['recipe']))
        Drink.insert(new_drink)
        drinks = list(map(Drink.long, Drink.query.all()))
        result = {
            "success": True,
            "drinks": drinks
        }
        return jsonify(result)


@app.route('/drinks/<int:drink_id>', methods=['PATCH'])
@requires_auth('patch:drinks')
def update_drink(token, drink_id):
    new_drink_data = json.loads(request.data.decode('utf-8'))
    drink_data = Drink.query.get(drink_id)
    if 'title' in new_drink_data:
        setattr(drink_data, 'title', new_drink_data['title'])
    if 'recipe' in new_drink_data:
        setattr(drink_data, 'recipe', new_drink_data['recipe'])
    Drink.update(drink_data)
    drinks = list(map(Drink.long, Drink.query.all()))
    result = {
        "success": True,
        "drinks": drinks
    }
    return jsonify(result)


@app.route('/drinks/<int:drink_id>', methods=['DELETE'])
@requires_auth('delete:drinks')
def delete_drink(token, drink_id):
    drink = Drink.query.filter(Drink.id == drink_id).one_or_none()

    if not drink:
        abort(404)

    try:
        drink.delete()
    except BaseException:
        abort(400)

    return jsonify({'success': True, 'delete': id}), 200


# Error Handling


@app.errorhandler(422)
def unprocessable(error):
    return jsonify({
        "success": False,
        "error": 422,
        "message": "unprocessable"
    }), 422


@app.errorhandler(404)
def not_found(error):
    return jsonify({
        "success": False,
        "error": 404,
        "message": "resource not found"
    }), 404


@app.errorhandler(AuthError)
def auth_error(error):
    return jsonify({
        "success": False,
        "error": error.status_code,
        "message": error.error['description']
    }), error.status_code


@app.errorhandler(401)
def unauthorized(error):
    return jsonify({
        "success": False,
        "error": 401,
        "message": 'Unathorized'
    }), 401


@app.errorhandler(500)
def internal_server_error(error):
    return jsonify({
        "success": False,
        "error": 500,
        "message": 'Internal Server Error'
    }), 500


@app.errorhandler(400)
def bad_request(error):
    return jsonify({
        "success": False,
        "error": 400,
        "message": 'Bad Request'
    }), 400


@app.errorhandler(405)
def method_not_allowed(error):
    return jsonify({
        "success": False,
        "error": 405,
        "message": 'Method Not Allowed'
    }), 405
