"""
This moduel has send_data functions to be used by other modules.
"""

import logging
import requests

def send_data(data, doku_url, doku_token):
    """
    Send data to the specified Doku URL.

    Args:
        data (dict): Data to be sent.
        api_url (str): URL of the API endpoint.
        auth_token (str): Authentication api_key.

    Raises:
        requests.exceptions.RequestException: If an error occurs during the request.
    """

    try:
        headers = {
            'Authorization': doku_token,
            'Content-Type': 'application/json',
        }

        response = requests.post(doku_url.rstrip("/") + "/api/push",
                                 json=data,
                                 headers=headers,
                                 timeout=30)
        response.raise_for_status()
    except requests.exceptions.RequestException as req_err:
        logging.error("Error sending data to Doku: %s", req_err)
        raise  # Re-raise the exception after logging
