import os
import boto3
from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse

class CloudFrontMiddleware:
    def __init__(self, app):
        self.app = app
        self.secret_header = os.getenv('CLOUDFRONT_SECRET_HEADER', 'X-CloudFront-Secret')
        self.secret_value = self._get_secret_value()
    
    def _get_secret_value(self):
        # Try environment variable first
        secret = os.getenv('CLOUDFRONT_SECRET_VALUE')
        if secret:
            return secret
        
        # Fetch from SSM Parameter Store
        try:
            ssm = boto3.client('ssm', region_name='ap-south-1')
            response = ssm.get_parameter(Name='/f1tof12/cloudfront/secret-value', WithDecryption=True)
            return response['Parameter']['Value']
        except Exception:
            return None
        
    async def __call__(self, scope, receive, send):
        if scope["type"] == "http":
            request = Request(scope, receive)
            
            # Skip validation for health check and root endpoints
            if request.url.path in ["/", "/health"]:
                await self.app(scope, receive, send)
                return
                
            # Check if CloudFront secret header is present and valid
            if self.secret_value:
                header_value = request.headers.get(self.secret_header)
                if header_value != self.secret_value:
                    response = JSONResponse(
                        status_code=403,
                        content={"error": "Access denied"}
                    )
                    await response(scope, receive, send)
                    return
        
        await self.app(scope, receive, send)