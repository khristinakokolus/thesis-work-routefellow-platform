from flask import Flask, request, make_response, jsonify
import variables as var
from postgres_client import PostgresClient
from flask_bcrypt import Bcrypt
import utils


app = Flask(__name__)
bcrypt = Bcrypt(app)

postgres_client = PostgresClient(var.HOST, var.PORT, var.DB_NAME, var.PASSWORD, var.USER)
postgres_client.connect()


# add: update profile, change password, delete account, show profile?


@app.route('/', methods=['GET'])
def sign_up_get():
    return "Welcome to sign in service"


@app.route(var.SIGN_IN, methods=['POST'])
def sign_in():
    email = request.json['email']
    password = request.json['password']

    user = postgres_client.select_user_by_email(email, var.TABLE_NAME)

    if not user:
        return make_response(jsonify({
            'results': f'ERROR, you need to sign up first'
        }), 401)

    if user[0][4]:
        return make_response(jsonify({
            'results': f'ERROR, you are logged in already'
        }), 401)

    byte_password = bytes(user[0][3], 'utf-8')
    if bcrypt.check_password_hash(byte_password, password):

        postgres_client.update_record(user[0][0], 'log_in', True, var.TABLE_NAME)
        return make_response(jsonify({'logged in': 'successfully'}), 200)
    else:
        return make_response(jsonify({
            'results': 'ERROR, incorrect Password'
        }), 401)


@app.route(var.SIGN_OUT, methods=['POST'])
def sign_out():
    email = request.json['email']

    if not utils.login_validation(email, postgres_client):
        return make_response(jsonify({
            'results': 'ERROR, incorrect email or not logged in user'
        }), 401)
    user = postgres_client.select_user_by_email(email, var.TABLE_NAME)
    postgres_client.update_record(user[0][0], 'log_in', False, var.TABLE_NAME)
    return make_response(jsonify({
        'success': "Logged out successfully"
    }), 200)


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port='5002')
