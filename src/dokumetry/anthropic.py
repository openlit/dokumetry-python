# pylint: disable=duplicate-code
"""
Module for monitoring Anthropic API calls.
"""

import time
from .__helpers import send_data

# pylint: disable=too-many-arguments, too-many-statements
def init(llm, doku_url, api_key, environment, application_name, skip_resp):
    """
    Initialize Anthropic integration with Doku.

    Args:
        llm: The Anthropic function to be patched.
        doku_url (str): Doku URL.
        api_key (str): Authentication api_key.
        environment (str): Doku environment.
        application_name (str): Doku application name.
        skip_resp (bool): Skip response processing.
    """

    original_messages_create = llm.messages.create

    #pylint: disable=too-many-locals
    def patched_messages_create(*args, **kwargs):
        """
        Patched version of Anthropic's messages.create method.

        Args:
            *args: Variable positional arguments.
            **kwargs: Variable keyword arguments.

        Returns:
            AnthropicResponse: The response from Anthropic's completions.create.
        """
        streaming = kwargs.get('stream', False)
        start_time = time.time()

        # pylint: disable=no-else-return
        if streaming:
            def stream_generator():
                accumulated_content = ""
                for event in original_messages_create(*args, **kwargs):
                    if event.type == "message_start":
                        response_id = event.message.id
                        prompt_tokens = event.message.usage.input_tokens
                    if event.type == "content_block_delta":
                        accumulated_content += event.delta.text
                    if event.type == "message_delta":
                        completion_tokens = event.usage.output_tokens
                    yield event
                end_time = time.time()
                duration = end_time - start_time
                message_prompt = kwargs.get('messages', "No prompt provided")
                formatted_messages = []
                for message in message_prompt:
                    role = message["role"]
                    content = message["content"]

                    if isinstance(content, list):
                        content_str = ", ".join(
                            #pylint: disable=line-too-long
                            f"{item['type']}: {item['text'] if 'text' in item else item['image_url']}"
                            if 'type' in item else f"text: {item['text']}"
                            for item in content
                        )
                        formatted_messages.append(f"{role}: {content_str}")
                    else:
                        formatted_messages.append(f"{role}: {content}")

                prompt = "\n".join(formatted_messages)
                data = {
                    "llmReqId": response_id,
                    "environment": environment,
                    "applicationName": application_name,
                    "sourceLanguage": "python",
                    "endpoint": "anthropic.messages",
                    "skipResp": skip_resp,
                    "requestDuration": duration,
                    "model": kwargs.get('model', "command"),
                    "prompt": prompt,
                    "response": accumulated_content,
                    "promptTokens": prompt_tokens,
                    "completionTokens": completion_tokens,
                }
                data["totalTokens"] = data["completionTokens"] + data["promptTokens"]

                send_data(data, doku_url, api_key)

            return stream_generator()
        else:
            start_time = time.time()
            response = original_messages_create(*args, **kwargs)
            end_time = time.time()
            duration = end_time - start_time
            message_prompt = kwargs.get('messages', "No prompt provided")
            formatted_messages = []

            for message in message_prompt:
                role = message["role"]
                content = message["content"]

                if isinstance(content, list):
                    content_str = ", ".join(
                        f"{item['type']}: {item['text'] if 'text' in item else item['image_url']}"
                        if 'type' in item else f"text: {item['text']}"
                        for item in content
                    )
                    formatted_messages.append(f"{role}: {content_str}")
                else:
                    formatted_messages.append(f"{role}: {content}")

            prompt = "\n".join(formatted_messages)

            model = kwargs.get('model')

            prompt_tokens = response.usage.input_tokens
            completion_tokens = response.usage.output_tokens

            data = {
                    "llmReqId": response.id,
                    "environment": environment,
                    "applicationName": application_name,
                    "sourceLanguage": "python",
                    "endpoint": "anthropic.messages",
                    "skipResp": skip_resp,
                    "completionTokens": completion_tokens,
                    "promptTokens": prompt_tokens,
                    "requestDuration": duration,
                    "model": model,
                    "prompt": prompt,
                    "finishReason": response.stop_reason,
                    "response": response.content[0].text
            }
            data["totalTokens"] = data["completionTokens"] + data["promptTokens"]

            send_data(data, doku_url, api_key)

            return response

    llm.messages.create = patched_messages_create
