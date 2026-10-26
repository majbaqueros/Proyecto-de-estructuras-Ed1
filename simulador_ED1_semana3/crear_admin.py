"""CLI local interactiva: no imprime ni almacena contraseñas en código."""
from getpass import getpass
from dotenv import load_dotenv
load_dotenv()
from portal.db import configure_db
from portal.services import bootstrap_admin

if __name__ == '__main__':
    configure_db()
    org = input('Nombre de la organización: ').strip()
    email = input('Correo del administrador: ').strip()
    password = getpass('Contraseña de 12+ caracteres: ')
    result = bootstrap_admin(org, email, password)
    print('Administrador creado' if result else 'La cuenta administradora ya existe')
