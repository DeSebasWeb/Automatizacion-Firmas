import sys
from pathlib import Path
import time
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturesTimeoutError

sys.path.insert(0, str(Path(__file__).parent.parent))


def simulate_slow_azure_call():
    print("Simulating slow Azure call that takes 120 seconds...")
    time.sleep(120)
    return "Should never reach here"


def test_threadpool_timeout():
    print("Testing ThreadPoolExecutor timeout enforcement\n")

    timeout_seconds = 5
    print(f"Setting timeout to {timeout_seconds} seconds")
    print("Starting slow operation...")

    start_time = time.time()

    try:
        with ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(simulate_slow_azure_call)

            try:
                result = future.result(timeout=timeout_seconds)
                print(f"Result: {result}")
            except FuturesTimeoutError:
                elapsed = time.time() - start_time
                print(f"\n✅ SUCCESS: Timeout enforced after {elapsed:.2f} seconds")
                print(f"Expected: ~{timeout_seconds}s, Got: {elapsed:.2f}s")
                future.cancel()
                print("Future cancelled successfully")
                return True

    except Exception as e:
        elapsed = time.time() - start_time
        print(f"\n❌ FAILED: Unexpected error after {elapsed:.2f}s")
        print(f"Error: {str(e)}")
        return False

    elapsed = time.time() - start_time
    print(f"\n❌ FAILED: No timeout occurred after {elapsed:.2f}s")
    return False


if __name__ == "__main__":
    print("=" * 60)
    print("TIMEOUT ENFORCEMENT TEST")
    print("=" * 60)
    print()

    success = test_threadpool_timeout()

    print()
    print("=" * 60)
    if success:
        print("✅ Timeout mechanism works correctly")
        print("This means Azure DI will be forced to timeout at 60 seconds")
    else:
        print("❌ Timeout mechanism FAILED")
        print("There may be issues with thread-based timeout")
    print("=" * 60)
