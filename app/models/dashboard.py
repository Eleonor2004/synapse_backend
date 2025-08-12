from pydantic import BaseModel

class UserDashboardStats(BaseModel):
    """
    Defines the statistical data for a single user's dashboard.
    """
    total_analyses: int
    total_records_processed: int
    # We can add more stats here in the future, like:
    # total_unique_contacts: int
    # most_active_day: Optional[date] = None