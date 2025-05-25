from flask import Flask, request, jsonify, render_template, redirect, url_for, current_app, send_file
from config import Config
from database import db
from models import *
from services.enhanced_dispatch_service import EnhancedDispatchService
from services.cad_service import CADService
import io
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

app = Flask(__name__)
app.config.from_object(Config)
db.init_app(app)

with app.app_context():
    db.create_all()

    # DEVELOPMENT ONLY: Clear all units for a fresh start
    EmergencyUnit.query.delete()
    db.session.commit()

    # Add 5 units per type if none exist
    if EmergencyUnit.query.count() == 0:
        for i in range(1, 6):
            db.session.add(EmergencyUnit(unit_id=f"POLICE-{i:02d}", service_type=EmergencyType.POLICE))
        for i in range(1, 6):
            db.session.add(EmergencyUnit(unit_id=f"FIRE-{i:02d}", service_type=EmergencyType.FIRE))
        for i in range(1, 6):
            db.session.add(EmergencyUnit(unit_id=f"EMS-{i:02d}", service_type=EmergencyType.MEDICAL))
        db.session.commit()

    # Only add dispatcher if not already present
    if not Dispatcher.query.filter_by(dispatcher_id="DISP-001").first():
        dispatcher = Dispatcher(
            dispatcher_id="DISP-001",
            name="John Dispatcher"
        )
        db.session.add(dispatcher)
        db.session.commit()

    app.dispatch_service = EnhancedDispatchService()
    app.cad_service = CADService()

@app.route("/")
def index():
    active_calls = current_app.cad_service.get_active_calls()
    available_units = current_app.cad_service.get_unit_status()
    stats = current_app.cad_service.generate_real_time_statistics()
    return render_template("dashboard.html",
                           active_calls=active_calls,
                           available_units=available_units,
                           stats=stats)

@app.route("/log_call", methods=["GET", "POST"])
def log_call():
    if request.method == "POST":
        data = request.form
        call = current_app.dispatch_service.log_emergency_call(
            caller_name=data["caller_name"],
            phone=data["phone_number"],
            location=data["location"],
            emergency_type=EmergencyType[data["emergency_type"]]
        )
        return redirect(url_for("index"))
    return render_template("log_call.html")

@app.route("/select_unit/<int:call_id>")
def select_unit(call_id):
    call = EmergencyCall.query.get_or_404(call_id)
    units = EmergencyUnit.query.filter_by(availability_status=True).all()
    return render_template("select_unit.html", call=call, units=units)

@app.route("/dispatch/<int:call_id>/<int:unit_id>")
def dispatch_unit(call_id, unit_id):
    try:
        unit = current_app.dispatch_service.dispatch_unit(call_id, unit_id)
        return redirect(url_for("index"))
    except Exception as e:
        return render_template("error.html", message=str(e)), 400

@app.route("/update_status/<int:call_id>", methods=["POST"])
def update_status(call_id):
    try:
        new_status = CallStatus[request.json["status"]]
        current_app.dispatch_service.update_unit_status(call_id, new_status)
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 400

@app.route("/submit_report/<int:call_id>", methods=["POST"])
def submit_report(call_id):
    try:
        report_data = request.json["details"]
        report = current_app.dispatch_service.submit_intervention_report(call_id, report_data)
        return jsonify({"success": True, "report_id": report.id})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 400

@app.route("/statistics")
def statistics():
    stats = current_app.dispatch_service.get_system_statistics()
    return jsonify(stats)

@app.route("/statistics_page")
def statistics_page():
    stats = current_app.dispatch_service.get_system_statistics()
    return render_template("statistics.html", stats=stats)

@app.route("/api/calls")
def api_calls():
    calls = EmergencyCall.query.all()
    return jsonify([{
        "id": call.id,
        "caller_name": call.caller_name,
        "location": call.location,
        "emergency_type": call.emergency_type.value,
        "status": call.status.value,
        "timestamp": call.timestamp.isoformat(),
        "unit_id": call.unit.unit_id if call.unit else None
    } for call in calls])

@app.route("/api/units")
def api_units():
    units = EmergencyUnit.query.all()
    return jsonify([{
        "id": unit.id,
        "unit_id": unit.unit_id,
        "service_type": unit.service_type.value,
        "available": unit.availability_status
    } for unit in units])

@app.route("/call/<int:call_id>")
def view_call(call_id):
    call = EmergencyCall.query.get_or_404(call_id)
    return render_template("view_call.html", call=call)

@app.route("/generate_report")
def generate_report():
    stats = current_app.dispatch_service.get_system_statistics()
    buffer = io.BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=letter)
    pdf.setTitle("System Statistics Report")
    pdf.setFont("Helvetica-Bold", 16)
    pdf.drawString(72, 750, "System Statistics Report")
    pdf.setFont("Helvetica", 12)
    y = 720
    for key, value in stats.items():
        pdf.drawString(72, y, f"{key}: {value}")
        y -= 20
        if y < 100:
            pdf.showPage()
            y = 750
    pdf.save()
    buffer.seek(0)
    current_app.dispatch_service.submit_intervention_report(
        call_id=None,
        report_data="System statistics PDF generated"
    )
    return send_file(
        buffer,
        mimetype="application/pdf",
        as_attachment=True,
        download_name="system_statistics.pdf"
    )

if __name__ == "__main__":
    app.run(debug=True)