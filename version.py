__version__ = "1.2.2"
__major_version__ = 1
__minor_version__ = 2
__patch_version__ = 2

# Latest version should be on top
__changelog__ = {
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