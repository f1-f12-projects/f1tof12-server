from scripts.db.dynamodb_adapters.user_dynamodb_adapter import UserDynamoDBAdapter
from scripts.db.dynamodb_adapters.company_dynamodb_adapter import CompanyDynamoDBAdapter
from scripts.db.dynamodb_adapters.spoc_dynamodb_adapter import SPOCDynamoDBAdapter
from scripts.db.dynamodb_adapters.invoice_dynamodb_adapter import InvoiceDynamoDBAdapter
from scripts.db.dynamodb_adapters.requirement_dynamodb_adapter import RequirementDynamoDBAdapter
from scripts.db.dynamodb_adapters.candidate_dynamodb_adapter import CandidateDynamoDBAdapter
from scripts.db.dynamodb_adapters.process_profile_dynamodb_adapter import ProcessProfileDynamoDBAdapter

class DynamoDBAdapter:
    def __init__(self):
        self.user = UserDynamoDBAdapter()
        self.company = CompanyDynamoDBAdapter()
        self.spoc = SPOCDynamoDBAdapter()
        self.invoice = InvoiceDynamoDBAdapter()
        self.requirement = RequirementDynamoDBAdapter()
        self.candidate = CandidateDynamoDBAdapter()
        self.process_profile = ProcessProfileDynamoDBAdapter()