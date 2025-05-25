from models import *
from state_machine import CallStateMachine
from database import db
import datetime

class CADService:
    def __init__(self):
        self.cad_system = self._get_cad_system()

    def _get_cad_system(self):
        """Get or create CAD system instance"""
        cad = CADSystem.query.first()
        if not cad:
            cad = CADSystem()
            db.session.add(cad)
            db.session.commit()
        return cad

    def get_active_calls(self):
        """Get all active emergency calls"""
        return EmergencyCall.query.filter(
            EmergencyCall.status.in_([
                CallStatus.LOGGED,
                CallStatus.DISPATCHED,
                CallStatus.EN_ROUTE,
                CallStatus.ON_SCENE
            ])
        ).all()

    def get_unit_status(self):
        """Get status of all emergency units"""
        return EmergencyUnit.query.all()

    def generate_real_time_statistics(self):
        """Generate real-time system statistics"""
        return self.cad_system.generate_statistics()