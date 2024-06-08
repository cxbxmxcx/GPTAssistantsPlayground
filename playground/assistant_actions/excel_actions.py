import pandas as pd
import io
import os

from playground.actions_manager import agent_action
from playground.global_values import GlobalValues


@agent_action
def excel_to_csv(filename, skiprows):
    """
    Reads an Excel file, skips the specified number of rows, and returns the content as a CSV-formatted text string.

    Parameters:
    filename (str): The path to the Excel file.
    skiprows (int or list of int): The number of rows to skip at the start or a list of row indices to skip.

    Returns:
    str: The CSV-formatted text string.
    """
    file_path = os.path.join(GlobalValues.ASSISTANTS_WORKING_FOLDER, filename)
    # Read the Excel file and skip the specified rows
    df = pd.read_excel(file_path, skiprows=skiprows)

    # Create a buffer to store the CSV content
    buffer = io.StringIO()

    # Write the DataFrame to the buffer as CSV
    df.to_csv(buffer, index=False)

    # Get the CSV content from the buffer
    csv_content = buffer.getvalue()

    # Close the buffer
    buffer.close()

    return csv_content


@agent_action
def csv_to_excel(csv_content, start_row, filename):
    """
    Reads a CSV-formatted text string, skips the specified number of rows, and saves the content as an Excel file.

    Parameters:
    csv_content (str): The CSV-formatted text string.
    start_row (int): The row number to start to add content to.
    filename (str): The path to the output Excel file.

    Returns:
    None
    """
    # Create a buffer from the CSV content
    buffer = io.StringIO(csv_content)

    # Read the CSV content into a DataFrame, skipping the specified rows
    df = pd.read_csv(buffer)

    # Save the DataFrame to an Excel file
    file_path = os.path.join(GlobalValues.ASSISTANTS_WORKING_FOLDER, filename)
    df.to_excel(file_path, index=False, startrow=start_row)

    # Close the buffer
    buffer.close()
