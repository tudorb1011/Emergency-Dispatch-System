from models import EmergencyCall, EmergencyUnit, CallStatus, InterventionReport
from state_machine import CallStateMachine
from database import db

class EmergencyDispatchService:
    def log_call(self, name, phone, location, emergency_type):
        call = EmergencyCall(
            caller_name=name,
            phone_number=phone,
            location=location,
            emergency_type=emergency_type
        )
        db.session.add(call)
        db.session.commit()
        return call

    def dispatch_unit(self, call_id):
        call = EmergencyCall.query.get(call_id)
        if not call:
            raise ValueError("Call not found")
        unit = EmergencyUnit.query.filter_by(unit_type=call.emergency_type, is_available=True).first()
        if not unit:
            raise ValueError("No units available")
        call.unit = unit
        unit.is_available = False
        call.status = CallStatus.DISPATCHED
        db.session.commit()
        return unit

    def update_status(self, call_id, new_status):
        call = EmergencyCall.query.get(call_id)
        fsm = CallStateMachine(call)
        fsm.transition(new_status)
        db.session.commit()

    def submit_report(self, call_id, details):
        report = InterventionReport(call_id=call_id, details=details)
        db.session.add(report)
        db.session.commit()
        return report
