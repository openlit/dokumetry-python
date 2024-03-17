"""
__init__ module for dokumetry package.
"""
from anthropic import AsyncAnthropic, Anthropic
from openai import AsyncOpenAI, OpenAI, AzureOpenAI, AsyncAzureOpenAI
from mistralai.async_client import MistralAsyncClient
from mistralai.client import MistralClient

from .openai import init as init_openai
from .async_openai import init as init_async_openai
from .azure_openai import init as init_azure_openai
from .async_azure_openai import init as init_async_azure_openai
from .anthropic import init as init_anthropic
from .async_anthropic import init as init_async_anthropic
from .cohere import init as init_cohere
from .mistral import init as init_mistral
from .async_mistral import init as init_async_mistral

# pylint: disable=too-few-public-methods
class DokuConfig:
    """
    Configuration class for Doku initialization.
    """

    llm = None
    doku_url = None
    api_key = None
    environment = None
    application_name = None
    skip_resp = None

# pylint: disable=too-many-arguments, line-too-long, too-many-return-statements
def init(llm, doku_url, api_key, environment="default", application_name="default", skip_resp=False):
    """
    Initialize Doku configuration based on the provided function.

    Args:
        llm: The function to determine the platform (OpenAI, Cohere, Anthropic).
        doku_url (str): Doku URL.
        api_key (str): Doku Authentication api_key.
        environment (str): Doku environment.
        application_name (str): Doku application name.
        skip_resp (bool): Skip response processing.
    """

    DokuConfig.llm = llm
    DokuConfig.doku_url = doku_url
    DokuConfig.api_key = api_key
    DokuConfig.environment = environment
    DokuConfig.application_name = application_name
    DokuConfig.skip_resp = skip_resp

    # pylint: disable=no-else-return, line-too-long
    if hasattr(llm, 'moderations') and callable(llm.chat.completions.create) and ('.openai.azure.com/' not in str(llm.base_url)):
        if isinstance(llm, OpenAI):
            init_openai(llm, doku_url, api_key, environment, application_name, skip_resp)
        elif isinstance(llm, AsyncOpenAI):
            init_async_openai(llm, doku_url, api_key, environment, application_name, skip_resp)
        return
    # pylint: disable=no-else-return, line-too-long
    if hasattr(llm, 'moderations') and callable(llm.chat.completions.create) and ('.openai.azure.com/' in str(llm.base_url)):
        if isinstance(llm, AzureOpenAI):
            init_azure_openai(llm, doku_url, api_key, environment, application_name, skip_resp)
        elif isinstance(llm, AsyncAzureOpenAI):
            init_async_azure_openai(llm, doku_url, api_key, environment, application_name, skip_resp)
        return
    if isinstance(llm, MistralClient):
        init_mistral(llm, doku_url, api_key, environment, application_name, skip_resp)
        return
    elif isinstance(llm, MistralAsyncClient):
        init_async_mistral(llm, doku_url, api_key, environment, application_name, skip_resp)
        return
    elif isinstance(llm, AsyncAnthropic):
        init_async_anthropic(llm, doku_url, api_key, environment, application_name, skip_resp)
        return
    elif isinstance(llm, Anthropic):
        init_anthropic(llm, doku_url, api_key, environment, application_name, skip_resp)
        return
    elif hasattr(llm, 'generate') and callable(llm.generate):
        init_cohere(llm, doku_url, api_key, environment, application_name, skip_resp)
        return
