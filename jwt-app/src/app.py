import uuid
from datetime import datetime, timedelta
from functools import wraps

import jwt
from jwt.exceptions import ExpiredSignatureError, InvalidTokenError
from sqlalchemy import delete, insert, select
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from flask import Blueprint, Flask, jsonify, make_response, request
from werkzeug.security import generate_password_hash, check_password_hash

import database as db
from constants import UserRole
from models import user_table, token_table
from settings import SETTINGS

api_bp = Blueprint("api", __name__)


def configure_app():
    app = Flask(__name__)
    app.config.update(SETTINGS)

    app.register_blueprint(api_bp)

    with app.app_context():
        db.configure_engine(app.config)

    return app


def check_token(role: UserRole = UserRole.USER):
    def decorator(func):
        @wraps(func)
        def decorated(*args, **kwargs):
            token = None

            if 'Authorization' in request.headers:
                token = request.headers['Authorization']

            if not token:
                return jsonify({'message': 'Token is missing!'}), 401

            try:
                data = jwt.decode(token, SETTINGS['SECRET_KEY'])
                session = db.Session()
                user = session.execute(select([user_table]).where(
                    user_table.c.username == data['username'])
                ).fetchone()
            except ExpiredSignatureError:
                return jsonify({'message': 'Token is expired!'}), 401
            except (InvalidTokenError, SQLAlchemyError):
                return jsonify({'message': 'Token is invalid!'}), 401

            if not user or user['role'] != role.value:
                return jsonify({'message': 'Token is invalid!'}), 401

            return func(*args, **kwargs)

        return decorated

    return decorator


@api_bp.route('/users', methods=['GET'])
@check_token(UserRole.ADMIN)
def get_users():
    session = db.Session()
    users = session.execute(select([user_table])).fetchall()
    return jsonify({'users': [{
        'id': user['id'],
        'username': user['username'],
        'role': user['role'],
    } for user in users]})


@api_bp.route('/refresh', methods=['POST'])
def refresh():
    data = request.get_json()
    session = db.Session()
    try:
        token = session.execute(select([token_table]).where(
            token_table.c.refresh_token == data.get('refreshToken')
        )).fetchone()
    except SQLAlchemyError:
        session.rollback()
        raise
    if not token:
        return jsonify({'message': 'Token is invalid!'}), 401

    username = token['username']

    try:
        session.execute(delete(token_table).where(token_table.c.username == username))
    except SQLAlchemyError:
        session.rollback()
        raise
    else:
        session.commit()

    token = _create_token(username)
    return jsonify(token)


@api_bp.route('/sign-up', methods=['POST'])
def sign_up():
    data = request.get_json()
    session = db.Session()
    query = insert(user_table).values(
        {
            'username': data['username'],
            'password': generate_password_hash(data['password'], method='sha256'),
            'role': UserRole.USER,
        }
    ).returning(user_table.c.username)
    try:
        inserted_user_data = session.execute(query).fetchone()
    except IntegrityError:
        session.rollback()
        return jsonify({'message': 'User with username {} already exists'.format(
            data['username'])})
    except SQLAlchemyError:
        session.rollback()
        raise
    else:
        session.commit()
        return jsonify({'message': 'New user {} is created'.format(
            inserted_user_data['username'])})


@api_bp.route('/login')
def login():
    auth = request.authorization

    if not auth or not auth.username or not auth.password:
        return make_response('Could not verify', 401,
                             {'WWW-Authenticate': 'Basic realm="Login required!"'})

    session = db.Session()
    query = select([user_table]).where(user_table.c.username == auth.username)
    try:
        user = session.execute(query).fetchone()
    except SQLAlchemyError:
        session.rollback()
        raise

    if not user or not check_password_hash(user['password'], auth.password):
        return make_response('Could not verify', 401,
                             {'WWW-Authenticate': 'Basic realm="Login required!"'})

    token = _create_token(user['username'])
    return jsonify(token)


def _create_token(username):
    session = db.Session()
    token = jwt.encode({'username': username,
                        'exp': datetime.utcnow() + timedelta(minutes=10)},
                       SETTINGS['SECRET_KEY'])
    refresh_token = str(uuid.uuid4())
    query = insert(token_table).values(
        {
            'username': username,
            'expired_at': datetime.utcnow() + timedelta(minutes=60),
            'refresh_token': refresh_token,
        }
    ).returning(token_table.c.refresh_token)
    try:
        inserted_token_data = session.execute(query).fetchone()
    except SQLAlchemyError:
        session.rollback()
        raise
    else:
        session.commit()
        return {'token': token.decode('UTF-8'),
                'refresh_token': inserted_token_data['refresh_token']}
