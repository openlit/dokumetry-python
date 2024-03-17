# pylint: disable=duplicate-code
"""
Module for monitoring Mistral API calls.
"""

import time
from .__helpers import send_data

# pylint: disable=too-many-arguments, too-many-statements
def init(llm, doku_url, api_key, environment, application_name, skip_resp):
    """
    Initialize Mistral integration with Doku.

    Args:
        llm: The Mistral function to be patched.
        doku_url (str): Doku URL.
        api_key (str): Authentication api_key.
        environment (str): Doku environment.
        application_name (str): Doku application name.
        skip_resp (bool): Skip response processing.
    """

    original_mistral_chat = llm.chat
    original_mistral_chat_stream = llm.chat_stream
    original_mistral_embeddings = llm.embeddings

    #pylint: disable=too-many-locals
    def patched_chat(*args, **kwargs):
        """
        Patched version of Mistral's chat method.

        Args:
            *args: Variable positional arguments.
            **kwargs: Variable keyword arguments.

        Returns:
            MistalResponse: The response from Mistral's chat.
        """
        start_time = time.time()
        response = original_mistral_chat(*args, **kwargs)
        end_time = time.time()
        duration = end_time - start_time
        message_prompt = kwargs.get('messages', "No prompt provided")
        formatted_messages = []

        for message in message_prompt:
            role = message.role
            content = message.content

            if isinstance(content, list):
                content_str = ", ".join(
                    f"{item['type']}: {item['text'] if 'text' in item else item['image_url']}"
                    if 'type' in item else f"text: {item['text']}"
                    for item in content
                )
                formatted_messages.append(f"{role}: {content_str}")
            else:
                formatted_messages.append(f"{role}: {content}")

        prompt = " ".join(formatted_messages)
        model = kwargs.get('model')

        prompt_tokens = response.usage.prompt_tokens
        completion_tokens = response.usage.completion_tokens
        total_tokens = response.usage.total_tokens

        data = {
                "llmReqId": response.id,
                "environment": environment,
                "applicationName": application_name,
                "sourceLanguage": "python",
                "endpoint": "mistral.chat",
                "skipResp": skip_resp,
                "completionTokens": completion_tokens,
                "promptTokens": prompt_tokens,
                "totalTokens": total_tokens,
                "requestDuration": duration,
                "model": model,
                "prompt": prompt,
                "finishReason": response.choices[0].finish_reason,
                "response": response.choices[0].message.content
        }

        send_data(data, doku_url, api_key)

        return response

    #pylint: disable=too-many-locals
    def patched_chat_stream(*args, **kwargs):
        """
        Patched version of Mistral's chat_stream method.

        Args:
            *args: Variable positional arguments.
            **kwargs: Variable keyword arguments.

        Returns:
            MistalResponse: The response from Mistral's chat_stream.
        """
        start_time = time.time()
        def stream_generator():
            accumulated_content = ""
            for event in original_mistral_chat_stream(*args, **kwargs):
                response_id = event.id
                accumulated_content += event.choices[0].delta.content
                if event.usage is not None:
                    prompt_tokens = event.usage.prompt_tokens
                    completion_tokens = event.usage.completion_tokens
                    total_tokens = event.usage.total_tokens
                    finish_reason = event.choices[0].finish_reason
                yield event
            end_time = time.time()
            duration = end_time - start_time
            message_prompt = kwargs.get('messages', "No prompt provided")
            formatted_messages = []

            for message in message_prompt:
                role = message.role
                content = message.content

                if isinstance(content, list):
                    content_str = ", ".join(
                        f"{item['type']}: {item['text'] if 'text' in item else item['image_url']}"
                        if 'type' in item else f"text: {item['text']}"
                        for item in content
                    )
                    formatted_messages.append(f"{role}: {content_str}")
                else:
                    formatted_messages.append(f"{role}: {content}")

            prompt = " ".join(formatted_messages)

            data = {
                "llmReqId": response_id,
                "environment": environment,
                "applicationName": application_name,
                "sourceLanguage": "python",
                "endpoint": "mistral.chat",
                "skipResp": skip_resp,
                "requestDuration": duration,
                "model": kwargs.get('model', "command"),
                "prompt": prompt,
                "response": accumulated_content,
                "promptTokens": prompt_tokens,
                "completionTokens": completion_tokens,
                "totalTokens": total_tokens,
                "finishReason": finish_reason
            }

            send_data(data, doku_url, api_key)

        return stream_generator()

    def patched_embeddings(*args, **kwargs):
        """
        Patched version of Cohere's embeddings generate method.

        Args:
            *args: Variable positional arguments.
            **kwargs: Variable keyword arguments.

        Returns:
            CohereResponse: The response from Cohere's embeddings generate method.
        """

        start_time = time.time()
        response = original_mistral_embeddings(*args, **kwargs)
        end_time = time.time()
        duration = end_time - start_time
        model = kwargs.get('model', "mistral-embed")
        prompt = ', '.join(kwargs.get('input', []))

        data = {
            "llmReqId": response.id,
            "environment": environment,
            "applicationName": application_name,
            "sourceLanguage": "python",
            "endpoint": "mistral.embeddings",
            "skipResp": skip_resp,
            "requestDuration": duration,
            "model": model,
            "prompt": prompt,
            "promptTokens": response.usage.prompt_tokens,
            "completionTokens": response.usage.completion_tokens,
            "totalTokens": response.usage.total_tokens,
        }

        send_data(data, doku_url, api_key)

        return response

    llm.chat = patched_chat
    llm.chat_stream = patched_chat_stream
    llm.embeddings = patched_embeddings
