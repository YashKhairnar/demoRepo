# app.py

import logging

# Configure basic logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def calculate_percentage(part, total):
    """
    Calculates the percentage of 'part' out of 'total'.
    Handles cases where 'total' is zero to prevent ZeroDivisionError.

    Args:
        part (float or int): The part of the total.
        total (float or int): The total amount.

    Returns:
        float: The calculated percentage, or 0.0 if total is zero.
    """
    if total == 0:
        # Log a warning instead of crashing.
        # Returning 0.0 is a common and sensible default for percentages
        # when the total is zero, implying no activity or an undefined rate
        # that should not crash the application.
        logging.warning(f"Attempted to calculate percentage with total=0. Returning 0%. Part: {part}")
        return 0.0
    
    # This was the line (or part of the line) causing the ZeroDivisionError
    # if 'total' was 0 before the fix.
    percentage = (part / total) * 100
    return percentage

def process_data():
    """
    Simulates processing data that might lead to a division by zero.
    """
    # Scenario 1: Problematic data (total_attempts is 0)
    successful_attempts_problematic = 50
    total_attempts_problematic = 0 

    logging.info(f"Processing data: {successful_attempts_problematic} successful out of {total_attempts_problematic} total.")
    try:
        completion_rate_problematic = calculate_percentage(successful_attempts_problematic, total_attempts_problematic)
        logging.info(f"Completion rate (problematic): {completion_rate_problematic:.2f}%")
    except Exception as e:
        # This block should now ideally not be hit for ZeroDivisionError
        logging.error(f"An unexpected error occurred during problematic data processing: {e}")

    # Scenario 2: Valid data
    successful_attempts_valid = 75
    total_attempts_valid = 100
    
    logging.info(f"\nProcessing valid data: {successful_attempts_valid} successful out of {total_attempts_valid} total.")
    try:
        completion_rate_valid = calculate_percentage(successful_attempts_valid, total_attempts_valid)
        logging.info(f"Completion rate (valid): {completion_rate_valid:.2f}%")
    except Exception as e:
        logging.error(f"An unexpected error occurred during valid data processing: {e}")

if __name__ == "__main__":
    process_data()