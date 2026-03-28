

import copy
import time
import requests
from requests.auth import HTTPBasicAuth
from typing import Dict
import json
import uuid

from src import settings
import re


class GrafanaHelper:
    def __init__(self, base_url : str):
        self.base_url = base_url
        self.service_account_id = None
        self.token = None
        self.link = None
        self.admin_user = settings.GRAFANA_ADMIN_USER
        self.admin_password = settings.GRAFANA_ADMIN_PASSWORD


    # Paso 1: Crear un Service Account   
    # base_url = "http://localhost:3002"
    def make_service_account(self):
        service_account_name = "Admin"
        service_account_role = "Admin"
        
        

        response_service_accounts = requests.get(
            f"{self.base_url}/api/serviceaccounts",
            auth=HTTPBasicAuth(self.admin_user, self.admin_password)
        )

        print("Service accounts response:", response_service_accounts.text)
        service_accounts_data = response_service_accounts.json()
                
        service_accounts_list = service_accounts_data.get("serviceAccounts", []) if isinstance(service_accounts_data, dict) else service_accounts_data

        # Revisar si ya existe la cuenta de servicio
        for account in service_accounts_list:
            if isinstance(account, dict) and account.get("name") == service_account_name:
                self.service_account_id = account["id"]
                return self.service_account_id

        response_create_service_account = requests.post(
            f"{self.base_url}/api/serviceaccounts",
            json={"name": service_account_name, "role": service_account_role},
            auth=HTTPBasicAuth(self.admin_user, self.admin_password)
        )

        print("Create service account response:", response_create_service_account.text)

        # En caso de error, intentar obtener el ID nuevamente usando una query
        if response_create_service_account.status_code != 200:
            response_service_accounts = requests.get(
                f"{self.base_url}/api/serviceaccounts/search?query={service_account_name}",
                auth=HTTPBasicAuth(self.admin_user, self.admin_password)
            )
            service_accounts_data = response_service_accounts.json()
            service_accounts_list = service_accounts_data.get("serviceAccounts", []) if isinstance(service_accounts_data, dict) else service_accounts_data
            self.service_account_id = next((account["id"] for account in service_accounts_list if isinstance(account, dict) and account.get("name") == service_account_name), None)
        else:
            self.service_account_id = response_create_service_account.json()["id"]

        return self.service_account_id

    # Paso 2: Crear un token para ese service account
    # base_url = "http://localhost:3002"
    def get_token_account(self):
        if self.service_account_id is None:
            raise ValueError("El ID de la cuenta de servicio no está configurado. Llama a make_service_account() primero.")

        existing_tokens_response = requests.get(
            f"{self.base_url}/api/serviceaccounts/{self.service_account_id}/tokens",
            auth=HTTPBasicAuth(self.admin_user, self.admin_password)
        )

        print("Existing tokens response:", existing_tokens_response.text)
        # Los tókens existentes no guardan la key, por lo tanto,
        # lo ideal es eliminarlo para generar uno nuevo. 
        existing_token = next((token for token in existing_tokens_response.json() if token.get("name") == "Admin"), None)
        
        # Lo eliminamos, dado que no es necessario ni seguro tener más de uno
        # TODO: Revisar si esto puede generar condiciones de carrera
        if existing_token:
            requests.delete(
                f"{self.base_url}/api/serviceaccounts/{self.service_account_id}/tokens/{existing_token['id']}",
                auth=HTTPBasicAuth(self.admin_user, self.admin_password)
            )
            print(f"Deleted existing token: {existing_token['id']}")

        token_response = requests.post(
            f"{self.base_url}/api/serviceaccounts/{self.service_account_id}/tokens",
            json={"name": "Admin"},
            auth=HTTPBasicAuth(self.admin_user, self.admin_password)
        )

        print("STATUS TOKEN:", token_response.status_code)
        print("RESPONSE TOKEN:", token_response.text)

        self.token = token_response.json()["key"]
        print("API TOKEN:", self.token)
        
        return self.token

    # Paso 3: unimos grafana y la db
    def get_db_grafana_uid(
        self,
        db_user : str,
        db_password : str, 
        db_host : str,
        db_name : str,
        db_port : str = "5432",
    ):
        # Endpoint de Grafana
        GRAFANA_URL = f"{self.base_url}/api/datasources"

        if self.token is None:
            raise ValueError("El token no está configurado. Llama a get_token_account() primero.")

    # Headers de la petición
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.token}"
        }

        # Verificar si el datasource ya existe
        response = requests.get(GRAFANA_URL, headers=headers)
        datasources = response.json()
        existing_datasource = next((datasource for datasource in datasources if datasource.get("name") == f"Postgres-{db_name}-{db_host}-{db_port}"), None)
        has_default = any(datasource.get("isDefault") for datasource in datasources)

        if existing_datasource:
            return existing_datasource.get("uid")

        # Definición del datasource para Grafana
        datasource = {
            "name": f"Postgres-{db_name}-{db_host}-{db_port}",
            "type": "postgres",
            "access": "proxy",
            "url": f"{db_host}:{db_port}",
            "user": db_user,
            "database": db_name,
            "basicAuth": False,
            "isDefault": not has_default,
            "jsonData": {
                "sslmode": "disable"
            },
            "secureJsonData": {
                "password": db_password
            }
        }

        response = requests.post(GRAFANA_URL, headers=headers, json=datasource)

        print("Status:", response.status_code)
        print("Respuesta:", response.text)

        if response.status_code >= 300:
            raise Exception(f"Hubo un error al crear el datasource. Revisa los que bigbang tenga acceso a tu db y que las credenciales sean correctas: {response.text}")
            
        
        datasource_response = response.json()["datasource"]
        datasource_uid = datasource_response["uid"]
        datasource_id = datasource_response["id"]

        # Hacemos un update para agregar parámetros adicionales
        # Que son necesarios para que funcione bien la conexión
        update_payload = {
            "id": datasource_id,
            "uid": datasource_uid,
            "orgId": datasource_response.get("orgId", 1),
            "name": f"Postgres-{db_name}-{db_host}-{db_port}",
            "type": "grafana-postgresql-datasource",
            "access": "proxy",
            "url": f"{db_host}:{db_port}",
            "user": db_user,
            "database": db_name,
            "basicAuth": False,
            "isDefault": not has_default,
            "jsonData": {
                "sslmode": "disable",
                "database": db_name,
                "maxOpenConns": 100,
                "maxIdleConns": 100,
                "maxIdleConnsAuto": True,
                "connMaxLifetime": 14400
            },
            "secureJsonData": {
                "password": db_password
            }
        }

        update_url = f"{self.base_url}/api/datasources/{datasource_id}"
        update_response = requests.put(update_url, headers=headers, json=update_payload)
        
        print("Update Status:", update_response.status_code)
        print("Update Respuesta:", update_response.text)

        return datasource_uid

    # Solicitud  para mirar las db´s relacionadas a grafana
    def get_all_uid_db(self):
        # base_url = http://localhost:3000 o 3002
        GRAFANA_URL = f"{self.base_url}/api/datasources"

        if self.token is None:
            raise ValueError("El token no está configurado. Llama a get_token_account() primero.")
        
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.token}"
        }

        # Hacer la solicitud GET
        response = requests.get(GRAFANA_URL, headers=headers)

        print("Status:", response.status_code)
        print("Respuesta:", response.text)

        list_json = response.json()

        """
        list_json es una lista de diccionarios que cada diccionario
        tiene claves:
        'id', 'uid', 'orgId', 'name'
        """

    # Solicitus para dado grafana_json construir un dashboard
    def push_grafana_dashboard(self, grafana_json : Dict):
        # Agrego acá algo 
        # base_url= "http://localhost:3000" o 3002
        GRAFANA_URL = f"{self.base_url}/api/dashboards/db"

        if self.token is None:
            raise ValueError("El token no está configurado. Llama a get_token_account() primero.")

        # Headers para la solicitud HTTP
        headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }
        
        dashboard_json = copy.deepcopy(grafana_json)

        dashboard_json["uid"] = str(uuid.uuid4())
        dashboard_json["version"] = 1

        # Título estable (sin UUID si no es necesario)
        #dashboard_json["title"] = dashboard_json.get("title", "Dashboard")[:40]
        
        #Paneles estables (sin IDs aleatorios)
        panel_id = 1
        for panel in dashboard_json.get("panels", []):
            panel["id"] = panel_id
            panel_id += 1

        payload = {
            "dashboard": dashboard_json,
            "overwrite": False  # Si quieres sobrescribir si ya existe un dashboard con el mismo título
        } 
        
        response = requests.post(
            GRAFANA_URL,
            headers=headers,
            data=json.dumps(payload),
            timeout=30
        )

        print("Status:", response.status_code)
        print("Respuesta:", response.text)

        
        if not (response.json().get('status', False) == "success"):
            raise ValueError(f"Error en solicitud {response.status_code}")

        return response.json()



