import variables as var


def login_validation(email, postgres_client):
    user = postgres_client.select_user_by_email(email, var.TABLE_NAME)
    if user:
        return user[0][4]
    return False