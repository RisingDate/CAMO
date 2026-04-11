"""
    脚本工匠
    A4 的任务是：围绕每条候选边设计结构化的仿真实验包，用仿真实验对 A3 标记的“重要且不确定”的因果边做反事实检验
"""
import asyncio
import json
from dataclasses import is_dataclass
from typing import List

from method.agents.BaseLLMAgent import BaseLLMAgent
from method.tools.printWithColor import Print
from method.config.Setting import LLM_MODEL_NAME


class ScriptCraftsman(BaseLLMAgent):
    def __init__(self,
                 name="ScriptCraftsman",
                 model_name=LLM_MODEL_NAME,
                 mcp_session=None):
        super().__init__(agent_name=name,
                         has_chat_history=False,
                         llm_model_name=model_name,
                         json_format=True,
                         system_prompt='',
                         mcp_session=mcp_session)
        self.system_prompt = '''
            你是一位经验丰富的脚本工匠，擅长设计结构化的仿真实验包。你的任务是围绕每条候选边设计结构化的仿真实验包，
            用仿真实验对“重要且不确定”的因果边做反事实检验。
        '''

    async def edge_importance(self, req: str, candidate_structure: List = None):
        """
            Task1: 边重要性评估
            Input:
                req: 用户需求
                candidate_structure: A3 输出的因果结构 (包含可识别性标签)
            Output:
                edge_importance_res: 增加了重要性评估的因果结构
        """
        info_prompt = '''
            - 你需要根据以下信息评估因果结构中每条边对核心目标的敏感度（重要性）：
                1. 用户想要研究的问题：{req};
                2. 候选因果结构 E(t): {candidate_structure}
            - 你的任务是参考候选因果结构 E(t)，为每一条边增加“重要性”评估。
            - “重要性”反映该边对核心目标的敏感度（如对关键 KPI 的因果弹性）。
            - 你输出的是一个 JSON 对象，包含一个字段：
                "edge_importance_res": 一个字典列表，表示增加了重要性评估后的因果结构。每个字典包含以下字段：
                    "source": 边的起始节点名称；
                    "target": 边的终止节点名称；
                    "description": 该边的描述；
                    "support_estimation": 该边的置信度；
                    "flag": 该边的来源标签；
                    "identifiability_flag": 该边的“可识别性”标签；
                    "importance": 该边的重要性评分，取值范围为 0 到 1 之间的浮点数，数值越大表示越重要；
                    "importance_explanation": 对重要性评分的简要解释。
            - 请严格按照上述格式输出，不要添加与输出无关的内容。保留原有字段，新增 importance 和 importance_explanation 字段。
        '''
        param_dict = {
            'req': req,
            'candidate_structure': candidate_structure
        }
        edge_importance_res: List = []
        llm_response = await self.get_response(input_prompt=info_prompt,
                                               input_param_dict=param_dict,
                                               is_first_call=False)
        try:
            edge_importance_res = llm_response["edge_importance_res"]
        except Exception as e:
            Print(f"A4 - Edge Importance Error: {e}", 'red')
            print('llm_response', llm_response)
        save_by_line('../mapper/Output_A4/task1.jsonl', edge_importance_res, "A4 - Edge Importance")
        return edge_importance_res

    def experiment_priority(self, edge_importance_res: List, beta: float = 1.0):
        """
            Task2: 实验优先级排序
            score = 重要性 * 不确定度 * beta * support_estimation
            Input:
                edge_importance_res: Task1 输出的带有重要性的因果结构
                beta: 调节常数
            Output:
                priority_res: 排序后的因果结构
        """
        uncertainty_map = {
            "non-identifiable": 1.0,
            "assumption-dependent": 0.8,
            "identifiable": 0.5
        }

        priority_res = []
        for edge in edge_importance_res:
            importance = edge.get('importance', 0.0)
            identifiability = edge.get('identifiability_flag', 'identifiable')
            uncertainty = uncertainty_map.get(identifiability, 0.5)
            support = edge.get('support_estimation', 0.0)

            # Calculate score
            score = importance * uncertainty * beta * support

            edge_with_score = edge.copy()
            edge_with_score['score'] = score
            priority_res.append(edge_with_score)

        # Sort by score descending
        priority_res.sort(key=lambda x: x['score'], reverse=True)

        save_by_line('../mapper/Output_A4/task2.jsonl', priority_res, "A4 - Experiment Priority")
        return priority_res


def save_by_line(file_path, data_list, prompt=""):
    import os
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
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
        return
    req = req_data['req']

    agent = ScriptCraftsman()

    # Task1: 边重要性评估
    # 获取 A3 Task3 的输出
    candidate_structure = get_by_line(file_path='../mapper/Output_A3/task3.jsonl')

    edge_importance_res = await agent.edge_importance(req=req,
                                                      candidate_structure=candidate_structure)

    # Task2: 实验优先级排序
    priority_res = agent.experiment_priority(edge_importance_res=edge_importance_res, beta=1.0)


if __name__ == '__main__':
    asyncio.run(run())
