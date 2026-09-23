"""Trusted local setup. Never run through a public HTTP endpoint."""
import getpass
import secrets
from server import ADMIN_EMAIL, connect, hash_password, init_db

def main():
    init_db()
    with connect() as db:
        if db.execute('SELECT id FROM users WHERE email=?', (ADMIN_EMAIL,)).fetchone():
            print(f'{ADMIN_EMAIL} ist bereits eingerichtet. Das bestehende Passwort bleibt gültig.')
            return
    print(f'Admin-Ersteinrichtung für {ADMIN_EMAIL}')
    password = getpass.getpass('Neues Passwort (mindestens 12 Zeichen): ')
    if len(password) < 12 or password != getpass.getpass('Passwort wiederholen: '):
        raise SystemExit('Passwörter stimmen nicht überein oder sind zu kurz. Es wurde kein Konto angelegt.')
    salt = secrets.token_hex(16)
    with connect() as db:
        db.execute('INSERT INTO users(email,name,company,role,salt,password_hash) VALUES (?,?,?,?,?,?)',
                   (ADMIN_EMAIL, 'MACHBAR', 'MACHBAR', 'admin', salt, hash_password(password, salt)))
    print('Admin-Konto angelegt. Anmeldung unter /#/admin möglich.')

if __name__ == '__main__':
    main()
