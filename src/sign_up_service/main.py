from flask import Flask, request, make_response, jsonify
import variables as var
from postgres_client import PostgresClient
from flask_bcrypt import Bcrypt
import uuid
import utils


app = Flask(__name__)
bcrypt = Bcrypt(app)

postgres_client = PostgresClient(var.HOST, var.PORT, var.DB_NAME, var.PASSWORD, var.USER)
postgres_client.connect()


@app.route('/', methods=['GET'])
def sign_up_get():
    return "Welcome to sign up service"


# Create new account with the user details
@app.route(var.SIGN_UP, methods=['POST'])
def sign_up():
    username = request.json['username']
    email = request.json['email']

    check_user_existence = postgres_client.select_user_by_username_and_email(username, email, var.TABLE_NAME)
    if check_user_existence:
        return make_response(jsonify({"results": f'ERROR, user with such email: {email} - already exists'}), 400)
    else:
        pass

    if utils.email_validation(email) is None:
        return make_response(jsonify({"results": f'ERROR, {email} is not a valid email address'}), 400)

    password = request.json['password']
    if utils.password_validation(password) is None:
        return make_response(jsonify({"results": f'ERROR, {var.error_msg}'}), 400)

    hashed_password = bcrypt.generate_password_hash(password)
    password = hashed_password.decode("utf-8")
    user_id = str(uuid.uuid4())
    data_to_insert = (user_id, username, email, password, False)
    postgres_client.insert_records(data_to_insert, var.TABLE_NAME)

    return make_response(jsonify({
        "success": 'User Created Successfully'
    }), 200)


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port='5001')
