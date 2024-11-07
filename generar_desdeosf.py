import time
import random
import requests
import pandas as pd
from io import StringIO

# Configuración inicial
osf_token = 'TVJALoFX8HrZ5YEbXeEMYYDBb9EL30qdDf2hA6jbXSOzb8C3P2QDxPY8LCAgnBgBax99n9'  # Reemplaza con tu token de OSF
project_id = 'h2te3'  # Reemplaza con el ID del proyecto en OSF
file_name = 'pacientes_enfermeras_200.csv'
download_url = 'https://osf.io/download/672a0d0f1728a8447dbaa565/'  # URL directa del archivo en OSF
headers = {
    'Authorization': f'Bearer {osf_token}'
}

# Función para descargar la base de datos inicial desde OSF
def descargar_datos_osf():
    response = requests.get(download_url)
    response.raise_for_status()
    data_str = response.text
    # Leer el archivo ignorando las primeras líneas no deseadas
    df = pd.read_csv(StringIO(data_str), skiprows=2)
    # Asegurar que las columnas sean de tipo entero
    df['id_pacientes_enfermeras'] = pd.to_numeric(df['id_pacientes_enfermeras'], errors='coerce').fillna(0).astype(int)
    df['id_paciente'] = pd.to_numeric(df['id_paciente'], errors='coerce').fillna(0).astype(int)
    return df

# Función para generar un nuevo paciente
def generar_nuevo_paciente(max_id_paciente, last_id_pacientes_enfermeras):
    return {
        'id_pacientes_enfermeras': last_id_pacientes_enfermeras + 1,
        'id_paciente': max_id_paciente + 1,
        'id_enfermera': random.randint(1, 50)
    }

# Función para actualizar el archivo local con un nuevo paciente
def actualizar_datos_localmente(df):
    max_id_paciente = df['id_paciente'].max()
    last_id_pacientes_enfermeras = df['id_pacientes_enfermeras'].max()
    
    # Genera un nuevo registro de paciente y lo añade al DataFrame
    nuevo_paciente = generar_nuevo_paciente(max_id_paciente, last_id_pacientes_enfermeras)
    df = pd.concat([df, pd.DataFrame([nuevo_paciente])], ignore_index=True)
    
    # Guarda el archivo actualizado localmente, concatenando con los datos existentes
    df.to_csv(file_name, index=False, mode='w', encoding='utf-8')
    print(f"Nuevo paciente añadido: {nuevo_paciente}")
    return df

# Función para subir o actualizar el archivo en OSF
def subir_o_actualizar_en_osf():
    list_url = f'https://api.osf.io/v2/nodes/{project_id}/files/osfstorage/'
    response = requests.get(list_url, headers=headers)
    
    if response.status_code == 200:
        files = response.json()['data']
        file_id = None
        for file in files:
            if file['attributes']['name'] == file_name:
                file_id = file['id']
                break
        
        if file_id:
            upload_url = f'https://files.osf.io/v1/resources/{project_id}/providers/osfstorage/{file_id}?kind=file'
            with open(file_name, 'rb') as f:
                response = requests.put(upload_url, headers=headers, files={'file': f})
            
            if response.status_code in [200, 201]:
                print('Archivo actualizado exitosamente en OSF.')
            else:
                print('Error al actualizar el archivo:', response.status_code, response.text)
        else:
            upload_url = f'https://files.osf.io/v1/resources/{project_id}/providers/osfstorage/?name={file_name}'
            with open(file_name, 'rb') as f:
                response = requests.put(upload_url, headers=headers, files={'file': f})
            
            if response.status_code == 201:
                print('Archivo creado exitosamente en OSF.')
            else:
                print('Error al crear el archivo:', response.status_code, response.text)
    else:
        print('Error al obtener la lista de archivos en OSF:', response.status_code, response.text)

# Descargar la base de datos inicial
df = descargar_datos_osf()

# Bucle de generación y carga cada 10 segundos
while True:
    df = actualizar_datos_localmente(df)  # Actualiza el DataFrame local con un nuevo paciente
    subir_o_actualizar_en_osf()           # Crea o actualiza el archivo en OSF
    time.sleep(10)  # Espera 10 segundos
