from models import EmergencyCall, CallStatus, InterventionReport

class ReportingService:
    def get_summary(self):
        return {
            "total_calls": EmergencyCall.query.count(),
            "completed_calls": EmergencyCall.query.filter_by(status=CallStatus.COMPLETED).count(),
            "reports_submitted": InterventionReport.query.count()
        }
