# spinner
import sys
import time
import threading

def spinning_cursor():
    while True:
        for cursor in "|/-\\":
            yield cursor


def spinner_function():
    spinner = spinning_cursor()
    while True:
        sys.stdout.write(next(spinner))
        sys.stdout.flush()
        time.sleep(0.1)
        sys.stdout.write("\b")
        
        
        
        
if __name__ == "__main__":
    # Start the spinner in a separate thread
    spinner_thread = threading.Thread(target=spinner_function)
    spinner_thread.daemon = (
        True  # Daemon threads will be automatically killed once the main program exits.
    )
    spinner_thread.start()