#!/usr/bin/env python3
import subprocess
import re
import sys
import os
from typing import List, Dict

def get_git_changes() -> Dict[str, List[str]]:
    """Get modified files and their changes from git"""
    try:
        # Get modified files
        result = subprocess.run(['git', 'status', '--porcelain'], 
                              capture_output=True, text=True, check=True)
        modified_files = [line[2:].strip() for line in result.stdout.strip().split('\n') if line.strip()]
        
        # Get diff summary
        result = subprocess.run(['git', 'diff', '--stat', 'HEAD'], 
                              capture_output=True, text=True, check=True)
        diff_stats = result.stdout.strip()
        
        return {
            'files': modified_files
        }
    except subprocess.CalledProcessError:
        return {'files': []}

def analyze_changes_with_ai(files: List[str]) -> List[str]:
    """Generate changelog entries using git diff analysis"""
    changes = []
    
    for file in files:
        if 'version.py' in file:
            continue  # Skip version file
            
        try:
            # Get diff for specific file
            result = subprocess.run(['git', 'diff', 'HEAD', '--', file], 
                                  capture_output=True, text=True, check=True)
            diff_content = result.stdout
            
            if not diff_content:
                continue
                
            # Analyze diff patterns
            added_lines = [line[1:] for line in diff_content.split('\n') if line.startswith('+') and not line.startswith('+++')]
            removed_lines = [line[1:] for line in diff_content.split('\n') if line.startswith('-') and not line.startswith('---')]
            
            # Generate smart changelog based on diff content
            if any('error' in line.lower() or 'exception' in line.lower() for line in added_lines):
                changes.append(f"Enhanced error handling in {file}")
            elif any('log' in line.lower() for line in added_lines):
                changes.append(f"Improved logging in {file}")
            elif any('auth' in line.lower() or 'token' in line.lower() for line in added_lines):
                changes.append(f"Updated authentication in {file}")
            elif 'test' in file.lower():
                changes.append(f"Added/updated tests in {file}")
            elif len(added_lines) > len(removed_lines):
                changes.append(f"Added new functionality to {file}")
            elif len(removed_lines) > len(added_lines):
                changes.append(f"Refactored and cleaned up {file}")
            else:
                changes.append(f"Updated {file}")
                
        except subprocess.CalledProcessError:
            changes.append(f"Updated {file}")
    
    return list(set(changes))  # Remove duplicates

def analyze_changes(files: List[str]) -> List[str]:
    """Analyze file changes and generate changelog entries"""
    # Try AI-powered analysis first
    try:
        return analyze_changes_with_ai(files)
    except Exception:
        # Fallback to simple pattern matching
        changes = []
        for file in files:
            if 'auth.py' in file:
                changes.append("Enhanced authentication and role-based access control")
            elif 'api.py' in file:
                changes.append("Improved API error handling and responses")
            elif 'logging' in file:
                changes.append("Updated logging configuration")
            elif 'response.py' in file:
                changes.append("Standardized error response format")
            elif 'version.py' in file:
                continue  # Skip version file
            else:
                changes.append(f"Updated {file}")
        return list(set(changes))

def generate_changelog() -> List[str]:
    """Generate changelog entries from current git changes"""
    git_data = get_git_changes()
    
    if not git_data['files']:
        return ["No changes detected"]
    
    changes = analyze_changes(git_data['files'])
    
    # Add generic entries based on file patterns
    if any('test' in f for f in git_data['files']):
        changes.append("Added/updated tests")
    
    if any('requirements' in f or 'setup' in f for f in git_data['files']):
        changes.append("Updated dependencies")
    
    return changes if changes else ["Minor updates and fixes"]

def increment_version(version_type: str = 'patch') -> str:
    """Increment version and update version.py file"""
    version_file = 'version.py'
    
    # Read current version
    with open(version_file, 'r') as f:
        content = f.read()
    
    # Extract current version numbers
    major_matches = re.findall(r'__major_version__ = (\d+)', content)
    minor_matches = re.findall(r'__minor_version__ = (\d+)', content)
    patch_matches = re.findall(r'__patch_version__ = (\d+)', content)
    
    if not all([major_matches, minor_matches, patch_matches]):
        raise ValueError("Could not find version numbers in version.py")
    
    major = int(major_matches[0])
    minor = int(minor_matches[0])
    patch = int(patch_matches[0])
    
    # Increment based on type
    if version_type == 'major':
        major += 1
        minor = 0
        patch = 0
    elif version_type == 'minor':
        minor += 1
        patch = 0
    else:  # patch
        patch += 1
    
    new_version = f"{major}.{minor}.{patch}"
    
    # Generate changelog entries
    changelog_entries = generate_changelog()
    
    # Update version.py
    new_content = re.sub(r'__version__ = "[^"]+"', f'__version__ = "{new_version}"', content)
    new_content = re.sub(r'__major_version__ = \d+', f'__major_version__ = {major}', new_content)
    new_content = re.sub(r'__minor_version__ = \d+', f'__minor_version__ = {minor}', new_content)
    new_content = re.sub(r'__patch_version__ = \d+', f'__patch_version__ = {patch}', new_content)
    
    # Add new changelog entry with proper formatting
    changelog_str = '[\n        "' + '",\n        "'.join(changelog_entries) + '"\n    ]'
    changelog_pattern = r'(__changelog__ = \{\s*)("[^"]+": \[)'
    changelog_replacement = f'\\1"{new_version}": {changelog_str},\n    \\2'
    new_content = re.sub(changelog_pattern, changelog_replacement, new_content)
    
    with open(version_file, 'w') as f:
        f.write(new_content)
    
    return new_version

if __name__ == "__main__":
    version_type = sys.argv[1] if len(sys.argv) > 1 else 'patch'
    
    if version_type not in ['major', 'minor', 'patch']:
        print("Usage: python generate_changelog.py [major|minor|patch]")
        sys.exit(1)
    
    new_version = increment_version(version_type)
    print(f"Updated to version {new_version}")
    
    changelog = generate_changelog()
    print("\nGenerated changelog entries:")
    for entry in changelog:
        print(f"- {entry}")