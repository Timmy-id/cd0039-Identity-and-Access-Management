import sys
from flask import Flask, request, jsonify, abort
import json
from flask_cors import CORS

from src.database.models import db_drop_and_create_all, setup_db, Drink
from src.auth.auth import AuthError, requires_auth

app = Flask(__name__)
setup_db(app)
CORS(app)

# Dropping and creating the database.
# db_drop_and_create_all()

# ROUTES


@app.route('/drinks')
def get_drinks():
    try:
        drinks = [drink.short() for drink in Drink.query.all()]

        return jsonify({
            "success": True,
            "drinks": drinks
        })
    except Exception:
        abort(404)


@app.route('/drinks-detail')
@requires_auth('get:drinks-detail')
def get_drink_details(payload):
    try:
        drinks = [drink.long() for drink in Drink.query.all()]
        return jsonify({
            "success": True,
            "drinks": drinks
        })
    except Exception:
        abort(404)


@app.route('/drinks', methods=['POST'])
@requires_auth('post:drinks')
def create_drink(payload):
    body = request.get_json()

    try:
        title = body.get("title")
        recipe = body.get("recipe")

        if not title or not recipe:
            abort(400)

        for info in recipe:
            color = info["color"]
            name = info["name"]
            parts = info["parts"]

            if not color or not parts or not name:
                abort(400)

        if Drink.query.filter_by(title=title).first():
            abort(400)
        drink = Drink(title=title, recipe=json.dumps(recipe))
        drink.insert()
        return jsonify({"success": True, "drinks": [drink.long()]})

    except Exception:
        print(sys.exc_info())
        abort(400)


@app.route('/drinks/<id>', methods=['PATCH'])
@requires_auth('patch:drinks')
def edit_drink(payload, id):
    body = request.get_json()

    try:
        drink = Drink.query.filter(
            Drink.id == id).one_or_none()

        if drink is None:
            abort(404)

        title = body.get("title")
        recipe = body.get("recipe")

        if title:
            drink.title = title

        if recipe:
            for info in recipe:
                color = info["color"]
                name = info["name"]
                parts = info["parts"]

                if not color or not parts or not name:
                    abort(400)

            drink.recipe = json.dumps(recipe)

        drink.update()
        return jsonify({"success": True, "drinks": [drink.long()]})
    except Exception:
        abort(400)


@app.route('/drinks/<id>', methods=['DELETE'])
@requires_auth('delete:drinks')
def delete_drink(payload, id):
    try:
        drink = Drink.query.filter(
            Drink.id == id).one_or_none()

        if drink is None:
            abort(404)

        drink.delete()

        return jsonify({
            "success": True,
            "delete": id
        })
    except Exception:
        abort(400)


# Error Handling

@app.errorhandler(422)
def unprocessable(error):
    return jsonify({
        "success": False,
        "error": 422,
        "message": "unprocessable"
    }), 422


@app.errorhandler(400)
def bad_request(error):
    return jsonify({
        "success": False,
        "error": 400,
        "message": "bad request"
    }), 400


@app.errorhandler(404)
def not_found(error):
    return jsonify({
        "success": False,
        "error": 404,
        "message": "not found"
    }), 404


@app.errorhandler(401)
def unauthorized(error):
    return jsonify({
        "success": False,
        "error": 401,
        "message": "unauthorized"
    }), 401


@app.errorhandler(AuthError)
def invalid_auth(error):
    return jsonify({
        "success": False,
        "error": error.status_code,
        "message": error.error
    }), error.status_code
