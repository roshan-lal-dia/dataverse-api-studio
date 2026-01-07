"""
Dataverse API Client - Core API operations
Handles authentication and CRUD operations with Dataverse Web API
"""

import requests
import msal
import json
from datetime import datetime
from typing import Optional, Dict, List


class DataverseClient:
    """Handles all authentication and API operations with Dataverse"""
    
    def __init__(self, tenant_id: str, client_id: str, client_secret: str, 
                 org_url: str):
        self.tenant_id = tenant_id
        self.client_id = client_id
        self.client_secret = client_secret
        self.org_url = org_url.rstrip('/')
        self.access_token = None
        self.token_expiry = None
        
    def authenticate(self) -> bool:
        """Authenticate with Entra ID and get access token"""
        try:
            authority = f"https://login.microsoftonline.com/{self.tenant_id}"
            app = msal.ConfidentialClientApplication(
                self.client_id,
                authority=authority,
                client_credential=self.client_secret
            )
            
            scope = [f"{self.org_url}/.default"]
            result = app.acquire_token_for_client(scopes=scope)
            
            if "access_token" in result:
                self.access_token = result["access_token"]
                return True
            else:
                raise Exception(f"Auth failed: {result.get('error_description', result)}")
        except Exception as e:
            raise Exception(f"Authentication Error: {str(e)}")
    
    def _get_headers(self) -> Dict:
        """Build standard headers for API calls"""
        return {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json",
            "OData-MaxVersion": "4.0",
            "OData-Version": "4.0",
            "Accept": "application/json"
        }
    
    def create_record(self, table_name: str, data: Dict) -> Dict:
        """Create a new record"""
        url = f"{self.org_url}/api/data/v9.2/{table_name}s"
        headers = self._get_headers()
        response = requests.post(url, json=data, headers=headers)
        
        if response.status_code in (200, 201):
            return {
                "success": True,
                "id": response.headers.get("OData-EntityId", "").split("(")[1].split(")")[0] if "OData-EntityId" in response.headers else "",
                "data": response.json() if response.content else {}
            }
        else:
            return {"success": False, "error": response.text}
    
    def read_record(self, table_name: str, record_id: str, 
                   select: List[str] = None) -> Dict:
        """Retrieve a single record by ID"""
        url = f"{self.org_url}/api/data/v9.2/{table_name}s({record_id})"
        headers = self._get_headers()
        
        params = {}
        if select:
            params["$select"] = ",".join(select)
        
        response = requests.get(url, headers=headers, params=params)
        
        if response.status_code == 200:
            return {"success": True, "data": response.json()}
        else:
            return {"success": False, "error": response.text}
    
    def read_multiple(self, table_name: str, filter_query: str = None,
                     select: List[str] = None, top: int = 100,
                     order_by: str = None) -> Dict:
        """Query multiple records with OData filter"""
        url = f"{self.org_url}/api/data/v9.2/{table_name}s"
        headers = self._get_headers()
        
        params = {"$top": top}
        if filter_query:
            params["$filter"] = filter_query
        if select:
            params["$select"] = ",".join(select)
        if order_by:
            params["$orderby"] = order_by
        
        response = requests.get(url, headers=headers, params=params)
        
        if response.status_code == 200:
            data = response.json()
            return {
                "success": True,
                "count": len(data.get("value", [])),
                "data": data.get("value", [])
            }
        else:
            return {"success": False, "error": response.text}
    
    def update_record(self, table_name: str, record_id: str, data: Dict) -> Dict:
        """Update an existing record"""
        url = f"{self.org_url}/api/data/v9.2/{table_name}s({record_id})"
        headers = self._get_headers()
        headers["If-Match"] = "*"
        
        response = requests.patch(url, json=data, headers=headers)
        
        if response.status_code in (204, 1223):
            return {"success": True, "message": "Record updated successfully"}
        else:
            return {"success": False, "error": response.text}
    
    def delete_record(self, table_name: str, record_id: str) -> Dict:
        """Delete a record"""
        url = f"{self.org_url}/api/data/v9.2/{table_name}s({record_id})"
        headers = self._get_headers()
        
        response = requests.delete(url, headers=headers)
        
        if response.status_code in (204, 1223):
            return {"success": True, "message": "Record deleted successfully"}
        else:
            return {"success": False, "error": response.text}
    
    def batch_operation(self, operations: List[Dict]) -> Dict:
        """Execute batch operations (max 1000 per batch)"""
        url = f"{self.org_url}/api/data/v9.2/$batch"
        headers = self._get_headers()
        
        batch_id = f"batch_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        headers["Content-Type"] = f"multipart/mixed;boundary={batch_id}"
        
        body = self._build_batch_body(batch_id, operations)
        
        response = requests.post(url, data=body, headers=headers)
        
        if response.status_code in (200, 201):
            return {"success": True, "data": response.text, "message": "Batch executed"}
        else:
            return {"success": False, "error": response.text}
    
    def _build_batch_body(self, batch_id: str, operations: List[Dict]) -> str:
        """
        Build multipart batch body with support for Content-ID references.
        
        Content-ID enables deep insert: operations can reference other operations' 
        created records using $1, $2, etc. syntax without needing to extract GUIDs.
        
        Example:
            Op 1 (id: "1"): POST /mdm_articles -> creates Article 1
            Op 2 (id: "2"): POST /mdm_articles -> creates Article 2
            Op 3 (id: "3"): POST /mdm_articlerelationships with:
                "mdm_parentarticle@odata.bind": "/$1"  <- references Op 1's GUID
                "mdm_childarticle@odata.bind": "/$2"   <- references Op 2's GUID
        """
        body = ""
        
        for idx, op in enumerate(operations, 1):
            body += f"--{batch_id}\r\n"
            body += "Content-Type: application/http\r\n"
            body += "Content-Transfer-Encoding: binary\r\n"
            
            # Add Content-ID header if operation has an id field (for deep insert)
            content_id = op.get("id")
            if content_id:
                body += f"Content-ID: {content_id}\r\n"
            
            body += "\r\n"
            
            method = op.get("method", "POST")
            url_path = op.get("url", "")
            data = op.get("data", {})
            
            # Prepare the HTTP request line and headers
            http_request = f"{method} {url_path} HTTP/1.1\r\n"
            http_request += "Content-Type: application/json\r\n"
            
            # Add Content-Length if we have data
            if data:
                data_str = json.dumps(data)
                http_request += f"Content-Length: {len(data_str.encode('utf-8'))}\r\n"
                http_request += "\r\n"
                http_request += data_str
            else:
                http_request += "Content-Length: 0\r\n"
                http_request += "\r\n"
            
            body += http_request
            body += "\r\n"
        
        body += f"--{batch_id}--"
        return body
