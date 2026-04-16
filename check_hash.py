from werkzeug.security import check_password_hash
h = 'scrypt:32768:8:1$w8CGw85QA1QUeY8V$b10983b5ca9b00265e78c286a8bdc7f98d26f589e98065e172f4077c49ac9e568b1f3ad075280d95e1d2062684d5c7d5e09faee199be84ffb8fedd682586a9f5'
print(check_password_hash(h, 'Admin@123'))
print(check_password_hash(h, 'password'))
