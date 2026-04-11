"""
    因果制图师
    A3 的任务是：在 A2 给出的世界观和数据约束下，围绕一个核心结果变量 Y（例如“涌现指标”），
    画出一张尽量可靠的因果图，并通过多轮与 A2 的反馈迭代，收敛到一个“数据能支持、世界观能解释”的版本。
"""
import asyncio
import json
from dataclasses import is_dataclass
from typing import List

from method.agents.BaseLLMAgent import BaseLLMAgent
from method.config.Setting import LLM_MODEL_NAME
from method.tools.printWithColor import Print


class CausalCartographAgent(BaseLLMAgent):
    def __init__(self,
                 name="CausalCartographAgent",
                 model_name=LLM_MODEL_NAME,
                 mcp_session=None):
        super().__init__(agent_name=name,
                         has_chat_history=False,
                         llm_model_name=model_name,
                         json_format=True,
                         system_prompt='',
                         mcp_session=mcp_session)
        self.system_prompt = '''
            你是一位经验丰富的因果制图师，擅长根据世界观和数据约束绘制因果图。你的任务是围绕一个核心结果变量 Y（例如“涌现指标”），
            画出一张尽量可靠的因果图，因果图需要收敛到一个“数据能支持、世界观能解释”的版本
        '''

    async def node_adaption(self,
                            req: str,
                            data_columns: List = None,
                            latent_variable: List = None,
                            certain_variables_names: List = None):
        """
            Task1: 节点适配：A2 的节点能不能在数据里站住脚
            Input:
                data_columns: 数据集的列名列表
                latent_variable: A2识别到的潜在变量列表
                certain_variables_names: 必须要保存的变量名称列表
            Output:
                variable_examination: 节点适配结果
        """
        Print("-------A3 - Task1: 节点适配-------", 'blue')
        info_prompt = '''
            - 你需要根据以下信息判断潜在变量集合中的变量能否站稳脚跟：
                1. 用户想要研究的问题：{req};
                2. 真实数据集中存在的变量: {data_columns};
                3. 我们之前根据'碎片事实'识别出的潜在变量集合: {latent_variable}
                4. 需要特别保留的变量名称列表: {certain_variables_names}
            - 你的任务是对于我们识别出的每一个潜在变量，判断其是否存在于数据集中，或能够根据显式的规则从数据集中存在的变量推导出该变量。
                对于'certain_variables_names'中的变量，必须要保留它们。
            - 你输出的是一个 JSON 对象，仅包含一个字段：
                "variable_examination": 一个字典列表，表示检测之后的结果，与潜在变量集合大小相同。每个字典包含两个字段：
                    "name": 潜在变量的名称；
                    "flag": 一共有三种取值：
                        "observable": 该变量的含义与数据集某一列含义相近或相同；
                        "constructible": 该变量在数据集没有直接列，但是可以根据潜在变量的描述或公式计算方法得出该变量可以由数据集中已有的列计算得出；
                        "uncertain": 无法确定该变量是否合理。
                    "explanation": 你做出该判断的依据。如果取值为'uncertain'，请说明缺少哪些信息导致无法判断。
                    "formula": 变量的计算公式或方法：
                        如果'flag'取值为'observable'，请给出该变量在数据集中对应的列名； 
                        如果'flag'取值为'constructible'，请给出该变量形式化的计算公式，如y=a+b*c，公式中涉及的内容仅'data_columns'中的变量名称；
                        如果'flag'的取值为'uncertain'，该字段取值为'uncertain'。
            - 对于'certain_variables_names'中存在的变量，请务必将其'flag'设置为'observable'或'constructible'。
            - 请严格按照上述格式输出，不要添加与输出无关的内容。
        '''
        param_dict = {
            'req': req,
            'data_columns': data_columns,
            'latent_variable': latent_variable,
            'certain_variables_names': certain_variables_names
        }
        variable_examination: List = []
        llm_response = await self.get_response(input_prompt=info_prompt,
                                               input_param_dict=param_dict,
                                               is_first_call=False)
        try:
            variable_examination = llm_response["variable_examination"]
        except Exception as e:
            Print(f"A3 - Node Adaption Error: {e}", 'red')
            print('llm_response', llm_response)
        save_by_line('../mapper/Output_A3/task1.jsonl', variable_examination, "A3 - Node Adaption")
        return variable_examination

    async def node_adaption_feedback(self,
                                     req: str,
                                     certainty_variables: List = None,
                                     data_columns: List = None):
        """
            Task1.5: 节点适配反馈：将节点适配的结果反馈给 A2，由 A2 进行迭代优化
            Input:
                req: 用户需求
                certainty_variables: Task1 选择保留的变量列表
                data_columns: 数据集中变量列表
            Output:
                需要反馈给 A2 的信息
        """
        Print("-------A3 - Task1.5: 节点适配反馈-------", 'blue')
        info_prompt = '''
            - A2 负责根据用户需求和'碎片事实'生成因果图中的变量，目前你已经根据Ground Truth确定了A2生成的变量中那些是合理需要保存的。
            - 现在你的任务是根据Ground Truth中的变量情况，给 A2 一些反馈建议，帮助 A2 优化其变量表。
            - 你已知的信息包括：
                1. 用户想要研究的问题：{req};
                2. 需要保留的变量列表: {certainty_variables};
                3. Ground Truth数据集中存在的变量: {data_columns}
            - 请根据以上信息，整理出需要反馈给 A2 的内容，帮助 A2 优化其世界观和变量表。
            - 你输出的是一个 JSON 对象，包含一个字段：
                "feedback_to_A2": 一个字符串，表示需要反馈给 A2 的内容，这是一个引导性的内容，返回的内容不超过100个字。比如返回的内容为'缺少与订单需求相关的变量'
            - 请严格按照上述格式输出，不要添加与输出无关的内容。
        '''
        param_dict = {
            'req': req,
            'certainty_variables': certainty_variables,
            'data_columns': data_columns
        }
        llm_response = await self.get_response(input_prompt=info_prompt,
                                               input_param_dict=param_dict,
                                               is_first_call=False)
        feedback_to_A2: str = ""
        try:
            feedback_to_A2 = llm_response["feedback_to_A2"]
        except Exception as e:
            Print(f"A3 - Node Adaption Feedback Error: {e}", 'red')
            print('llm_response', llm_response)
        return feedback_to_A2

    async def candidate_structure(self,
                                  req: str,
                                  world_driven_node: List = None,
                                  world_driven_structure: List = None,
                                  data_driven_node: List = None,
                                  data_driven_structure: List = None,
                                  node_adaption_res: List = None):
        """
            Task2: 候选结构：合并 world-driven 和 data-driven 两部分得到 E(t) ，并给每条边打上来源标签：
            Input:
                req: 用户需求
                world_driven_node: 基于世界观得到的节点列表
                world_driven_structure: 基于世界观得到的因果结构
                data_driven_node: 基于数据得到的节点列表
                data_driven_structure: 基于数据得到的因果结构
                node_adaption_res: 节点适配结果
            Output:
                candidate_structure: 最终的候选因果结构 E(t)
        """
        Print("-------A3 - Task2: 候选结构-------", 'blue')
        info_prompt = '''
            - 你需要根据以下信息合并两部分因果结构，得到最终的候选因果结构 E(t)：
                1. 用户想要研究的问题：{req};
                2. 基于世界观得到的节点列表: {world_driven_node};
                3. 基于世界观得到的因果结构: {world_driven_structure};
                3. 基于数据得到的节点列表: {data_driven_node};
                5. 基于数据得到的因果结构: {data_driven_structure};
                6. 节点适配结果: {node_adaption_res}
            - 你的任务是参考节点适配结果，将两部分因果结构进行合并，得到最终的候选因果结构 E(t)。
            - 合并因果图时你需要额外注意'node_adaption_res'中的'formula'字段，如果某个变量是通过公式计算得到的，那么在合并因果图时需要添加相应的边。
            - 对于每一条边，你需要打上来源标签，表示该边是来自于世界观、数据驱动，还是两者皆有支持。
            - 你输出的是一个 JSON 对象，包含一个字段：
                "candidate_structure": 一个字典列表，表示最终的候选因果结构 E(t)。每个字典包含四个字段：
                    "source": 边的起始节点名称；
                    "target": 边的终止节点名称；
                    "description": 该边的描述，简要说明该边的含义；
                    "support_estimation": 该边的置信度，取值范围为 0 到 1 之间的浮点数，根据世界观因果结构中边的置信度和由数据得到的因果结构重新判断，数值越大表示支持程度越高；
                    "flag": 该边的来源标签，一共有三种取值：
                        "world": 该边仅来自于世界观；
                        "data": 该边仅来自于数据驱动；
                        "both": 该边同时来自于世界观和数据驱动。
            - 注意，节点适配的结果非常重要，你需要做的不仅仅是两部分的简单合并，而是要参考节点适配的结果，对因果结构进行调整和优化。
            - 请严格按照上述格式输出，不要添加与输出无关的内容。
        '''
        param_dict = {
            'req': req,
            'world_driven_node': world_driven_node,
            'world_driven_structure': world_driven_structure,
            'data_driven_node': data_driven_node,
            'data_driven_structure': data_driven_structure,
            'node_adaption_res': node_adaption_res
        }
        candidate_structure: List = []
        llm_response = await self.get_response(input_prompt=info_prompt,
                                               input_param_dict=param_dict,
                                               is_first_call=False)
        try:
            candidate_structure = llm_response["candidate_structure"]
        except Exception as e:
            Print(f"A3 - Candidate Structure Error: {e}", 'red')
            print('llm_response', llm_response)
        save_by_line('../mapper/Output_A3/task2.jsonl', candidate_structure, "A3 - Candidate Structure")
        return candidate_structure

    async def edge_identifiability(self,
                                   req: str,
                                   candidate_structure: List = None):
        """
            Task3: 给边打“可识别性”标签
            将因果图中的每条边打上“可识别性”标签，标签分为三类：
                “identifiable”：在当前图结构和假设下，因果方向基本确定，且有标准办法估计因果效应；
                "assumption-dependent"：需要额外假设线性、可忽略性、无未观测混杂等才能识别；
                “non-identifiable”：方向 / 效应在理论上就是不确定的，只能作为相关性或机制假设存在
            Input:
                req: 用户需求
                candidate_structure: 候选因果结构 E(t)
            Output:
                edge_identifiability: 给边打上“可识别性”标签后的因果结构
        """
        Print("-------A3 - Task3: 边的可识别性-------", 'blue')
        info_prompt = '''
            - 你需要根据以下信息给因果图中的每条边打上“可识别性”标签：
                1. 用户想要研究的问题：{req};
                2. 候选因果结构 E(t): {candidate_structure}
            - 你的任务是参考候选因果结构 E(t)，将每一条边打上“可识别性”标签，标签分为三类：
                “identifiable”：在当前图结构和假设下，因果方向基本确定，且有标准办法估计因果效应；
                "assumption-dependent"：需要额外假设线性、可忽略性、无未观测混杂等才能识别；
                “non-identifiable”：方向 / 效应在理论上就是不确定的，只能作为相关性或机制假设存在
            - 你输出的是一个 JSON 对象，包含一个字段：
                "edge_identifiability": 一个字典列表，表示给边打上“可识别性”标签后的因果结构。每个字典包含五个字段：
                    "source": 边的起始节点名称；
                    "target": 边的终止节点名称；
                    "description": 该边的描述，简要说明该边的含义；
                    "support_estimation": 该边的置信度；
                    "flag": 该边的来源标签；
                    "identifiability_flag": 该边的“可识别性”标签，一共有三种取值：
                        “identifiable”：在当前图结构和假设下，因果方向基本确定，且有标准办法估计因果效应；
                        "assumption-dependent"：需要额外假设线性、可忽略性、无未观测混杂等才能识别；
                        “non-identifiable”：方向/效应在理论上就是不确定的，只能作为相关性或机制假设存在
            - 请严格按照上述格式输出，不要添加与输出无关的内容。只有'可识别性'需要你去设计，其他字段请保持与输入一致。
        '''
        param_dict = {
            'req': req,
            'candidate_structure': candidate_structure
        }
        edge_identifiability: List = []
        llm_response = await self.get_response(input_prompt=info_prompt,
                                               input_param_dict=param_dict,
                                               is_first_call=False)
        try:
            edge_identifiability = llm_response["edge_identifiability"]
        except Exception as e:
            Print(f"A3 - Edge Identifiability Error: {e}", 'red')
            print('llm_response', llm_response)
        save_by_line('../mapper/Output_A3/task3.jsonl', edge_identifiability, "A3 - Edge Identifiability")
        return edge_identifiability

    async def feedback_iteration(self,
                                 req: str,
                                 candidate_structure: List = None,
                                 outcome_variable: str = None):
        """
            Task4: 反馈迭代
            在这张因果图下，结果变量 Y 的哪些部分还解释得很差？A3 把这些“解释盲点”整理成反馈项
            这些反馈组成 F(t)，送回 A2。A2 据此修订世界观和变量表
        """
        Print("-------A3 - Task4: 反馈迭代-------", 'blue')
        info_prompt = '''
            - 你的任务是根据当前的因果图，找出结果变量 Y 的哪些部分还解释得很差，并将这些“解释盲点”整理成反馈项，例如：
                “在某类制度环境下，模型持续低估 Y，可能缺少这类环境相关的制度变量”；
                X 与 Y 在当前 Markov Blanket 条件下仍强相关，可能存在未建模的共同原因或中介节点”。
            - 你已知的信息包括：
                1. 用户想要研究的问题：{req};
                2. 当前的候选因果结构 E(t): {candidate_structure};
                3. 结果变量 Y 的名称: {outcome_variable}
            - 你输出的是一个 JSON 对象，包含一个字段：
                "feedback_items": 一个字符串列表，表示整理出的反馈项列表。
            - 请严格按照上述格式输出，不要添加与输出无关的内容。
        '''
        param_dict = {
            'req': req,
            'candidate_structure': candidate_structure,
            'outcome_variable': outcome_variable
        }
        feedback_items: List = []
        llm_response = await self.get_response(input_prompt=info_prompt,
                                               input_param_dict=param_dict,
                                               is_first_call=False)
        try:
            feedback_items = llm_response["feedback_items"]
        except Exception as e:
            Print(f"A3 - Feedback Iteration Error: {e}", 'red')
            print('llm_response', llm_response)
        save_by_line('../mapper/Output_A3/task4.jsonl', feedback_items, "A3 - Feedback Iteration")
        return feedback_items


def save_by_line(file_path, data_list, prompt=""):
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            for data in data_list:
                if is_dataclass(data):
                    data = data.to_dict()
                json_line = json.dumps(data, ensure_ascii=False)
                f.write(json_line + '\n')
        Print(f"{prompt} Data saved to {file_path}", 'green')
    except Exception as e:
        Print(f"{prompt} Saving data Error: {e}", 'red')


def get_by_line(file_path):
    data_list = []
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                data_list.append(json.loads(line))
    except Exception as e:
        Print(f"Loading data from {file_path} Error: {e}", 'red')
    return data_list


def get_dict(file_path):
    data_dict = {}
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data_dict = json.load(f)
    except Exception as e:
        Print(f"Loading dict from {file_path} Error: {e}", 'red')
    return data_dict


async def run():
    # 用户需求
    req_file_path = "../mapper/Requirement.json"
    try:
        with open(req_file_path, 'r', encoding='utf-8') as f:
            req_data = json.load(f)
    except Exception as e:
        Print(f"Load requirement from {req_file_path} Error: {e}", 'red')
    req = req_data['req']
    sample_facts = req_data['sample_facts']

    agent = CausalCartographAgent()
    # Task1：节点适配
    latent_variables = get_by_line(file_path='../mapper/Output_A2/task1.jsonl')
    data_column = get_dict(file_path='../mapper/Baseline_mt/baseline_nodes.json')
    node_adaption_res = await agent.node_adaption(req=req,
                                                  data_columns=data_column,
                                                  latent_variable=latent_variables)
    # TODO 将适配结果反馈给A2，由A2进行迭代优化
    pass
    # Task2：候选结构
    # TODO 获取world-driven结构（简单处理A2的最终输出）
    world_driven_node = latent_variables  # 暂时先用潜在变量代替
    world_driven_structure = get_by_line(file_path='../mapper/Output_A2/task4.jsonl')
    world_driven_structure = world_driven_structure[0]
    # TODO 获取data-driven结构（使用简单的因果算法获取根据数据列生成的因果图，这里暂时用已经生成好的图代替）
    data_driven_node = data_column
    data_driven_structure = get_dict('../mapper/Baseline_mt/baseline_edges.json')

    candidate_structure_res = await agent.candidate_structure(req=req,
                                                              world_driven_node=world_driven_node,
                                                              world_driven_structure=world_driven_structure,
                                                              data_driven_node=data_driven_node,
                                                              data_driven_structure=data_driven_structure,
                                                              node_adaption_res=node_adaption_res)
    # Task3: 可识别性
    edge_identifiability_res = await agent.edge_identifiability(req=req,
                                                                candidate_structure=candidate_structure_res)
    # Task4: 反馈迭代
    feed_back = await agent.feedback_iteration(req=req,
                                               candidate_structure=edge_identifiability_res,
                                               outcome_variable="涌现现象")
    # TODO 将反馈送回A2，由A2进行迭代优化


if __name__ == '__main__':
    asyncio.run(run())
