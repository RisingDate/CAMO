import asyncio
import json
from dataclasses import is_dataclass
from typing import List, Dict

from method.agents.BaseLLMAgent import BaseLLMAgent
from method.config.Setting import LLM_MODEL_NAME
from method.tools.printWithColor import Print


class CounterfactualVerificationAgent(BaseLLMAgent):
    def __init__(self,
                 name="CounterfactualVerificationAgent",
                 model_name=LLM_MODEL_NAME,
                 mcp_session=None):
        super().__init__(agent_name=name,
                         has_chat_history=False,
                         llm_model_name=model_name,
                         json_format=True,
                         system_prompt='',
                         mcp_session=mcp_session)
        self.system_prompt = '''
            你是一位反事实验证专家，负责设计仿真实验并根据实验结果验证因果图的可靠性。
            你的任务包括评估模型可信度、设计反事实实验、验证因果边以及修正因果图。
        '''

    async def evaluate_model_credibility(self,
                                         simulation_output: Dict,
                                         real_observation: Dict):
        """
            Task1: 模型可信度评价
            比较仿真输出与现实观测，得到 C_model
            Input:
                simulation_output: 仿真输出
                real_observation: 现实观测
            Output:
                credibility_res: 可信度评价结果
        """
        Print("-------A5 - Task1: 模型可信度评价-------", 'blue')
        info_prompt = '''
            - Task: Evaluate Model Credibility (C_model)
            - Please compare the simulation output with real-world observations to evaluate the model's credibility.
            - Simulation Output: {simulation_output}
            - Real-world Observations: {real_observation}
            - Requirements:
                - Compare key statistical metrics.
                - Calculate a credibility score C_model between 0 and 1.
                - 1 indicates a perfect match, 0 indicates no resemblance.
                - If C_model is low, the simulation results should be treated as "model-internal evidence" only.
            - Output Format (JSON):
                {{
                    "credibility_score": <float>,
                    "explanation": "<string>"
                }}
        '''
        param_dict = {
            'simulation_output': simulation_output,
            'real_observation': real_observation
        }

        llm_response = await self.get_response(input_prompt=info_prompt,
                                               input_param_dict=param_dict,
                                               is_first_call=False)
        try:
            return llm_response
        except Exception as e:
            Print(f"A5 - Evaluate Model Credibility Error: {e}", 'red')
            print('llm_response', llm_response)
            return {}

    async def design_counterfactual_experiments(self,
                                                task1_data: List,
                                                task2_data: List):
        """
            Task2: 实验设计
            获取task1.jsonl(所有潜在变量)和task2.jsonl(第一行，目标变量)，设计实验点。
            Input:
                task1_data: 所有潜在变量
                task2_data: 目标变量数据
            Output:
                experiment_design: 实验设计结果
        """
        Print("-------A5 - Task2: 实验设计-------", 'blue')

        target_variable = task2_data[0] if task2_data else {}

        info_prompt = '''
            - Task: Design Counterfactual Experiments
            - Input Data:
                1. All Potential Variables (System Variables): {all_variables}
                2. Target Variable for Intervention: {target_variable}
            - Requirements:
                1. Design a 'Default Setting' where all variables are assigned reasonable default values based on their descriptions.
                2. Design 'Intervention Settings' for the Target Variable. Create different values (counterfactuals) for the target variable while keeping others at default.
                3. The goal is to test the effect of the Target Variable on the system.
            - Output Format (JSON):
                {{
                    "default_values": {{ "var_name": "value", ... }},
                    "experiments": [
                        {{
                            "experiment_id": "exp_1",
                            "description": "Baseline",
                            "settings": {{ "var_name": value, ... }} 
                        }},
                        {{
                            "experiment_id": "exp_2",
                            "description": "Intervention 1",
                            "settings": {{ "var_name": value, ... }}
                        }},
                        ...
                    ]
                }}
        '''
        param_dict = {
            'all_variables': task1_data,
            'target_variable': target_variable
        }

        llm_response = await self.get_response(input_prompt=info_prompt,
                                               input_param_dict=param_dict,
                                               is_first_call=False)

        save_by_line('../mapper/Output_A5/task2.jsonl', [llm_response], "A5 - Experiment Design")
        return llm_response

    async def verify_causal_edges(self,
                                  simulation_results: Dict,
                                  causal_graph: List,
                                  model_credibility: float):
        """
            Task3: 因果边验证
            根据仿真结果(json)和因果图(task3.jsonl)，为每条边赋予多维标签。
            Input:
                simulation_results: 仿真结果
                causal_graph: 因果图
                model_credibility: 模型可信度
            Output:
                verified_edges: 验证后的因果边
        """
        Print("-------A5 - Task3: 因果边验证-------", 'blue')

        info_prompt = '''
            - Task: Verify Causal Edges based on Simulation Results
            - Context:
                - Model Credibility Score: {model_credibility}
                - If credibility is low, findings are considered "In-model evidence" only.
            - Input:
                1. Causal Graph (Hypotheses): {causal_graph}
                2. Simulation Results: {simulation_results}
            - Requirements:
                - For each edge in the Causal Graph, determine the level of support provided by the simulation results.
                - Assign one of the following labels:
                    - "In-model strong support"
                    - "In-model partial support"
                    - "In-model refutation"
                    - "Insufficient evidence"
            - Output Format (JSON):
                [
                    {{
                        "source": "var_a",
                        "target": "var_b",
                        "verification_label": "Label",
                        "reasoning": "..."
                    }},
                    ...
                ]
        '''
        param_dict = {
            'model_credibility': model_credibility,
            'causal_graph': causal_graph,
            'simulation_results': simulation_results
        }

        llm_response = await self.get_response(input_prompt=info_prompt,
                                               input_param_dict=param_dict,
                                               is_first_call=False)

        verified_edges = llm_response if isinstance(llm_response, list) else []
        save_by_line('../mapper/Output_A5/task3.jsonl', verified_edges, "A5 - Verify Causal Edges")
        return verified_edges

    async def refine_causal_graph(self, verified_edges: List):
        """
            Task4: 修正因果图
            根据验证结果修改因果图结构并返回。
            Input:
                verified_edges: 验证后的因果边
            Output:
                refined_graph: 修正后的因果图
        """
        Print("-------A5 - Task4: 修正因果图-------", 'blue')

        info_prompt = '''
            - Task: Refine Causal Graph Structure
            - Input:
                - Verified Edges with Labels: {verified_edges}
            - Requirements:
                - Analyze the verification labels.
                - Remove edges with "In-model refutation".
                - Keep edges with "In-model strong support" or "In-model partial support".
                - For "Insufficient evidence", decide whether to keep (as uncertain) or remove based on the context.
                - Return the final list of edges representing the refined causal graph.
            - Output Format (JSON):
                [
                    {{
                        "source": "var_a",
                        "target": "var_b",
                        "relation": "..."
                    }},
                    ...
                ]
        '''
        param_dict = {
            'verified_edges': verified_edges
        }

        llm_response = await self.get_response(input_prompt=info_prompt,
                                               input_param_dict=param_dict,
                                               is_first_call=False)

        refined_graph = llm_response if isinstance(llm_response, list) else []
        save_by_line('../mapper/Output_A5/task4.jsonl', refined_graph, "A5 - Refine Causal Graph")
        return refined_graph


def save_by_line(file_path, data_list, prompt=""):
    try:
        import os
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
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
    agent = CounterfactualVerificationAgent()

    # Mock data for testing
    # Task 1
    sim_output = {"metric_a": 10, "metric_b": 0.5}
    real_obs = {"metric_a": 12, "metric_b": 0.45}
    credibility_res = await agent.evaluate_model_credibility(sim_output, real_obs)
    credibility_score = credibility_res.get("credibility_score", 0.5)

    # Task 2
    # Assuming files exist or passing empty lists for test
    # In a real scenario, these paths should be correct
    task1_data = [] # get_by_line('../mapper/Output_A1/task1.jsonl')
    task2_data = [] # get_by_line('../mapper/Output_A1/task2.jsonl')

    experiment_design = await agent.design_counterfactual_experiments(task1_data, task2_data)

    # Task 3
    # Mock simulation result based on experiment design
    sim_results = {"exp_1": "result_1", "exp_2": "result_2"}
    task3_data = [] # get_by_line('../mapper/Output_A3/task3.jsonl')

    verified_edges = await agent.verify_causal_edges(sim_results, task3_data, credibility_score)

    # Task 4
    refined_graph = await agent.refine_causal_graph(verified_edges)


if __name__ == '__main__':
    asyncio.run(run())

