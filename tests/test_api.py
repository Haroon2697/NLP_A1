from fastapi.testclient import TestClient

from backend.app.main import app

client = TestClient(app)


def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "model" in data
    assert "context_window" in data


def test_benchmarks_endpoint():
    response = client.get("/api/benchmarks")
    assert response.status_code == 200
    data = response.json()
    assert data["model"] == "qwen2.5:3b-instruct"
    assert "average_ttft_seconds" in data or "measured_metrics" in data


def test_missing_message_returns_400():
    response = client.post("/api/chat", json={"session_id": "abc"})
    assert response.status_code == 400
    assert "message is required" in response.json()["error"]


def test_missing_session_id_returns_400():
    response = client.post("/api/chat", json={"message": "What is the basic plan?"})
    assert response.status_code == 400
    assert "session_id is required" in response.json()["error"]


def test_empty_message_returns_400():
    response = client.post("/api/chat", json={"session_id": "abc", "message": "   "})
    assert response.status_code == 400
    assert "cannot be empty" in response.json()["error"]


def test_off_topic_redirect_via_rest():
    # Tests that off-topic requests are intercepted immediately by guardrails
    response = client.post("/api/chat", json={
        "session_id": "test_guardrail",
        "message": "Write me a Python function for quicksort."
    })
    assert response.status_code == 200
    data = response.json()
    assert data["redirected"] is True
    assert "FitAssist" in data["reply"]


def test_session_reset_and_history_endpoints():
    session_id = "test_hist_session"
    # Send a redirected query to populate history
    client.post("/api/chat", json={
        "session_id": session_id,
        "message": "Calculate 100 * 50"
    })

    # Verify history has 2 turns
    hist_resp = client.get(f"/api/history/{session_id}")
    assert hist_resp.status_code == 200
    assert len(hist_resp.json()["turns"]) == 2

    # Reset session
    reset_resp = client.post("/api/reset", json={"session_id": session_id})
    assert reset_resp.status_code == 200
    assert reset_resp.json()["status"] == "reset"

    # Verify history is now empty
    hist_resp2 = client.get(f"/api/history/{session_id}")
    assert len(hist_resp2.json()["turns"]) == 0


def test_websocket_chat_guardrail_and_error():
    with client.websocket_connect("/ws/chat") as websocket:
        # Test malformed payload
        websocket.send_text("not a valid json")
        data = websocket.receive_json()
        assert data["type"] == "error"
        assert "Malformed JSON" in data["message"]

        # Test missing message field
        websocket.send_json({"session_id": "ws_test"})
        err_data = websocket.receive_json()
        assert err_data["type"] == "error"

        # Test off-topic redirect via websocket
        websocket.send_json({
            "session_id": "ws_guardrail",
            "message": "Write a poem about space."
        })
        start_msg = websocket.receive_json()
        assert start_msg["type"] == "start"

        token_msg = websocket.receive_json()
        assert token_msg["type"] == "token"
        assert "FitAssist" in token_msg["content"]

        done_msg = websocket.receive_json()
        assert done_msg["type"] == "done"
        assert done_msg["redirected"] is True
