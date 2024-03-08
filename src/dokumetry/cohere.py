# pylint: disable=duplicate-code
"""
Module for monitoring Cohere API calls.
"""

import time
from .__helpers import send_data

def count_tokens(text):
    """
    Count the number of tokens in the given text.

    Args:
        text (str): The input text.

    Returns:
        int: The number of tokens in the text.
    """
    tokens_per_word = 1.5

    # Split the text into words
    words = text.split()

    # Calculate the number of tokens
    num_tokens = round(len(words) * tokens_per_word)

    return num_tokens

# pylint: disable=too-many-arguments, too-many-statements
def init(llm, doku_url, api_key, environment, application_name, skip_resp):
    """
    Initialize Cohere monitoring for Doku.

    Args:
        llm: The Cohere function to be patched.
        doku_url (str): Doku URL.
        api_key (str): Doku Authentication api_key.
        environment (str): Doku environment.
        application_name (str): Doku application name.
        skip_resp (bool): Skip response processing.
    """

    original_generate = llm.generate
    original_embed = llm.embed
    original_chat = llm.chat
    original_summarize = llm.summarize

    def patched_generate(*args, **kwargs):
        """
        Patched version of Cohere's generate method.

        Args:
            *args: Variable positional arguments.
            **kwargs: Variable keyword arguments.

        Returns:
            CohereResponse: The response from Cohere's generate method.
        """
        streaming = kwargs.get('stream', False)
        start_time = time.time()
        #pylint: disable=no-else-return
        if streaming:
            def stream_generator():
                accumulated_content = ""
                for event in original_generate(*args, **kwargs):
                    accumulated_content += event.text
                    yield event
                end_time = time.time()
                duration = end_time - start_time
                prompt = kwargs.get('prompt')
                data = {
                    "environment": environment,
                    "applicationName": application_name,
                    "sourceLanguage": "python",
                    "endpoint": "cohere.generate",
                    "skipResp": skip_resp,
                    "requestDuration": duration,
                    "model": kwargs.get('model', "command"),
                    "prompt": prompt,
                    "response": accumulated_content,
                    "promptTokens": count_tokens(prompt),
                    "completionTokens": count_tokens(accumulated_content),
                }
                data["totalTokens"] = data["completionTokens"] + data["promptTokens"]

                send_data(data, doku_url, api_key)

            return stream_generator()
        else:
            start_time = time.time()
            response = original_generate(*args, **kwargs)
            end_time = time.time()
            duration = end_time - start_time
            model = kwargs.get('model', 'command')
            prompt = kwargs.get('prompt')

            for generation in response:
                data = {
                    "llmReqId": generation.id,
                    "environment": environment,
                    "applicationName": application_name,
                    "sourceLanguage": "python",
                    "endpoint": "cohere.generate",
                    "skipResp": skip_resp,
                    "finishReason": generation.finish_reason,
                    "completionTokens": count_tokens(generation.text),
                    "promptTokens": count_tokens(prompt),
                    "requestDuration": duration,
                    "model": model,
                    "prompt": prompt,
                    "response": generation.text,
                }
                data["totalTokens"] = data["completionTokens"] + data["promptTokens"]

                send_data(data, doku_url, api_key)

            return response

    def embeddings_generate(*args, **kwargs):
        """
        Patched version of Cohere's embeddings generate method.

        Args:
            *args: Variable positional arguments.
            **kwargs: Variable keyword arguments.

        Returns:
            CohereResponse: The response from Cohere's embeddings generate method.
        """

        start_time = time.time()
        response = original_embed(*args, **kwargs)
        end_time = time.time()
        duration = end_time - start_time
        model = kwargs.get('model', "embed-english-v2.0")
        prompt = ' '.join(kwargs.get('texts', []))

        data = {
            "environment": environment,
            "applicationName": application_name,
            "sourceLanguage": "python",
            "endpoint": "cohere.embed",
            "skipResp": skip_resp,
            "requestDuration": duration,
            "model": model,
            "prompt": prompt,
            "promptTokens": response.meta["billed_units"]["input_tokens"],
        }

        send_data(data, doku_url, api_key)

        return response

    def chat_generate(*args, **kwargs):
        """
        Patched version of Cohere's chat generate method.

        Args:
            *args: Variable positional arguments.
            **kwargs: Variable keyword arguments.

        Returns:
            CohereResponse: The response from Cohere's chat generate method.
        """
        streaming = kwargs.get('stream', False)
        start_time = time.time()
        #pylint: disable=no-else-return
        if streaming:
            def stream_generator():
                accumulated_content = ""
                for event in original_chat(*args, **kwargs):
                    if event.event_type == "stream-start":
                        response_id = event.generation_id
                    if event.event_type == "text-generation":
                        accumulated_content += event.text
                    yield event
                end_time = time.time()
                duration = end_time - start_time
                prompt = kwargs.get('message')
                data = {
                    "llmReqId": response_id,
                    "environment": environment,
                    "applicationName": application_name,
                    "sourceLanguage": "python",
                    "endpoint": "cohere.chat",
                    "skipResp": skip_resp,
                    "requestDuration": duration,
                    "model": kwargs.get('model', "command"),
                    "prompt": prompt,
                    "response": accumulated_content,
                    "promptTokens": count_tokens(prompt),
                    "completionTokens": count_tokens(accumulated_content),
                }
                data["totalTokens"] = data["completionTokens"] + data["promptTokens"]

                send_data(data, doku_url, api_key)

            return stream_generator()
        else:
            start_time = time.time()
            response = original_chat(*args, **kwargs)
            end_time = time.time()
            duration = end_time - start_time
            model = kwargs.get('model', "command")
            prompt = kwargs.get('message')
            data = {
                "llmReqId": response.response_id,
                "environment": environment,
                "applicationName": application_name,
                "sourceLanguage": "python",
                "endpoint": "cohere.chat",
                "skipResp": skip_resp,
                "requestDuration": duration,
                "prompt": prompt,
                "model": model,
                "completionTokens": response.meta["billed_units"]["output_tokens"],
                "promptTokens": response.meta["billed_units"]["input_tokens"],
                "totalTokens": response.token_count["billed_tokens"],
                "response": response.text
            }

            send_data(data, doku_url, api_key)

            return response

    def summarize_generate(*args, **kwargs):
        """
        Patched version of Cohere's summarize generate method.

        Args:
            *args: Variable positional arguments.
            **kwargs: Variable keyword arguments.

        Returns:
            CohereResponse: The response from Cohere's summarize generate method.
        """

        start_time = time.time()
        response = original_summarize(*args, **kwargs)
        end_time = time.time()
        duration = end_time - start_time
        model = kwargs.get('model', 'command')
        prompt = kwargs.get('text')

        data = {
                "applicationName": application_name,
                "llmReqId": response.id,
                "environment": environment,
                "sourceLanguage": "python",
                "endpoint": "cohere.summarize",
                "skipResp": skip_resp,
                "requestDuration": duration,
                "completionTokens": response.meta["billed_units"]["output_tokens"],
                "promptTokens": response.meta["billed_units"]["input_tokens"],
                "model": model,
                "prompt": prompt,
                "response": response.summary
        }
        data["totalTokens"] = data["completionTokens"] + data["promptTokens"]

        send_data(data, doku_url, api_key)

        return response

    llm.generate = patched_generate
    llm.embed = embeddings_generate
    llm.chat = chat_generate
    llm.summarize = summarize_generate
