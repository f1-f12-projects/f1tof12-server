import os
import boto3
import logging
from fastapi import Request
from fastapi.responses import JSONResponse

logger = logging.getLogger(__name__)

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
            
            logger.info(f"CloudFront Middleware - Method: {request.method}, Path: {request.url.path}, Environment: {os.getenv('ENVIRONMENT')}")
            
            # Skip validation for OPTIONS requests (CORS preflight)
            if request.method == "OPTIONS":
                logger.info("Allowing OPTIONS request")
                await self.app(scope, receive, send)
                return
            
            # Skip validation for health check and root endpoints
            if request.url.path in ["/", "/health", "/vst/health", "/vst/", "/vst/version"]:
                logger.info("Allowing health/root endpoint")
                await self.app(scope, receive, send)
                return
            
            # Skip validation in non-production environments
            if os.getenv('ENVIRONMENT') != 'prod':
                logger.info("Allowing non-prod environment")
                await self.app(scope, receive, send)
                return
                
            # Check headers
            origin = request.headers.get("origin") or request.headers.get("x-origin")
            cloudfront_secret = request.headers.get("x-cloudfront-secret")
            
            # Require both CloudFront secret AND allowed origin
            secret_match = cloudfront_secret == self.cloudfront_secret
            origin_allowed = origin and origin in self.allowed_origins
            
            if secret_match and origin_allowed:
                logger.info("Request allowed through CloudFront validation")
                await self.app(scope, receive, send)
                return
            else:
                logger.warning(f"Request blocked - Origin: {origin}, Secret Match: {secret_match}")
                logger.warning(f"Origin in allowed: {origin_allowed}")
                response = JSONResponse(
                    status_code=403,
                    content={"error": "Access denied"},
                    headers={
                        "Access-Control-Allow-Origin": origin or "*",
                        "Access-Control-Allow-Credentials": "true",
                        "Access-Control-Allow-Methods": "*",
                        "Access-Control-Allow-Headers": "*"
                    }
                )
                await response(scope, receive, send)
                return
        
        await self.app(scope, receive, send)