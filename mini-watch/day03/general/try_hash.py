from werkzeug.security import generate_password_hash, check_password_hash

password_hash = generate_password_hash("Learn123!")
print(password_hash)
print(check_password_hash(password_hash, "Learn123!"))
print(check_password_hash(password_hash, "Wrong123!"))
