from scripts.db.adapters.user_adapter import UserAdapter
from scripts.db.adapters.company_adapter import CompanyAdapter
from scripts.db.adapters.spoc_adapter import SPOCAdapter
from scripts.db.adapters.invoice_adapter import InvoiceAdapter
from scripts.db.adapters.requirement_adapter import RequirementAdapter
from scripts.db.adapters.profile_adapter import ProfileAdapter
from scripts.db.adapters.process_profile_adapter import ProcessProfileAdapter
from scripts.db.adapters.leave_adapter import LeaveAdapter
from scripts.db.adapters.financial_year_adapter import FinancialYearAdapter
from scripts.db.adapters.holiday_adapter import HolidayAdapter

class SQLiteAdapter:
    def __init__(self):
        self.user = UserAdapter()
        self.company = CompanyAdapter()
        self.spoc = SPOCAdapter()
        self.invoice = InvoiceAdapter()
        self.requirement = RequirementAdapter()
        self.profile = ProfileAdapter()
        self.process_profile = ProcessProfileAdapter()
        self.leave = LeaveAdapter()
        self.financial_year = FinancialYearAdapter()
        self.holiday = HolidayAdapter()