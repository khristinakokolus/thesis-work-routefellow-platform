import re


def password_validation(password):
    pattern = re.compile("^(?=.*?[A-Z])(?=.*?[a-z])(?=.*?[0-9])(?=.*?[#?!@$%^&*-_]).{6,}$")
    match = re.search(pattern, password)
    return match


def email_validation(email):
    pattern = re.compile('^[\w\.]+@([\w-]+\.)+[\w-]{2,4}$')
    match = re.search(pattern, email)
    return match