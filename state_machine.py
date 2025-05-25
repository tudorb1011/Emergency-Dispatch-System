from models import CallStatus

class CallStateMachine:
    def __init__(self, call):
        self.call = call

    def transition(self, new_status):
        valid_transitions = {
            CallStatus.LOGGED: [CallStatus.DISPATCHED],
            CallStatus.DISPATCHED: [CallStatus.EN_ROUTE],
            CallStatus.EN_ROUTE: [CallStatus.ON_SCENE],
            CallStatus.ON_SCENE: [CallStatus.COMPLETED],
        }
        # Allow transition to COMPLETED from any state except COMPLETED itself
        if new_status == CallStatus.COMPLETED and self.call.status != CallStatus.COMPLETED:
            self.call.status = new_status
        elif new_status in valid_transitions.get(self.call.status, []):
            self.call.status = new_status
        else:
            raise ValueError(f"Invalid transition from {self.call.status} to {new_status}")