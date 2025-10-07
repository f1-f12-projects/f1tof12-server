from scripts.db.adapters.user_adapter import UserAdapter
from scripts.db.adapters.company_adapter import CompanyAdapter
from scripts.db.adapters.spoc_adapter import SPOCAdapter
from scripts.db.adapters.invoice_adapter import InvoiceAdapter
from scripts.db.adapters.requirement_adapter import RequirementAdapter
from scripts.db.adapters.candidate_adapter import CandidateAdapter
from scripts.db.adapters.process_profile_adapter import ProcessProfileAdapter

class SQLiteAdapter:
    def __init__(self):
        self.user = UserAdapter()
        self.company = CompanyAdapter()
        self.spoc = SPOCAdapter()
        self.invoice = InvoiceAdapter()
        self.requirement = RequirementAdapter()
        self.candidate = CandidateAdapter()
        self.process_profile = ProcessProfileAdapter()