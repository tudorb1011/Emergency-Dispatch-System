from models import *
from state_machine import CallStateMachine
from database import db
import datetime

class EnhancedDispatchService:
    def __init__(self):
        self.cad_system = None
        self._initialize_cad_system()

    def _initialize_cad_system(self):
        self.cad_system = CADSystem.query.first()
        if not self.cad_system:
            self.cad_system = CADSystem()
            db.session.add(self.cad_system)
            db.session.commit()

    def log_emergency_call(self, caller_name, phone, location, emergency_type, dispatcher_id=None):
        call = EmergencyCall(
            caller_name=caller_name,
            phone_number=phone,
            location=location,
            emergency_type=emergency_type
        )
        db.session.add(call)
        db.session.commit()
        self.cad_system.log_call(call)
        return call

    def determine_emergency_type(self, call_details):
        dispatcher = Dispatcher.query.first()
        if dispatcher:
            return dispatcher.determine_emergency_type(call_details)
        if any(word in call_details.lower() for word in ['fire', 'smoke', 'burning']):
            return EmergencyType.FIRE
        elif any(word in call_details.lower() for word in ['medical', 'heart', 'accident', 'injury']):
            return EmergencyType.MEDICAL
        else:
            return EmergencyType.POLICE

    def dispatch_unit(self, call_id, unit_id=None):
        call = EmergencyCall.query.get(call_id)
        if not call:
            raise ValueError("Call not found")
        if call.status != CallStatus.LOGGED:
            raise ValueError(f"Cannot dispatch: call is already in state {call.status.value}")

        if unit_id is not None:
            unit = EmergencyUnit.query.get(unit_id)
            if not unit or not unit.availability_status or unit.service_type != call.emergency_type:
                raise ValueError("Selected unit is not available or not suitable")
        else:
            unit = self._find_best_unit(call.emergency_type)
            if not unit:
                raise ValueError("No units available")

        call.unit = unit
        unit.availability_status = False

        fsm = CallStateMachine(call)
        fsm.transition(CallStatus.DISPATCHED)

        dispatch_cmd = DispatchCommand(
            command_id=f"DISPATCH-{call.id}-{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}",
            details=f"Dispatching {unit.unit_id} to {call.location} for {call.emergency_type.value} emergency"
        )
        db.session.add(dispatch_cmd)
        db.session.commit()
        self.cad_system.dispatch_emergency(dispatch_cmd)
        return unit

    def _find_best_unit(self, emergency_type):
        return EmergencyUnit.query.filter_by(
            service_type=emergency_type,
            availability_status=True
        ).first()

    def update_unit_status(self, call_id, new_status):
        call = EmergencyCall.query.get(call_id)
        if not call:
            raise ValueError("Call not found")
        fsm = CallStateMachine(call)
        fsm.transition(new_status)
        if new_status == CallStatus.COMPLETED and call.unit:
            call.unit.availability_status = True
        db.session.commit()

    def submit_intervention_report(self, call_id, report_data):
        report = InterventionReport(
            call_id=call_id,
            details=report_data
        )
        db.session.add(report)
        db.session.commit()
        return report

    def get_system_statistics(self):
        stats_obj = Statistics()
        return stats_obj.calculate_metrics()