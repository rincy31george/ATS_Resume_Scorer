
def authenticate(username, password):
    users = {
        "admin": {"password": "admin123"},
        "user": {"password": "user123"}
    }
    return username if username in users and users[username]["password"] == password else None
