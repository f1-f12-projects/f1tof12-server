__version__ = "4.0.0"
__major_version__ = 4
__minor_version__ = 0
__patch_version__ = 0

# Latest version should be on top
__changelog__ = {
    "4.0.0": [
        "Leave management system implementation"
    ],
    "3.1.1": [
        "Minor version update"
    ],
    "3.0.0": [
        "Enhancements related to Profiles & Requirements"
    ],
    "2.4.0": [
        "Fixed DynamoDBAdapter abstract class implementation by adding missing candidate methods",
        "Implemented candidate related APIs",
        "Implemented process profile related APIs"
    ],
    "2.3.0": [
        "Added requirement statuses from database",
        "Implemented requirement status update API with remarks appending",
    ],
    "2.2.0": [
        "Added requirement status update API with remarks appending",
        "Implemented automatic closed_date setting for terminal statuses (9, 10)",
        "Added date and username formatting for remarks tracking",
        "Standardized timezone consistency across all datetime fields to IST"
    ],
    "2.1.0": [
        "Added APIs to handle Requirements"
    ],
    "2.0.0": [
        "Added CloudFront middleware security layer to restrict API access",
        "Implemented dual validation: CloudFront secret header and origin verification",
        "APIs now only accessible from f1tof12.com domain through CloudFront",
        "Enhanced CORS configuration to support custom security headers",
        "Fixed CloudFront header forwarding for Authorization tokens"
    ],
    "1.4.1": [
        "Fixed CloudFront middleware to correctly bypass origin checks for health and root endpoints",
        "Ensured CloudFront secret validation is skipped in non-production environments"
    ],
    "1.4.0": [
        "Removed CloudFront-related files and configurations",
        "Cleaned up deployment files for Lambda-only architecture",
        "Removed Docker and Serverless Framework dependencies",
        "APIs can now only be accessed via API Gateway endpoints"
    ],
    "1.3.0": [
        "Cleaned up deployment configuration",
        "Removed unused Docker and Serverless Framework files",
        "Simplified environment configuration for production",
        "Fixed cross-region SSM parameter access"
    ],
    "1.2.3": [
        "Enhanced error handling for users",
        "Updated authentication for Finance users to fetch customers"
    ],
    "1.2.2": [
        "Added filename & method name to the log output.",
        "auth: Fixed issue where admin role requires manager role and not all roles.",
        "Users: Fixed issue with password reset return code.",
        "Added new file to get updated change log based on git changes.",
        "Enhanced error handling in scripts/utils/response.py"
    ],
    "1.2.1": [
        "Added manager role access to invoice APIs",
        "Optimized SQLiteAdapter with helper methods",
        "Fixed SQLAlchemy type errors in update operations",
        "Implemented all placeholder database methods"
    ],
    "1.2.0": [
        "Added role-based access control with Cognito custom attributes",
        "Centralized constants for role management", 
        "Enhanced login response with user role",
        "Added bulk role assignment for existing users",
        "Improved error handling and security"
    ],
    "1.1.0": ["Initial release with basic user management"],
    "1.0.0": ["Base application structure"]
}