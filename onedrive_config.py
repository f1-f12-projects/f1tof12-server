"""OneDrive integration configuration"""
from math import log
import os
import httpx
import boto3
import json
import logging
from datetime import datetime, timedelta
from fastapi import HTTPException

logger = logging.getLogger(__name__)

class MicrosoftTokenManager:
    def __init__(self):
        from scripts.constants import ENVIRONMENT
        self.environment = ENVIRONMENT
        self.ssm = boto3.client('ssm', region_name='us-east-1')
        customer = os.getenv('CUSTOMER', 'vst')
        self.path_prefix = f'/f1tof12/{self.environment}/{customer}'
        self._cached_token = None
        self._token_expires_at = None
        self.tenant_id = None
        logger.info(f"Initialized MicrosoftTokenManager with path prefix: {self.path_prefix}")
    
    def _get_ssm_parameter(self, param_name: str) -> str:
        """Get parameter from SSM"""
        try:
            response = self.ssm.get_parameter(Name=param_name, WithDecryption=True)
            return response['Parameter']['Value']
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to get SSM parameter {param_name}: {str(e)}")
    
    def _is_token_expired(self) -> bool:
        """Check if current token is expired"""
        if not self._token_expires_at:
            logger.info("Token expiration time not set, treating as expired.")
            return True
        
        logger.info(f"Token expires at {self._token_expires_at}, current time is {datetime.now()}")
        return datetime.now() >= self._token_expires_at
    
    async def get_microsoft_token(self) -> str:
        """Get Microsoft access token, refresh if expired"""
        if self._cached_token and not self._is_token_expired():
            logger.info("Using cached Microsoft token.")
            return self._cached_token
        
        logger.info("Fetching new Microsoft token from Azure AD.")
        # Get tenant ID and credentials from SSM
        # If environment is dev, then get from .env file
        if self.environment == 'dev':
            self.tenant_id = os.getenv('ONEDRIVE_TENANT_ID')
            client_id = os.getenv('ONEDRIVE_CLIENT_ID')
            client_secret = os.getenv('ONEDRIVE_CLIENT_SECRET')
            self.drive_id = os.getenv('ONEDRIVE_DRIVE_ID')
        else:
            self.tenant_id = self._get_ssm_parameter(f'{self.path_prefix}/onedrive/tenant_id')
            client_id = self._get_ssm_parameter(f'{self.path_prefix}/onedrive/client-id')
            client_secret = self._get_ssm_parameter(f'{self.path_prefix}/onedrive/client-secret')
            self.drive_id = self._get_ssm_parameter(f'{self.path_prefix}/onedrive/drive-id')
            logger.info("Retrieved OneDrive configuration from SSM.")
        
        self.folder_path = 'documents/profiles' + self.path_prefix
        logger.info(f"Using folder path: {self.folder_path}")

        # Request new token
        url = f"https://login.microsoftonline.com/{self.tenant_id}/oauth2/v2.0/token"
        logger.info(f"Requesting token from URL: {url}")
        data = {
            'grant_type': 'client_credentials',
            'client_id': client_id,
            'client_secret': client_secret,
            'scope': 'https://graph.microsoft.com/.default'
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(url, data=data)
            
        if response.status_code != 200:
            raise HTTPException(status_code=500, detail=f"Failed to get Microsoft token: {response.text}")
        
        token_data = response.json()
        self._cached_token = token_data['access_token']
        expires_in = token_data.get('expires_in', 3600)
        self._token_expires_at = datetime.now() + timedelta(seconds=expires_in - 60)  # 60s buffer
        
        logger.info(f"Obtained new Microsoft token, expires in {expires_in} seconds.")
        return self._cached_token

class OneDriveClient:
    def __init__(self):
        from scripts.constants import ENVIRONMENT
        self.environment = ENVIRONMENT
        self.token_manager = MicrosoftTokenManager()
        self.access_token = None

        logger.info(f"Initialized OneDriveClient for environment: {self.environment}")
    
    async def upload_file(self, file_path: str, filename: str) -> str:
        """Upload file to OneDrive using site drive"""
        # Get fresh token
        if self.access_token:
            token = self.access_token  # Dev environment
        else:
            token = await self.token_manager.get_microsoft_token()  # Prod environment
        
        # Use SharePoint drive ID
        drive_id = self.token_manager.drive_id
        folder_path = self.token_manager.folder_path
        url = f"https://graph.microsoft.com/v1.0/drives/{drive_id}/root:/{folder_path}/{filename}:/content"
        logger.info(f"Uploading file to OneDrive: {url}")
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/octet-stream"
        }
        
        with open(file_path, "rb") as f:
            async with httpx.AsyncClient() as client:
                response = await client.put(url, headers=headers, content=f.read())
                
        if response.status_code in [200, 201]:
            return response.json().get("webUrl", file_path)
        
        error_detail = f"Status: {response.status_code}, Response: {response.text[:200]}"
        raise HTTPException(status_code=500, detail=error_detail)

token_manager = MicrosoftTokenManager()
onedrive_client = OneDriveClient()