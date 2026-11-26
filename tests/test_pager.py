import json
import threading
import urllib.request
from http.server import ThreadingHTTPServer

from pager.render import HEIGHT, WIDTH, render
from pager.server import make_handler
from pager.state import State

NOW = 1_800_000_000.0


def make_state(tmp_path):
    return State(tmp_path / "state.json")


def hook(state, event, sid="s1", cwd="/x/web-app", **extra):
    state.apply_hook({"hook_event_name": event, "session_id": sid, "cwd": cwd, **extra}, now=NOW)


def test_session_lifecycle(tmp_path):
    st = make_state(tmp_path)
    hook(st, "UserPromptSubmit")
    assert st.active_sessions(NOW)[0]["status"] == "working"
    hook(st, "Notification", message="Claude needs your permission to use Bash")
    s = st.active_sessions(NOW)[0]
    assert (s["status"], s["project"]) == ("waiting", "web-app")
    hook(st, "SessionEnd")
    assert st.active_sessions(NOW) == []


def test_waiting_sorted_first_and_stale_hidden(tmp_path):
    st = make_state(tmp_path)
    hook(st, "UserPromptSubmit", sid="a")
    hook(st, "Notification", sid="b")
    assert [s["id"] for s in st.active_sessions(NOW)] == ["b", "a"]
    assert st.active_sessions(NOW + 7 * 3600) == []


def test_state_persists(tmp_path):
    st = make_state(tmp_path)
    st.set_usage({"five_hour": {"used_percentage": 42}}, now=NOW)
    assert make_state(tmp_path).data["usage"]["five_hour"]["used_percentage"] == 42


def test_render_all_sections(tmp_path):
    st = make_state(tmp_path)
    img = render(st, now=NOW)  # vacío no debe fallar
    st.set_usage({"five_hour": {"used_percentage": 42, "resets_at": NOW + 4800},
                  "seven_day": {"used_percentage": 18}}, now=NOW)
    hook(st, "Notification", message="needs permission " * 10)
    hook(st, "Stop", sid="s2", cwd="/x/api-server")
    st.set_digest({"next_event": "15:00 Reunión", "needs_you": ["a: b", "c: d"]}, now=NOW)
    img = render(st, now=NOW)
    assert img.size == (WIDTH, HEIGHT) and img.mode == "1"
    assert 0 < sum(1 for p in img.get_flattened_data() if p == 0) < WIDTH * HEIGHT


def test_server_roundtrip(tmp_path):
    st = make_state(tmp_path)
    srv = ThreadingHTTPServer(("127.0.0.1", 0), make_handler(st))
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    base = f"http://127.0.0.1:{srv.server_port}"
    body = json.dumps({"hook_event_name": "Stop", "session_id": "z", "cwd": "/p/q"}).encode()
    urllib.request.urlopen(urllib.request.Request(base + "/hook", data=body)).read()
    assert st.data["sessions"]["z"]["status"] == "done"
    assert urllib.request.urlopen(base + "/frame.bmp").read()[:2] == b"BM"
    srv.shutdown()


def test_short_message():
    from pager.render import short_message
    assert short_message("Claude needs your permission to use Bash") == "permiso: Bash"
    assert short_message("Claude is waiting for your input") == "espera tu respuesta"
