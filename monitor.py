import gspread
from oauth2client.service_account import ServiceAccountCredentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import time
from datetime import datetime

# Autenticación y acceso a Google Sheets
scope = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/drive",
    "https://www.googleapis.com/auth/spreadsheets"
]

# Cargar credenciales
creds = ServiceAccountCredentials.from_json_keyfile_name("key.json", scope)
client = gspread.authorize(creds)
drive_service = build('drive', 'v3', credentials=creds)

def load_page_token():
    """Carga el último token de página guardado."""
    try:
        with open('page_token.txt', 'r') as f:
            return f.read().strip()
    except FileNotFoundError:
        return None

def save_page_token(token):
    """Guarda el token de página actual."""
    try:
        with open('page_token.txt', 'w') as f:
            f.write(token)
    except Exception as e:
        print(f"Error al guardar el token de página: {e}")

def get_file_details(file_id):
    """Obtiene los detalles del archivo, incluyendo el último usuario que lo modificó."""
    try:
        file = drive_service.files().get(
            fileId=file_id,
            fields='name,lastModifyingUser'
        ).execute()
        return file
    except Exception as e:
        print(f"Error al obtener detalles del archivo: {e}")
        return None

def monitor_sheet_changes(drive_service, sheet_id):
    """
    Monitorea cambios en una hoja de cálculo específica.

    Args:
        drive_service: Objeto del servicio de la API de Drive.
        sheet_id: El ID de la hoja de cálculo a monitorear.
    """
    try:
        # Obtener el último token guardado o solicitar uno nuevo
        page_token = load_page_token()
        if not page_token:
            response = drive_service.changes().getStartPageToken().execute()
            page_token = response.get('startPageToken')
            save_page_token(page_token)

        while True:
            response = drive_service.changes().list(
                pageToken=page_token,
                fields='newStartPageToken, changes(fileId, file)'
            ).execute()

            for change in response.get('changes', []):
                if change.get('fileId') == sheet_id:
                    print(f"\n[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] ¡Se detectaron cambios en la hoja!")
                    
                    # Obtener detalles del archivo
                    file_details = get_file_details(sheet_id)
                    if file_details:
                        file_name = file_details.get('name', 'Desconocido')
                        last_user = file_details.get('lastModifyingUser', {}).get('displayName', 'Desconocido')
                        print(f"Archivo modificado: {file_name}")
                        print(f"Modificado por: {last_user}")

            # Actualizar y guardar el nuevo token
            page_token = response.get('newStartPageToken')
            if page_token:
                save_page_token(page_token)
            else:
                break

            # Esperar 10 segundos antes de la próxima verificación
            time.sleep(10)

    except HttpError as error:
        print(f'Ocurrió un error: {error}')
    except Exception as e:
        print(f'Error inesperado: {e}')

if __name__ == "__main__":
    try:
        sheet_id = '1QeY6G-VkcC-s6B2irJA3M2jVnmxxMvcgCIWiZfc4UCM'
        monitor_sheet_changes(drive_service, sheet_id)
    except Exception as e:
        print(f"Error al iniciar el monitoreo: {e}")