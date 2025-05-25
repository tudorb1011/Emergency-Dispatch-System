from database import db
from sqlalchemy import Enum
import enum
import datetime


class EmergencyType(enum.Enum):
    POLICE = "police"
    FIRE = "fire"
    MEDICAL = "medical"


class CallStatus(enum.Enum):
    LOGGED = "logged"
    DISPATCHED = "dispatched"
    EN_ROUTE = "en_route"
    ON_SCENE = "on_scene"
    COMPLETED = "completed"


class EmergencyUnit(db.Model):
    __tablename__ = 'emergency_unit'

    id = db.Column(db.Integer, primary_key=True)
    unit_id = db.Column(db.String(50), unique=True, nullable=False)  # unitID from UML
    service_type = db.Column(db.Enum(EmergencyType), nullable=False)  # serviceType from UML
    availability_status = db.Column(db.Boolean, default=True)  # availabilityStatus from UML
    intervention_report = db.Column(db.String(500))  # interventionReport from UML
    last_update = db.Column(db.DateTime, default=datetime.datetime.utcnow)  # lastUpdate from UML

    # Relationships
    calls = db.relationship("EmergencyCall", back_populates="unit")

    def update_status(self, new_status):
        """Update the availability status of the unit"""
        self.availability_status = new_status
        self.last_update = datetime.datetime.utcnow()
        db.session.commit()

    def submit_report(self, report_details):
        """Submit an intervention report"""
        self.intervention_report = report_details
        db.session.commit()


class EmergencyCall(db.Model):
    __tablename__ = 'emergency_call'

    id = db.Column(db.Integer, primary_key=True)
    caller_name = db.Column(db.String(100), nullable=False)
    phone_number = db.Column(db.String(20), nullable=False)
    location = db.Column(db.String(200), nullable=False)
    emergency_type = db.Column(db.Enum(EmergencyType), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    status = db.Column(db.Enum(CallStatus), default=CallStatus.LOGGED)

    # Foreign key and relationship
    unit_id = db.Column(db.Integer, db.ForeignKey('emergency_unit.id'))
    unit = db.relationship("EmergencyUnit", back_populates="calls")

    # Relationship to reports
    reports = db.relationship("InterventionReport", back_populates="call")

    def create_call(self):
        """Create a new emergency call"""
        db.session.add(self)
        db.session.commit()
        return self

class InterventionReport(db.Model):
        __tablename__ = 'intervention_report'

        id = db.Column(db.Integer, primary_key=True)
        call_id = db.Column(db.Integer, db.ForeignKey('emergency_call.id'), nullable=True)  # <-- allow NULL
        details = db.Column(db.Text, nullable=False)
        timestamp = db.Column(db.DateTime, default=datetime.datetime.utcnow)

        # Relationship
        call = db.relationship("EmergencyCall", back_populates="reports")

class Dispatcher(db.Model):
    __tablename__ = 'dispatcher'

    id = db.Column(db.Integer, primary_key=True)
    dispatcher_id = db.Column(db.String(50), unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    shift_start = db.Column(db.DateTime)
    shift_end = db.Column(db.DateTime)

    def log_emergency_call(self, caller_name, phone, location, emergency_type):
        """Log a new emergency call"""
        call = EmergencyCall(
            caller_name=caller_name,
            phone_number=phone,
            location=location,
            emergency_type=emergency_type
        )
        return call.create_call()

    def determine_emergency_type(self, call_details):
        """Determine the type of emergency based on call details"""
        # Simple logic - in real system this would be more sophisticated
        if any(word in call_details.lower() for word in ['fire', 'smoke', 'burning']):
            return EmergencyType.FIRE
        elif any(word in call_details.lower() for word in ['medical', 'heart', 'accident', 'injury']):
            return EmergencyType.MEDICAL
        else:
            return EmergencyType.POLICE

    def assign_unit(self, call_id, unit_id):
        """Assign a unit to an emergency call"""
        call = EmergencyCall.query.get(call_id)
        unit = EmergencyUnit.query.filter_by(unit_id=unit_id).first()

        if call and unit and unit.availability_status:
            call.unit = unit
            call.status = CallStatus.DISPATCHED
            unit.availability_status = False
            db.session.commit()
            return True
        return False

    def log_incident_report(self, report_data):
        """Log an incident report"""
        # Implementation for logging incident reports
        pass

    def submit_intervention_report(self, call_id, report_data):
        """Submit intervention report"""
        report = InterventionReport(
            call_id=call_id,
            details=report_data
        )
        db.session.add(report)
        db.session.commit()
        return report


class DispatchCommand(db.Model):
    __tablename__ = 'dispatch_command'

    id = db.Column(db.Integer, primary_key=True)
    command_id = db.Column(db.String(50), unique=True, nullable=False)
    report_id = db.Column(db.String(50))
    details = db.Column(db.Text)
    response_times = db.Column(db.JSON)  # Store list of response times
    timestamp = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    workload_distribution = db.Column(db.JSON)  # Map of unit workloads

    def create_dispatch(self):
        """Create a new dispatch command"""
        db.session.add(self)
        db.session.commit()
        return self


class CADSystem(db.Model):
    __tablename__ = 'cad_system'

    id = db.Column(db.Integer, primary_key=True)
    call_log = db.Column(db.JSON)  # List of emergency calls
    dispatch_commands = db.Column(db.JSON)  # List of dispatch commands
    unit_reports = db.Column(db.JSON)  # List of unit reports
    statistics = db.Column(db.JSON)  # System statistics
    last_updated = db.Column(db.DateTime, default=datetime.datetime.utcnow)

    def log_call(self, emergency_call):
        """Log an emergency call in the CAD system"""
        if not self.call_log:
            self.call_log = []

        call_data = {
            'id': emergency_call.id,
            'caller_name': emergency_call.caller_name,
            'location': emergency_call.location,
            'type': emergency_call.emergency_type.value,
            'timestamp': emergency_call.timestamp.isoformat()
        }

        self.call_log.append(call_data)
        self.last_updated = datetime.datetime.utcnow()
        db.session.commit()

    def dispatch_emergency(self, dispatch_command):
        """Process emergency dispatch"""
        if not self.dispatch_commands:
            self.dispatch_commands = []

        command_data = {
            'command_id': dispatch_command.command_id,
            'details': dispatch_command.details,
            'timestamp': dispatch_command.timestamp.isoformat()
        }

        self.dispatch_commands.append(command_data)
        db.session.commit()

    def generate_statistics(self):
        """Generate system statistics"""
        stats = {
            'total_calls': EmergencyCall.query.count(),
            'active_calls': EmergencyCall.query.filter(
                EmergencyCall.status.in_([CallStatus.DISPATCHED, CallStatus.EN_ROUTE, CallStatus.ON_SCENE])
            ).count(),
            'completed_calls': EmergencyCall.query.filter_by(status=CallStatus.COMPLETED).count(),
            'available_units': EmergencyUnit.query.filter_by(availability_status=True).count(),
            'total_units': EmergencyUnit.query.count(),
            'reports_filed': InterventionReport.query.count()
        }

        self.statistics = stats
        self.last_updated = datetime.datetime.utcnow()
        db.session.commit()
        return stats


# Specialized Unit Classes (inheriting from EmergencyUnit)
class EMSUnit(EmergencyUnit):
    __tablename__ = 'ems_unit'

    id = db.Column(db.Integer, db.ForeignKey('emergency_unit.id'), primary_key=True)
    medical_equipment = db.Column(db.JSON)  # List of available medical equipment
    paramedic_count = db.Column(db.Integer, default=2)

    __mapper_args__ = {
        'polymorphic_identity': 'ems_unit'
    }


class FireUnit(EmergencyUnit):
    __tablename__ = 'fire_unit'

    id = db.Column(db.Integer, db.ForeignKey('emergency_unit.id'), primary_key=True)
    firefighter_count = db.Column(db.Integer, default=4)
    equipment_list = db.Column(db.JSON)  # Fire fighting equipment

    __mapper_args__ = {
        'polymorphic_identity': 'fire_unit'
    }


class PoliceUnit(EmergencyUnit):
    __tablename__ = 'police_unit'

    id = db.Column(db.Integer, db.ForeignKey('emergency_unit.id'), primary_key=True)
    officer_count = db.Column(db.Integer, default=2)
    patrol_area = db.Column(db.String(100))

    __mapper_args__ = {
        'polymorphic_identity': 'police_unit'
    }


class Statistics(db.Model):
    __tablename__ = 'statistics'

    id = db.Column(db.Integer, primary_key=True)
    metric_data = db.Column(db.JSON)  # Map of various metrics
    generated_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)

    def calculate_metrics(self):
        """Calculate various system metrics"""
        metrics = {
            'response_times': self._calculate_response_times(),
            'call_volume_by_type': self._call_volume_by_type(),
            'unit_utilization': self._unit_utilization(),
            'completion_rate': self._completion_rate()
        }

        self.metric_data = metrics
        self.generated_at = datetime.datetime.utcnow()
        db.session.commit()
        return metrics

    def _calculate_response_times(self):
        """Calculate average response times"""
        # Implementation for response time calculation
        return {"average": 8.5, "median": 7.2, "max": 15.3}

    def _call_volume_by_type(self):
        """Calculate call volume by emergency type"""
        police_calls = EmergencyCall.query.filter_by(emergency_type=EmergencyType.POLICE).count()
        fire_calls = EmergencyCall.query.filter_by(emergency_type=EmergencyType.FIRE).count()
        medical_calls = EmergencyCall.query.filter_by(emergency_type=EmergencyType.MEDICAL).count()

        return {
            "police": police_calls,
            "fire": fire_calls,
            "medical": medical_calls
        }

    def _unit_utilization(self):
        """Calculate unit utilization rates"""
        total_units = EmergencyUnit.query.count()
        busy_units = EmergencyUnit.query.filter_by(availability_status=False).count()

        return {
            "total": total_units,
            "busy": busy_units,
            "utilization_rate": (busy_units / total_units * 100) if total_units > 0 else 0
        }

    def _completion_rate(self):
        """Calculate call completion rate"""
        total_calls = EmergencyCall.query.count()
        completed_calls = EmergencyCall.query.filter_by(status=CallStatus.COMPLETED).count()

        return {
            "total": total_calls,
            "completed": completed_calls,
            "completion_rate": (completed_calls / total_calls * 100) if total_calls > 0 else 0
        }
