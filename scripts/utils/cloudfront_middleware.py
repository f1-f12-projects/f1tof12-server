import os
import boto3
from fastapi import Request
from fastapi.responses import JSONResponse

class CloudFrontMiddleware:
    def __init__(self, app):
        self.app = app
        self.allowed_origins = [
            "https://f1tof12.com",
            "https://www.f1tof12.com"
        ]
        self.cloudfront_secret = self._get_cloudfront_secret()
    
    def _get_cloudfront_secret(self):
        # Try environment variable first
        secret = os.getenv('CLOUDFRONT_SECRET_VALUE')
        if secret:
            return secret
        
        # Fetch from SSM Parameter Store
        try:
            ssm = boto3.client('ssm', region_name='us-east-1')
            response = ssm.get_parameter(Name='/f1tof12/cloudfront/secret-value', WithDecryption=True)
            return response['Parameter']['Value']
        except Exception:
            return None
        
    async def __call__(self, scope, receive, send):
        if scope["type"] == "http":
            request = Request(scope, receive)
            
            # Skip validation for health check and root endpoints
            if request.url.path in ["/", "/health", "/vst/health", "/vst/"]:
                await self.app(scope, receive, send)
                return
            
            # Skip validation in non-production environments
            if os.getenv('ENVIRONMENT') != 'prod':
                await self.app(scope, receive, send)
                return
                
            # Check CloudFront secret header (if present)
            cloudfront_secret = request.headers.get("x-cloudfront-secret")
            if cloudfront_secret and cloudfront_secret != self.cloudfront_secret:
                response = JSONResponse(
                    status_code=403,
                    content={"error": "Access denied"}
                )
                await response(scope, receive, send)
                return
                
            # Check Origin header
            origin = request.headers.get("origin")
            if origin and origin not in self.allowed_origins:
                response = JSONResponse(
                    status_code=403,
                    content={"error": "Access denied"}
                )
                await response(scope, receive, send)
                return
        
        await self.app(scope, receive, send)