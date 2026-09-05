import time
from app.features.windows import WindowManager

def test_window_manager_flush_expired_types():
    manager = WindowManager()
    
    event = {
        "service_id": "cart",
        "namespace": "production",
        "pod": "cart-5cc",
        "timestamp": "2026-09-02T10:00:00Z",
        "source": "kubernetes"
    }
    
    manager.add_event(event)

    try:
        # Pass a future timestamp that forces the window to definitely expire.
        # This will trigger the arithmetic line: current_ts > w_start + ws_sec + buffer
        flush_results = manager.flush_expired(current_ts=int(time.time()) + 999999)
        assert len(flush_results) > 0, "Expected a feature vector to be successfully flushed"
    except TypeError as e:
        assert False, f"TypeError encountered during flush_expired: {e}"
        
    print("Regression test passed! flush_expired safely calculates arithmetic limits.")

if __name__ == "__main__":
    test_window_manager_flush_expired_types()
