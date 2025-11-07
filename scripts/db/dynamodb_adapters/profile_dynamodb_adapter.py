from typing import Optional, List, Dict, Any
from botocore.exceptions import ClientError
from scripts.db.config import PROFILES_TABLE, PROFILE_STATUSES_TABLE
from .base_dynamodb_adapter import BaseDynamoDBAdapter

class ProfileDynamoDBAdapter(BaseDynamoDBAdapter):
    def __init__(self):
        super().__init__()
        self.profiles_table = self.dynamodb.Table(PROFILES_TABLE)
        self.profile_statuses_table = self.dynamodb.Table(PROFILE_STATUSES_TABLE)
    
    def create_profile(self, profile_data: Dict[str, Any]) -> Dict[str, Any]:
        from decimal import Decimal
        from datetime import date, datetime
        from zoneinfo import ZoneInfo
        
        profile_id = self._get_next_id('profiles')
        profile_data['id'] = profile_id
        
        # Add timestamps
        now = datetime.now(ZoneInfo('Asia/Kolkata'))
        profile_data['created_date'] = now.isoformat()
        profile_data['updated_date'] = now.isoformat()
        
        # Convert float and date values for DynamoDB compatibility
        for key, value in profile_data.items():
            if isinstance(value, float):
                profile_data[key] = Decimal(str(value))
            elif isinstance(value, (date, datetime)) and key not in ['created_date', 'updated_date']:
                profile_data[key] = value.isoformat()
        
        self.profiles_table.put_item(Item=profile_data)
        return profile_data
    
    def list_profiles(self) -> List[Dict[str, Any]]:
        try:
            response = self.profiles_table.scan()
            return response.get('Items', [])
        except ClientError:
            return []
    
    def get_profile(self, profile_id: int) -> Optional[Dict[str, Any]]:
        try:
            from decimal import Decimal
            response = self.profiles_table.get_item(Key={'id': Decimal(str(profile_id))})
            return response.get('Item')
        except ClientError:
            return None
    
    def update_profile(self, profile_id: int, update_data: Dict[str, Any]) -> bool:
        try:
            from decimal import Decimal
            from datetime import date, datetime
            from zoneinfo import ZoneInfo
            
            # Add updated_date timestamp
            update_data['updated_date'] = datetime.now(ZoneInfo('Asia/Kolkata')).isoformat()
            
            update_expression = "SET "
            expression_values = {}
            expression_names = {}
            
            # DynamoDB reserved keywords that need ExpressionAttributeNames
            reserved_keywords = {'location', 'status', 'role', 'name', 'date', 'time'}
            
            for key, value in update_data.items():
                # Convert float and date values for DynamoDB compatibility
                if isinstance(value, float):
                    value = Decimal(str(value))
                elif isinstance(value, (date, datetime)) and key != 'updated_date':
                    value = value.isoformat()
                
                # Handle reserved keywords
                if key.lower() in reserved_keywords:
                    attr_name = f"#{key}"
                    expression_names[attr_name] = key
                    update_expression += f"{attr_name} = :{key}, "
                else:
                    update_expression += f"{key} = :{key}, "
                
                expression_values[f":{key}"] = value
            
            update_expression = update_expression.rstrip(', ')
            
            update_params = {
                'Key': {'id': Decimal(str(profile_id))},
                'UpdateExpression': update_expression,
                'ExpressionAttributeValues': expression_values
            }
            
            if expression_names:
                update_params['ExpressionAttributeNames'] = expression_names
            
            self.profiles_table.update_item(**update_params)
            return True
        except ClientError:
            return False
    
    def list_profile_statuses(self) -> List[Dict[str, Any]]:
        try:
            response = self.profile_statuses_table.scan()
            return response.get('Items', [])
        except ClientError:
            return []
    
    def get_profiles_by_date_range(self, start_date, end_date, recruiter_name=None) -> List[Dict[str, Any]]:
        try:
            import logging
            from scripts.db.config import PROCESS_PROFILES_TABLE, REQUIREMENTS_TABLE, COMPANIES_TABLE
            from decimal import Decimal
            
            # Filter by date range using DynamoDB FilterExpression
            start_str = start_date.isoformat()
            end_str = (end_date.replace(hour=23, minute=59, second=59) if hasattr(end_date, 'hour') else end_date).isoformat() + 'T23:59:59'
            
            response = self.profiles_table.scan(
                FilterExpression='#created_date BETWEEN :start_date AND :end_date',
                ExpressionAttributeNames={'#created_date': 'created_date'},
                ExpressionAttributeValues={
                    ':start_date': start_str,
                    ':end_date': end_str
                }
            )
            filtered_profiles = response.get('Items', [])
            logging.info(f"Filtered profiles count: {len(filtered_profiles)}")
            
            # Get profile IDs from filtered profiles
            profile_ids = []
            for profile in filtered_profiles:
                pid = profile.get('id')
                if isinstance(pid, Decimal):
                    pid = int(pid)
                profile_ids.append(pid)
            
            # Get process profiles only for filtered profile IDs
            process_profiles_table = self.dynamodb.Table(PROCESS_PROFILES_TABLE)
            process_profiles = self._batch_scan_by_ids(process_profiles_table, profile_ids, 'profile_id')
            
            # Get unique requirement IDs from process profiles
            requirement_ids = set()
            for pp in process_profiles.values():
                req_id = pp.get('requirement_id')
                if req_id:
                    if isinstance(req_id, Decimal):
                        req_id = int(req_id)
                    requirement_ids.add(req_id)
            
            # Get requirements only for the ones we need
            requirements_table = self.dynamodb.Table(REQUIREMENTS_TABLE)
            companies_table = self.dynamodb.Table(COMPANIES_TABLE)
            requirements = self._batch_scan_by_ids(requirements_table, list(requirement_ids), 'requirement_id')
            
            comp_response = companies_table.scan()
            companies = {}
            for comp in comp_response.get('Items', []):
                comp_id = comp.get('id')
                if isinstance(comp_id, Decimal):
                    comp_id = int(comp_id)
                companies[comp_id] = comp.get('name')
            
            logging.info(f"Process profiles mapped: {len(process_profiles)}")
            
            result = []
            for profile in filtered_profiles:
                try:
                    pid = profile.get('id')
                    logging.info(f"Processing profile id: {pid}, type: {type(pid)}")
                    if isinstance(pid, Decimal):
                        pid = int(pid)
                    
                    status = profile.get('status', 1)
                    logging.info(f"Profile status: {status}, type: {type(status)}")
                    if isinstance(status, Decimal):
                        status = int(status)
                    
                    pp_data = process_profiles.get(pid, {})
                    profile_recruiter = pp_data.get('recruiter_name')
                    
                    # Filter by recruiter if provided
                    if recruiter_name and profile_recruiter != recruiter_name:
                        continue
                    
                    req_id = pp_data.get('requirement_id')
                    logging.info(f"Requirement id: {req_id}, type: {type(req_id)}")
                    if isinstance(req_id, Decimal):
                        req_id = int(req_id)
                    
                    # Get company name from requirement
                    company_name = None
                    if req_id and req_id in requirements:
                        company_id = requirements[req_id].get('company_id')
                        if isinstance(company_id, Decimal):
                            company_id = int(company_id)
                        company_name = companies.get(company_id)
                    
                    result.append({
                        'profile_id': pid,
                        'status': status,
                        'name': profile.get('name'),
                        'recruiter_name': profile_recruiter,
                        'requirement_id': req_id,
                        'company_name': company_name
                    })
                except Exception as e:
                    logging.error(f"Error processing profile: {e}")
                    continue
            
            logging.info(f"Final result count: {len(result)}")
            return result
        except Exception as e:
            import logging
            logging.error(f"Error in get_profiles_by_date_range: {e}")
            return []