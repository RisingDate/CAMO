import json
import os
import re

import demjson3
from langchain_core.output_parsers import StrOutputParser, JsonOutputParser
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder, PromptTemplate
from langchain_ollama.llms import OllamaLLM
from langchain_openai import ChatOpenAI
from volcenginesdkarkruntime import Ark

from method.tools.printWithColor import Print

from method.config.Setting import (
    LANGCHAIN_TRACING_V2, LANGCHAIN_ENDPOINT, LANGCHAIN_API_KEY, LANGCHAIN_PROJECT,
    OPENAI_API_KEY, OPENAI_BASE_URL,
    ARK_API_KEY, ARK_BASE_URL,
    LOCAL_MODEL_A_API_KEY, LOCAL_MODEL_A_BASE_URL,
    LOCAL_MODEL_B_API_KEY, LOCAL_MODEL_B_BASE_URL,
    MODEL_LIST, ARK_MODEL_LIST, LLM_MODEL_NAME, MODEL_IN_THINK
)
os.environ['LANGCHAIN_TRACING_V2'] = LANGCHAIN_TRACING_V2
os.environ['LANGCHAIN_ENDPOINT'] = LANGCHAIN_ENDPOINT
os.environ['LANGCHAIN_API_KEY'] = LANGCHAIN_API_KEY
os.environ['LANGCHAIN_PROJECT'] = LANGCHAIN_PROJECT
os.environ["OPENAI_API_KEY"] = OPENAI_API_KEY
os.environ["OPENAI_BASE_URL"] = OPENAI_BASE_URL
MODEL_NAME = LLM_MODEL_NAME
class BaseLLMAgent:
    def __init__(self,
                 agent_name: str,
                 has_chat_history=False,
                 llm_model_name=MODEL_NAME,
                 json_format=True,
                 system_prompt='',
                 mcp_session=None):
        self.agent_name = agent_name or "Base Agent"
        self.has_chat_history = has_chat_history
        self.model_name = llm_model_name
        self.json_format = json_format
        self.system_prompt = system_prompt
        self.mcp_session = mcp_session

    async def get_response(self,
                           input_prompt=None,
                           input_param_dict=None,
                           is_first_call=True,
                           tools_used=None,
                           model_name=None):
        """
        实现大模型回答的函数
        Args:
            input_prompt(str): 用户输入的提示词
            input_param_dict(dict): input_prompt中的参数list
            is_first_call(boolean): 是否为Agent第一次调用此函数，用于控制对话记忆
            tools_used: 使用的mcp工具
            model_name(str): 使用的大模型名称
        Returns:
            result(str or json): 大模型的对问题的回答
        """
        # 删除掉所有制表符
        input_prompt = input_prompt.replace("\t", "")

        if model_name is None:
            model_name = self.model_name
        system_prompt = self.system_prompt
        if self.json_format:
            input_prompt += "\n Please give your response in JSON format.Return a JSON object. "
        else:
            input_prompt += "\n You just need to give me the result I want."

        # TODO 处理对话记忆
        if is_first_call:
            system_prompt = PromptTemplate.from_template(system_prompt).invoke(input_param_dict).to_string()
            input_prompt = PromptTemplate.from_template(input_prompt).invoke(input_param_dict).to_string()
            prompt_template = ChatPromptTemplate.from_messages([
                ('system', system_prompt),
                MessagesPlaceholder(variable_name="history"),
                ('user', input_prompt)
            ])
        else:
            prompt_template = ChatPromptTemplate.from_messages([
                ('system', system_prompt),
                ('user', input_prompt)
            ])

        if model_name == "deepseek-r1:32b":
            print("Your Model is deepseek-r1:32b")
            model = OllamaLLM(model=model_name)
        elif model_name == "deepseek-V3.2":
            print('Your Model is deepseek-V3.2')
            model = Ark(
                base_url=ARK_BASE_URL,
                api_key=ARK_API_KEY,
            )
        elif model_name == "deepseek-r1:671b":
            print('Your Model is deepseek-r1:671b')
            model = Ark(
                base_url=ARK_BASE_URL,
                api_key=ARK_API_KEY,
            )
        elif model_name == "gemma3:27b-q8":
            print("Your Model is gemma3:27b-q8")
            model = ChatOpenAI(
                model='gemma3:27b-q8',
                api_key=LOCAL_MODEL_A_API_KEY,
                base_url=LOCAL_MODEL_A_BASE_URL,
                temperature=0.7
            )
        elif 'gpt' in model_name:
            print('Your Model is gpt-5-mini')
            model = ChatOpenAI(
                model=model_name,
                api_key=os.environ['OPENAI_API_KEY'],
                base_url=os.environ['OPENAI_BASE_URL'],
            )
        elif 'qwen' in model_name:
            print('Your Model is', model_name)
            model = ChatOpenAI(
                model=model_name,
                api_key=LOCAL_MODEL_B_API_KEY,
                base_url=LOCAL_MODEL_B_BASE_URL,
            )
        else:
            print('unknown model, we choice to use gpt-5-mini')
            model = ChatOpenAI(
                model='gpt-5-mini',
                api_key=os.environ['OPENAI_API_KEY'],
                base_url=os.environ['OPENAI_BASE_URL'],
            )

        # Create parser
        if self.json_format:
            parser = JsonOutputParser()
        else:
            parser = StrOutputParser()

        if model_name in MODEL_IN_THINK:
            try:
                chain = prompt_template | model
                result = chain.invoke(input_param_dict)

                pattern = r"<think>(.*?)</think>"
                think = re.findall(pattern, str(result), re.DOTALL)[0]
                result = re.sub(pattern, '', str(result), flags=re.DOTALL)
                result = parser.invoke(result)
            except Exception as e:
                print("下面为错误信息")
                print(e)
                return 'llm报错'
        else:
            # chain = (prompt_template | model | parser)
            messages = prompt_template.invoke(input_param_dict).to_messages()
            # 执行工具调用
            if tools_used:
                result = model.invoke(messages, tools=tools_used)
            elif model_name in ARK_MODEL_LIST:
                ark_messages = []
                for msg in messages:
                    role = 'user'
                    if msg.type == 'system':
                        role = 'system'
                    elif msg.type == 'human':
                        role = 'user'
                    ark_messages.append({'role': role, 'content': msg.content})
                if model_name == "deepseek-V3.2":
                    result = model.chat.completions.create(
                        model="ep-20251226140226-2qv8z",
                        messages=ark_messages,
                        max_tokens=32768
                    )
                elif model_name == "deepseek-r1:671b":
                    result = model.chat.completions.create(
                        model="ep-20251227142844-2b2g6",
                        messages=ark_messages,
                        max_tokens=32768
                    )
            else:
                result = model.invoke(messages)

        # 如果模型调用了工具，则 result 可能是个 dict 包含 tool_calls
        if hasattr(result, "tool_calls") and result.tool_calls:
            print("检测到工具调用")
            for call in result.tool_calls:
                tool_name = call["name"]
                args = call["args"]
                print(f"➡ 调用工具: {tool_name}, 参数: {args}")

                if self.mcp_session:
                    tool_result = await self.mcp_session.call_tool(tool_name, args)
                    print(f"工具执行结果: {tool_result}")
                    result = model.invoke([
                        {"role": "user", "content": f"{tool_result}"}
                    ])

        try:
            if model_name in MODEL_IN_THINK:
                res = result
            elif model_name in ARK_MODEL_LIST:
                content = result.choices[0].message.content
                if "```" in content:
                    content = content.replace("```json", "").replace("```", "").strip()
                res = json.loads(content)
            else:
                res = parser.parse(result.content)
        except Exception as e:
            Print(f"BaseLLMAgent - Get Response Error: {e}", 'red')
            raw_content = ""
            try:
                # 1. 安全地提取原始内容（兼容不同 SDK）
                if model_name in ARK_MODEL_LIST:
                    # Ark SDK 结构
                    if hasattr(result, 'choices') and len(result.choices) > 0:
                        raw_content = result.choices[0].message.content
                    else:
                        raw_content = str(result)
                elif hasattr(result, 'content'):
                    raw_content = result.content
                else:
                    raw_content = str(result)

                # 2. 再次清洗
                if "```" in raw_content:
                    raw_content = raw_content.replace("```json", "").replace("```", "").strip()

                # 3. 使用容错能力更强的 demjson3 尝试修复
                res = demjson3.decode(raw_content)
                Print("BaseLLMAgent - Recovered from JSON error using demjson3", 'green')

            except Exception as inner_e:
                Print(f"Final parsing failed: {inner_e}", 'red')
                # 返回一个包含错误信息的字典，而不是让程序崩溃
                # 这样上层 Agent 可以根据 'error' 字段决定重试或跳过
                return {"error": "parsing_failed", "raw_content": raw_content}
        return res
