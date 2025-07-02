# Emergency Dispatching Center - CAD System (Python)

This project is a Python-based simulation and analysis model of a **Computer-Aided Dispatch (CAD)** system used in emergency services. It represents the core business operations of an Emergency Dispatching Center, including call intake, unit dispatching, intervention tracking, and statistical reporting.

## Features

- **Emergency Call Logging** – Captures caller details and logs calls in the system.
- **Automated Classification** – Identifies and categorizes emergencies (Police, Fire, Medical).
- **Dispatch Operations** – Assigns and notifies appropriate emergency units.
- **Real-Time Updates** – Tracks unit status through various lifecycle stages.
- **Incident & Intervention Reporting** – Logs detailed records post-response.
- **Statistical Dashboard** – Generates insights on response time and workload distribution.

## Technologies

- Python 3.x
- Object-Oriented Design
- UML-based Modeling (Use Case, Sequence, Activity Diagrams)
- Modular Architecture Pattern

##  Structure

- `dispatcher.py` – Handles call logging and dispatch coordination.
- `cad_system.py` – Manages core data structures and business logic.
- `emergency_units/` – Contains unit classes for Police, Fire, and EMS.
- `reports/` – Facilitates statistics generation and incident reporting.


##  Use Case Examples

1. Caller initiates an emergency call.
2. Dispatcher logs the call and determines the emergency type.
3. CAD system dispatches the nearest appropriate unit.
4. Unit acknowledges, updates status, and submits a final report.
5. System generates response metrics for external review.

---

For academic modeling and system architecture demonstration purposes only.
