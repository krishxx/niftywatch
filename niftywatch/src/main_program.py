import subprocess
import time
import datetime

# --- Configuration ---
program_to_run = "get_idx.py"
# On Windows, you might need to specify the python executable explicitly:
# program_to_run = ["python", "sub_program.py"]

start_time_str = "09:15"  # H:MM
end_time_str = "15:30"    # H:MM
frequency_seconds = 30   # How often to run the sub-program in seconds

print(f"Scheduler started for '{program_to_run}'.")
print(f"Will run every {frequency_seconds} seconds between {start_time_str} and {end_time_str}.")

def run_sub_program():
    """Function to execute the sub-program and handle its output/errors."""
    print(f"\n--- Running '{program_to_run}' at {datetime.datetime.now().strftime('%H:%M:%S')} ---")
    try:
        result = subprocess.run(
            ["python", program_to_run], # Use ["python", program_to_run] to explicitly call python
            capture_output=True,
            text=True,
            check=True
        )
        print("Sub-program output:")
        print(result.stdout)
        if result.stderr:
            print("Sub-program errors (stderr):")
            print(result.stderr)

    except subprocess.CalledProcessError as e:
        print(f"Error running sub-program: {e}")
        print(f"Sub-program exited with code {e.returncode}")
        print(f"Stdout: {e.stdout}")
        print(f"Stderr: {e.stderr}")
    except FileNotFoundError:
        print(f"Error: '{program_to_run}' not found. Make sure the path is correct.")
        return False # Indicate a critical error, stop execution
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
    return True # Indicate successful (or handled) execution

def get_next_run_time(current_dt, start_dt, end_dt, interval_seconds):
    """Calculates the next scheduled run time."""
    # Normalize current_dt to today's date with start_time
    start_of_day_run_window = current_dt.replace(hour=start_dt.hour, minute=start_dt.minute, second=0, microsecond=0)

    # If current time is before start_of_day_run_window, the next run is at start_of_day_run_window
    if current_dt < start_of_day_run_window:
        return start_of_day_run_window

    # Calculate seconds past start_of_day_run_window
    seconds_past_start = (current_dt - start_of_day_run_window).total_seconds()
    
    # Calculate how many intervals have passed
    intervals_passed = int(seconds_past_start / interval_seconds)
    
    # Calculate the potential next run time
    next_run = start_of_day_run_window + datetime.timedelta(seconds=(intervals_passed + 1) * interval_seconds)

    # If current time is exactly on an interval, the current one is valid.
    # We add a small buffer (e.g., 0.1 seconds) to avoid floating point issues
    # and ensure we don't re-run if it literally just ran.
    if abs(seconds_past_start % interval_seconds) < 0.1: # Check if close to an interval boundary
         if current_dt >= start_of_day_run_window: # Ensure we are within or after start
             return current_dt # Run now

    return next_run

def parse_time_string(time_str):
    """Parses a 'HH:MM' string into a time object."""
    h, m = map(int, time_str.split(':'))
    return datetime.time(h, m)

# Parse start and end times
start_time_obj = parse_time_string(start_time_str)
end_time_obj = parse_time_string(end_time_str)

while True:
    now = datetime.datetime.now()
    
    # Check if current time is within the operating window (using time part only)
    if start_time_obj <= now.time() <= end_time_obj:
        # Construct datetime objects for today's start and end times
        today_start_dt = now.replace(
            hour=start_time_obj.hour, 
            minute=start_time_obj.minute, 
            second=0, 
            microsecond=0
        )
        today_end_dt = now.replace(
            hour=end_time_obj.hour, 
            minute=end_time_obj.minute, 
            second=0, 
            microsecond=0
        )

        next_scheduled_run = get_next_run_time(now, today_start_dt, today_end_dt, frequency_seconds)

        # If the next scheduled run is in the past or now, it's time to execute
        if next_scheduled_run <= now: 
            if run_sub_program() == False: # If sub-program indicates a critical error
                break # Exit the main loop
            
            # After running, calculate the *next* ideal run time to ensure proper spacing
            # This accounts for the time the sub-program took to execute
            last_run_completion_time = datetime.datetime.now()
            next_scheduled_run = get_next_run_time(last_run_completion_time, today_start_dt, today_end_dt, frequency_seconds)
            
            # If the calculated next run is still before or at the last run completion time,
            # advance it by one interval to avoid immediate re-runs.
            if next_scheduled_run <= last_run_completion_time:
                next_scheduled_run += datetime.timedelta(seconds=frequency_seconds)

        # Ensure next_scheduled_run does not exceed end_time for today
        if next_scheduled_run > today_end_dt:
            print(f"End of operating window ({end_time_str}) reached or passed for today. Waiting until tomorrow {start_time_str}.")
            # Calculate time to wait until tomorrow's start time
            tomorrow_start_dt = (now + datetime.timedelta(days=1)).replace(
                hour=start_time_obj.hour, 
                minute=start_time_obj.minute, 
                second=0, 
                microsecond=0
            )
            wait_seconds = (tomorrow_start_dt - now).total_seconds()
            print(f"Sleeping for {int(wait_seconds / 3600)} hours, {int((wait_seconds % 3600) / 60)} minutes, and {int(wait_seconds % 60)} seconds.")
            time.sleep(wait_seconds)
            continue # Go to next iteration of while loop to re-evaluate time

        wait_seconds = (next_scheduled_run - now).total_seconds()
        if wait_seconds > 0:
            print(f"Next run scheduled for {next_scheduled_run.strftime('%H:%M:%S')}. Sleeping for {int(wait_seconds)} seconds.")
            time.sleep(wait_seconds)
        else:
            # If wait_seconds is 0 or negative (means we just missed the time or it's now),
            # sleep for a very short period to prevent busy-waiting.
            # This helps avoid CPU spikes if the schedule is very tight.
            time.sleep(0.1) 
            
    else:
        print(f"Outside operating window ({start_time_str}-{end_time_str}). Current time: {now.strftime('%H:%M:%S')}.")
        # Calculate time until start of next window (today or tomorrow)
        if now.time() < start_time_obj:
            # Still before today's start time
            next_window_start = now.replace(
                hour=start_time_obj.hour, 
                minute=start_time_obj.minute, 
                second=0, 
                microsecond=0
            )
        else:
            # After today's end time, wait for tomorrow's start time
            next_window_start = (now + datetime.timedelta(days=1)).replace(
                hour=start_time_obj.hour, 
                minute=start_time_obj.minute, 
                second=0, 
                microsecond=0
            )
        
        wait_seconds = (next_window_start - now).total_seconds()
        print(f"Waiting for {int(wait_seconds / 3600)} hours, {int((wait_seconds % 3600) / 60)} minutes, and {int(wait_seconds % 60)} seconds until {next_window_start.strftime('%H:%M:%S')}.")
        time.sleep(wait_seconds)

print("\nScheduler terminated.")