# main.py
import os
from dotenv import load_dotenv
from app.database import DatabaseManager
from app.auth import login
from app.menus import mostrar_menu_principal
from app.ui import mostrar_encabezado
from colorama import Fore

def main():
    """
    Función principal que inicializa la base de datos y corre el bucle de la aplicación.
    """
    load_dotenv()
    ENVIRONMENT = os.getenv("ENVIRONMENT", "production")

    # --- NUEVA LÓGICA PARA LA BASE DE DATOS ---
    DB_PATH = os.getenv("DB_PATH", "app/data")
    DB_NAME = os.getenv("DB_NAME", "inventario.db")
    
    # Asegurarse de que el directorio de la base de datos exista
    if not os.path.exists(DB_PATH):
        os.makedirs(DB_PATH)
        print(Fore.CYAN + f"Directorio '{DB_PATH}' creado.")

    db_full_path = os.path.join(DB_PATH, DB_NAME)
    # --- FIN DE LA NUEVA LÓGICA ---

    db = DatabaseManager(db_full_path)
    admin_creado, admin_pass = db.inicializar_admin_si_no_existe()

    while True:
        if ENVIRONMENT == 'development':
            usuario_logueado = db.get_user_by_username("admin")
        else:
            usuario_logueado = login(db, admin_creado, admin_pass)
            admin_creado = False

        if usuario_logueado:
            mostrar_menu_principal(db, usuario_logueado)
        else:
            mostrar_encabezado("Fin del Programa")
            print(Fore.GREEN + "\n¡Gracias por usar el Sistema de Gestión de Inventario!")
            db.close()
            print(Fore.GREEN + "Conexión a la base de datos cerrada.")
            break

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(Fore.RED + "\n\nPrograma interrumpido por el usuario.")
    except Exception as e:
        print(Fore.RED + f"\n\n❌ Un error inesperado ha ocurrido: {str(e)}")