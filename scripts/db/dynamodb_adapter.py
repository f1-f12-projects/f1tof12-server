from scripts.db.dynamodb_adapters.user_dynamodb_adapter import UserDynamoDBAdapter
from scripts.db.dynamodb_adapters.company_dynamodb_adapter import CompanyDynamoDBAdapter
from scripts.db.dynamodb_adapters.spoc_dynamodb_adapter import SPOCDynamoDBAdapter
from scripts.db.dynamodb_adapters.invoice_dynamodb_adapter import InvoiceDynamoDBAdapter
from scripts.db.dynamodb_adapters.requirement_dynamodb_adapter import RequirementDynamoDBAdapter
from scripts.db.dynamodb_adapters.profile_dynamodb_adapter import ProfileDynamoDBAdapter
from scripts.db.dynamodb_adapters.process_profile_dynamodb_adapter import ProcessProfileDynamoDBAdapter
from scripts.db.dynamodb_adapters.leave_dynamodb_adapter import LeaveDynamoDBAdapter
from scripts.db.dynamodb_adapters.financial_year_dynamodb_adapter import FinancialYearDynamoDBAdapter
from scripts.db.dynamodb_adapters.holiday_dynamodb_adapter import HolidayDynamoDBAdapter

class DynamoDBAdapter:
    def __init__(self):
        self.user = UserDynamoDBAdapter()
        self.company = CompanyDynamoDBAdapter()
        self.spoc = SPOCDynamoDBAdapter()
        self.invoice = InvoiceDynamoDBAdapter()
        self.requirement = RequirementDynamoDBAdapter()
        self.profile = ProfileDynamoDBAdapter()
        self.process_profile = ProcessProfileDynamoDBAdapter()
        self.leave = LeaveDynamoDBAdapter()
        self.financial_year = FinancialYearDynamoDBAdapter()
        self.holiday = HolidayDynamoDBAdapter()