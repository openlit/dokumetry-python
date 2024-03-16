# pylint: disable=duplicate-code
"""
Module for monitoring OpenAI API calls.
"""

import time
from .__helpers import send_data

# pylint: disable=too-many-locals
# pylint: disable=too-many-arguments
# pylint: disable=too-many-statements
def init(llm, doku_url, api_key, environment, application_name, skip_resp):
    """
    Initialize OpenAI monitoring for Doku.

    Args:
        llm: The OpenAI function to be patched.
        doku_url (str): Doku URL.
        api_key (str): Doku Authentication api_key.
        environment (str): Doku environment.
        application_name (str): Doku application name.
        skip_resp (bool): Skip response processing.
    """

    original_chat_create = llm.chat.completions.create
    original_completions_create = llm.completions.create
    original_embeddings_create = llm.embeddings.create
    original_images_create = llm.images.generate

    async def llm_chat_completions(*args, **kwargs):
        """
        Patched version of OpenAI's chat completions create method.

        Args:
            *args: Variable positional arguments.
            **kwargs: Variable keyword arguments.

        Returns:
            OpenAIResponse: The response from OpenAI's chat completions create method.
        """
        is_streaming = kwargs.get('stream', False)
        start_time = time.time()
        #pylint: disable=no-else-return
        if is_streaming:
            async def stream_generator():
                accumulated_content = ""
                async for chunk in await original_chat_create(*args, **kwargs):
                    #pylint: disable=line-too-long
                    if len(chunk.choices) > 0:
                        if hasattr(chunk.choices[0], 'delta') and hasattr(chunk.choices[0].delta, 'content'):
                            content = chunk.choices[0].delta.content
                            if content:
                                accumulated_content += content
                    yield chunk
                    response_id = chunk.id
                    model = chunk.model
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
                    "environment": environment,
                    "llmReqId": response_id,
                    "applicationName": application_name,
                    "sourceLanguage": "python",
                    "endpoint": "azure.chat.completions",
                    "skipResp": skip_resp,
                    "requestDuration": duration,
                    "model": "azure_" + model,
                    "prompt": prompt,
                    "response": accumulated_content,
                }

                send_data(data, doku_url, api_key)

            return stream_generator()
        else:
            start_time = time.time()
            response = await original_chat_create(*args, **kwargs)
            end_time = time.time()
            duration = end_time - start_time
            model = "azure_" + response.model
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

            data = {
                "llmReqId": response.id,
                "endpoint": "azure.chat.completions",
                "environment": environment,
                "applicationName": application_name,
                "sourceLanguage": "python",
                "skipResp": skip_resp,
                "requestDuration": duration,
                "model": model,
                "prompt": prompt,
            }

            if "tools" not in kwargs:
                data["completionTokens"] = response.usage.completion_tokens
                data["promptTokens"] = response.usage.prompt_tokens
                data["totalTokens"] = response.usage.total_tokens
                data["finishReason"] = response.choices[0].finish_reason

                if "n" not in kwargs or kwargs["n"] == 1:
                    data["response"] = response.choices[0].message.content
                else:
                    i = 0
                    while i < kwargs["n"]:
                        data["response"] = response.choices[i].message.content
                        i += 1
                        send_data(data, doku_url, api_key)
                    return response
            elif "tools" in kwargs:
                data["response"] = "Function called with tools"
                data["completionTokens"] = response.usage.completion_tokens
                data["promptTokens"] = response.usage.prompt_tokens
                data["totalTokens"] = response.usage.total_tokens

            send_data(data, doku_url, api_key)

            return response

    async def llm_completions(*args, **kwargs):
        """
        Patched version of OpenAI's completions create method.

        Args:
            *args: Variable positional arguments.
            **kwargs: Variable keyword arguments.

        Returns:
            OpenAIResponse: The response from OpenAI's completions create method.
        """
        start_time = time.time()
        streaming = kwargs.get('stream', False)
        #pylint: disable=no-else-return
        if streaming:
            async def stream_generator():
                accumulated_content = ""
                async for chunk in await original_completions_create(*args, **kwargs):
                    if len(chunk.choices) > 0:
                        if hasattr(chunk.choices[0], 'text'):
                            content = chunk.choices[0].text
                            if content:
                                accumulated_content += content
                    yield chunk
                    response_id = chunk.id
                    model = chunk.model
                end_time = time.time()
                duration = end_time - start_time
                prompt = kwargs.get('prompt', "No prompt provided")
                data = {
                    "endpoint": "azure.completions",
                    "llmReqId": response_id,
                    "environment": environment,
                    "applicationName": application_name,
                    "sourceLanguage": "python",
                    "skipResp": skip_resp,
                    "requestDuration": duration,
                    "model": "azure_" + model,
                    "prompt": prompt,
                    "response": accumulated_content,
                }

                send_data(data, doku_url, api_key)

            return stream_generator()
        else:
            start_time = time.time()
            response = await original_completions_create(*args, **kwargs)
            end_time = time.time()
            duration = end_time - start_time
            model = "azure_" + response.model
            prompt = kwargs.get('prompt', "No prompt provided")

            data = {
                "environment": environment,
                "applicationName": application_name,
                "llmReqId": response.id,
                "sourceLanguage": "python",
                "endpoint": "azure.completions",
                "skipResp": skip_resp,
                "requestDuration": duration,
                "model": model,
                "prompt": prompt,
            }

            if "tools" not in kwargs:
                data["completionTokens"] = response.usage.completion_tokens
                data["promptTokens"] = response.usage.prompt_tokens
                data["totalTokens"] = response.usage.total_tokens
                data["finishReason"] = response.choices[0].finish_reason

                if "n" not in kwargs or kwargs["n"] == 1:
                    data["response"] = response.choices[0].text
                else:
                    i = 0
                    while i < kwargs["n"]:
                        data["response"] = response.choices[i].text
                        i += 1
                        send_data(data, doku_url, api_key)
                    return response
            elif "tools" in kwargs:
                data["response"] = "Function called with tools"
                data["completionTokens"] = response.usage.completion_tokens
                data["promptTokens"] = response.usage.prompt_tokens
                data["totalTokens"] = response.usage.total_tokens

            send_data(data, doku_url, api_key)

            return response

    async def patched_embeddings_create(*args, **kwargs):
        """
        Patched version of OpenAI's embeddings create method.

        Args:
            *args: Variable positional arguments.
            **kwargs: Variable keyword arguments.

        Returns:
            OpenAIResponse: The response from OpenAI's embeddings create method.
        """

        start_time = time.time()
        response = await original_embeddings_create(*args, **kwargs)
        end_time = time.time()
        duration = end_time - start_time
        model = "azure_" + response.model
        prompt = ', '.join(kwargs.get('input', []))

        data = {
            "environment": environment,
            "applicationName": application_name,
            "sourceLanguage": "python",
            "endpoint": "azure.embeddings",
            "skipResp": skip_resp,
            "requestDuration": duration,
            "model": model,
            "prompt": prompt,
            "promptTokens": response.usage.prompt_tokens,
            "totalTokens": response.usage.total_tokens
        }

        send_data(data, doku_url, api_key)

        return response

    async def patched_image_create(*args, **kwargs):
        """
        Patched version of OpenAI's images generate method.

        Args:
            *args: Variable positional arguments.
            **kwargs: Variable keyword arguments.

        Returns:
            OpenAIResponse: The response from OpenAI's images generate method.
        """

        start_time = time.time()
        response = await original_images_create(*args, **kwargs)
        end_time = time.time()
        duration = end_time - start_time
        model = "azure_dall-e-3"
        prompt = kwargs.get('prompt', "No prompt provided")
        size = kwargs.get('size', '1024x1024')

        if 'response_format' in kwargs and kwargs['response_format'] == 'b64_json':
            image = "b64_json"
        else:
            image = "url"

        if 'quality' not in kwargs:
            quality = "standard"
        else:
            quality = kwargs['quality']

        for items in response.data:
            data = {
                "llmReqId": response.created,
                "environment": environment,
                "applicationName": application_name,
                "sourceLanguage": "python",
                "endpoint": "azure.images.create",
                "skipResp": skip_resp,
                "requestDuration": duration,
                "model": model,
                "prompt": prompt,
                "imageSize": size,
                "imageQuality": quality,
                "revisedPrompt": items.revised_prompt,
                "image": getattr(items, image)
            }

            send_data(data, doku_url, api_key)

        return response

    llm.chat.completions.create = llm_chat_completions
    llm.completions.create = llm_completions
    llm.embeddings.create = patched_embeddings_create
    llm.images.generate = patched_image_create
