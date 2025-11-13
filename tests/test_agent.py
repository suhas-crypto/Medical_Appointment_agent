from backend.agent.scheduling_agent import SchedulingAgent
def test_greeting_and_flow():
    a = SchedulingAgent()
    resp, ctx = a.handle_message('user1','I need to book',{})
    assert 'schedule' in resp.lower() or 'help' in resp.lower()
    resp, ctx = a.handle_message('user1','Routine checkup', ctx)
    assert 'which type' in resp.lower() or 'appointment' in resp.lower()
