"""
    A2 接过 A1 的输出，面对现实中的“多视角、多数据源、多解释”的冲突，对世界观进行统一与决议。
"""
import asyncio
import json
from dataclasses import is_dataclass
from typing import List

from method.agents.BaseLLMAgent import BaseLLMAgent
from method.config.Setting import LLM_MODEL_NAME
from method.tools.printWithColor import Print


class ConflictMediationAgent(BaseLLMAgent):
    def __init__(self,
                 name: str = "ConflictMediationAgent",
                 model_name: str = LLM_MODEL_NAME,
                 mcp_session=None):
        super().__init__(agent_name=name,
                         has_chat_history=False,
                         llm_model_name=model_name,
                         json_format=True,
                         system_prompt='',
                         mcp_session=mcp_session)
        self.system_prompt = '''
            你正在解析"碎片事实"中的因果关系，目前已经进行了简单的解析并获取了不同视角下的世界观。
            你的任务是面对现实中的“多视角、多数据源、多解释”的冲突，对世界观进行统一与决议。
        '''

    async def language_unification(self,
                                   req: str = "",
                                   fragmented_facts=None,
                                   latent_variables: List[dict] = None) -> List[dict]:
        """
            Task1：统一语言与口径，对潜在变量进行去重和统一
            req: 用户需求
            fragmented_facts: 碎片事实
            latent_variables: 潜在变量集合
        """
        Print("-------A2 - Task1: 统一语言与口径-------", 'blue')
        info_prompt = '''
            - 你正在对世界观中的潜在变量进行统一与去重，你所了解的内容为：
                你的需求目标是：{req}；
                解析世界观所用的"碎片事实"：{fragmented_facts}，
                以不同视角解析到的潜在变量集合为：{latent_variables}
            - 你需要检测潜在变量集合中语义相同但命名不同的指标，之后将统一化之后的变量放到同一个列表中。
                需要统一化的变量如“订单取消率”和“履约失败率”；
            - 你有两个任务：
                1. 对这些指标进行对齐并统一统计口径，对齐后的指标需要尽可能的基础，能够适配大多数环境； 
                2. 对每一关键指标给出唯一、清晰的定义；
            - 你返回的结果需要符合 JSON 格式，具体字段如下：
                "unified_indicators": 统一化后的指标列表，包含每个指标的名称、定义、计算公式、数据源和时间窗口，列表中每个元素均为一个字典，字典描述如下:
                    "name": 指标名称;
                    "description": 指标的唯一定义;
                    "calculation_formula": 指标的计算公式;
                    "data_source": 指标的数据来源;
                    "time_window": 指标的时间窗口;
        '''
        param_dict = {
            "req": req,
            "fragmented_facts": fragmented_facts,
            "latent_variables": latent_variables
        }
        unified_indicators: List[dict] = []
        llm_response = await self.get_response(input_prompt=info_prompt,
                                               input_param_dict=param_dict,
                                               is_first_call=False)
        try:
            unified_indicators = llm_response['unified_indicators']
        except Exception as e:
            Print(f"A2 - Language Unification Error: {e}", 'red')
            print('llm_response', llm_response)

        save_by_line("../mapper/Output_A2/task1.jsonl", unified_indicators, prompt="A2 - Language Unification")

        return unified_indicators

    async def determine_variable_links(self,
                                       req: str = "",
                                       behavior_patterns: List[dict] = None,
                                       unified_latent_variables: List[dict] = None) -> List[dict]:
        """
            Task2：确定变量间的关联关系
            req: 用户需求
            behavior_patterns: 行为模式集合
            unified_latent_variables: 统一化后的潜在变量集合
        """
        Print("-------A2 - Task2: 确定因果图连边-------", 'blue')
        info_prompt = '''
            - 你正在对世界观中的潜在变量进行关联关系的确定，已知的信息如下：
                你的需求目标是：{req}；
                行为模式集合为：{behavior_patterns}；
                潜在变量集合为：{unified_latent_variables}
            - 你的任务是针对需求目标和行为模式，确定'潜在变量集合'中变量间的关联关系。
            - 你的输出需要符合 JSON 格式，具体字段如下：
                "variable_links": 变量关联关系列表，包含每个变量及其关联变量，列表中每个元素均为一个字典，字典描述如下:
                    "name": 变量名称;
                    "targets": 与该变量关联的其他变量列表，列表中每个元素均为一个字典，字典描述如下:
                        "name": 关联变量名称;
                        "description": 关联关系的描述;
            - 请注意，关联关系中变量必须在潜在变量中选取。若两个变量之间存在多个关系，需要全部放入关联关系列表中。
        '''
        param_dict = {
            "req": req,
            "behavior_patterns": behavior_patterns,
            "unified_latent_variables": unified_latent_variables
        }
        llm_response = await self.get_response(input_prompt=info_prompt,
                                               input_param_dict=param_dict,
                                               is_first_call=False)
        variable_links: List[dict] = []
        try:
            pre_links = llm_response['variable_links']
            for item in pre_links:
                for target in item['targets']:
                    variable_links.append({
                        "source": item['name'],
                        "target": target['name'],
                        "description": target['description']
                    })
        except Exception as e:
            Print(f"A2 - Determine Variable Links Error: {e}", 'red')
        save_by_line("../mapper/Output_A2/task2.jsonl", variable_links,
                     prompt="A2 - Determine Variable Links")
        return variable_links

    async def maintain_competing_explanations(self,
                                              req: str = "",
                                              fragmented_facts=None,
                                              latent_variables: List[dict] = None,
                                              behavior_patterns: List[dict] = None,
                                              variable_links: List[dict] = None,
                                              extra_hint: str = "") -> List[dict]:
        """
            Task3：显式记录竞争解释集合
            req: 用户需求
            latent_variables: 潜在变量集合
            behavior_patterns: 行为模式集合
            variable_links: 变量关联关系集合
        """
        Print("-------A2 - Task3: 显式记录竞争解释集合-------", 'blue')
        info_prompt = '''
            - 你正在检索变量之间关联关系是否存在竞争解释，目前已知的信息如下：
                你的需求目标是：{req}；
                潜在变量集合为：{latent_variables}；
                行为模式集合为：{behavior_patterns}；
                解析世界观使用的碎片事实为：{fragmented_facts}；
                潜在变量之间的关联关系为：{variable_links}；
                额外提示信息：{extra_hint}
            - 你的任务是根据需求目标，维护和拓展'潜在变量之间的关联关系'集合，通过检索原始潜在变量、行为模式集合和碎片事实，查询该关联关系是否存在竞争解释。
            - 请重视，竞争解释之间应存在较大的差异，若差异不大则不构成竞争解释。
            - 你的输出需要符合 JSON 格式，具体字段如下：
                "competition_relationship": 拓展后的变量之间的关联关系集合，列表中每个元素均为一个字典，字典描述如下:
                    "source": 关联关系中源节点变量名称;
                    "target": 关联关系中目标节点变量名称;
                    "explanations": 该关联关系的竞争解释列表，每个解释均为一个字典，字典描述如下:
                        "text": 该变量的解释内容;
                        "prerequisites": 此解释的前提条件;
                        "evidence": 该解释所依据的支持证据;
                        "support_estimation": 该解释的支持度估计，是一个0~1之间的两位浮点数;
            - 请注意，只有一个解释的关联关系也应该出现在竞争解释集合中，拓展后的变量之间的关联关系集合的长度和'潜在变量之间关联关系集合'长度相同。
        '''
        param_dict = {
            "req": req,
            "fragmented_facts": fragmented_facts,
            "latent_variables": latent_variables,
            "behavior_patterns": behavior_patterns,
            "variable_links": variable_links,
            "extra_hint": extra_hint
        }
        llm_response = await self.get_response(input_prompt=info_prompt,
                                               input_param_dict=param_dict,
                                               is_first_call=False)
        competition_relationship: List[dict] = []
        try:
            competition_relationship = llm_response['competition_relationship']
        except Exception as e:
            Print(f"A2 - Maintain Competing Explanations Error: {e}", 'red')
        save_by_line("../mapper/Output_A2/task3.jsonl", competition_relationship,
                     prompt="A2 - Maintain Competing Explanations")

        return competition_relationship

    async def rating_and_selection(self,
                                   links: List[dict] = None,
                                   alpha: float = 0.5,
                                   beta: float = 0.2,
                                   gemma: float = 0.3) -> dict:
        """
            Task4：评分与选择最佳世界观
        """
        Print("-------A2 - Task4: 评分与选择最佳世界观-------", 'blue')
        info_prompt = '''
            - 你正在对世界观中的因果关系进行评分，目前初步形成的因果图为：{links}
            - 你的任务是从三个角度对该因果图进行评分。
            - 你的输出需要符合 JSON 格式，具体字段如下：
                "fit": 因果模型对关键观测现象的拟合度评分，取值范围0~100的整数，分数越高表示拟合度越好;
                "simplicity": 结构简洁程度评分，取值范围0~100的整数，分数越高表示结构越简洁，变量数量越多、关系越复杂的惩罚越高;
                "explainability": 因果图中业务可解释性、决策可沟通性的评分，取值范围0~100的整数，分数越高表示可解释
        '''
        param_dict = {
            "links": links
        }
        llm_response = await self.get_response(input_prompt=info_prompt,
                                               input_param_dict=param_dict,
                                               is_first_call=False)
        rating_param = dict(rating=0.0, fit=0, simplicity=0, explainability=0)
        try:
            rating_param['fit'] = llm_response['fit']
            rating_param['simplicity'] = llm_response['simplicity']
            rating_param['explainability'] = llm_response['explainability']
            rating_param['rating'] = (alpha * rating_param['fit'] +
                                      beta * rating_param['simplicity'] +
                                      gemma * rating_param['explainability'])
        except Exception as e:
            Print(f"A2 - Rating and Selection Error: {e}", 'red')
        return rating_param

    async def reassess_uncertain_variables(self,
                                           req: str = "",
                                           uncertain_latent_variables: List[dict] = None,
                                           uncertain_variables: List[dict] = None,
                                           fragmented_facts=None,
                                           gt_feedback: str = "") -> List[dict]:
        """
            Task5: 重新审视不确定变量
            A3的Task1生成的结果中，对于标记flag为'uncertain'的变量需要由A2重新去重新审视这个变量到底是不是真正应该属于因果图
        """
        Print("-------A2 - Task5: 重新审视不确定变量-------", 'blue')
        info_prompt = '''
            - 在结合数据集含有的列信息后，智能体A3对世界观解析出的潜在变量进行了标记，其中无法从数据集中找到对应列或无法根据数据集构造出的变量被标记为'uncertain'。
            - 你正在重新审视被标记为'uncertain'的变量，目前已知的信息如下：
                1. 用户的需求目标是：{req}；
                2. 解析世界观使用的碎片事实为：{fragmented_facts}；
                3. 被标记为'uncertain'的潜在变量集合为：{uncertain_latent_variables}；
                4. 被A3标记为'uncertain'的变量及其原因: {uncertain_variables}；
                5. 根据真实数据集的反馈信息：{gt_feedback}；
            - 你的任务是根据真实数据集的反馈信息来重新判断这些变量是否真正应该属于因果图。
            - 你的回复必须严格遵循 JSON 格式，具体字段如下：
                "uncertain_variable_reassess": 一个字典列表，是你对'uncertain_latent_variables'中每个变量的重新审视结果，列表中每个元素均为一个字典，字典描述如下:
                    "name": 变量名称；
                    "is_important": 该变量是否重要且应该保留，布尔值；
                    "reason": 你做出该判断的原因；
            - 请注意，A3的提示非常重要，请仔细考虑。每次最多对其中3个最不靠谱变量的'is_important'字段标记为False，并给出相应的'reason'，其他变量均标记为True。
        '''
        param_dict = {
            "req": req,
            "fragmented_facts": fragmented_facts,
            "uncertain_latent_variables": uncertain_latent_variables,
            "uncertain_variables": uncertain_variables,
            "gt_feedback": gt_feedback
        }
        llm_response = await self.get_response(input_prompt=info_prompt,
                                               input_param_dict=param_dict,
                                               is_first_call=False)
        uncertain_variable_reassess = []
        try:
            uncertain_variable_reassess = llm_response.get("uncertain_variable_reassess", [])
        except Exception as e:
            Print(f"A2 - Reassess Uncertain Variables Error: {e}", 'red')

        return uncertain_variable_reassess

    async def uncertain_latent_variables_regeneration(self,
                                                      req: str = "",
                                                      fragmented_facts=None,
                                                      certainty_latent_variables: List[dict] = None,
                                                      uncertain_latent_variables: List[dict] = None,
                                                      uncertain_latent_variable_reassess: List[dict] = None,
                                                      gt_feedback: str = "") -> List[dict]:
        """
            Task6：潜在变量再生成
            req: 用户需求
            fragmented_facts: 碎片事实
            certainty_latent_variables: 确定保留的潜在变量集合
            uncertain_latent_variables: 不确定的潜在变量集合
            uncertain_latent_variable_reassess: 重新审视后的不确定的潜在变量集合
        """
        Print("-------A2 - Task6: 潜在变量再生成-------", 'blue')
        info_prompt = '''
            - 智能体A3根据数据事实对根据世界观生成的潜在变量进行了审视并反馈了信息，现在你正在对世界观中的潜在变量进行再生成，你所了解的内容为：
                1. 你的需求目标是：{req}；
                2. 解析世界观所用的"碎片事实"：{fragmented_facts}；
                3. 经过A3判断后确定保留的潜在变量集合为：{certainty_latent_variables}；
                4. A3判断后认为需要重新生成的潜在变量集合为：{uncertain_latent_variables}；
                5. 潜在变量经过A3重新审视后的反馈为：{uncertain_latent_variable_reassess}；
                6. 根据真实数据集的反馈信息：{gt_feedback}；
            - 你的任务有两个：
                1. 根据'uncertain_latent_variable_reassess'中的提示，对'uncertain_latent_variables'相应的变量内容进行修改和完善；
                2. 根据用户需求和真实数据集的反馈信息'gt_feedback'重新解析"碎片事实"，生成新的潜在变量并添加到返回的结果中，当前任务也可以不生成新变量，且最多生成2个新变量，
                    注意不要生成'certainty_latent_variables'中已经存在的变量；
            - 你返回的结果需要符合 JSON 格式，具体字段如下：
                "regenerated_uncertain_indicators": 新生成的潜在变量列表，首先这是'uncertain_latent_variables'的一份完整的拷贝，
                对于任务1，你需要重新设计'uncertain_latent_variable_reassess'提到的每个变量，包含变量的定义、计算公式、数据源和时间窗口；
                对于任务2，你需要将新生成的变量添加到列表中，包含变量的名称、定义、计算公式、数据源和时间窗口，任务2新生成的变量不能是前面信息中提到的'3. 经过A3判断后确定保留的潜在变量集合'中存在的变量。
                列表中每个元素均为一个字典，字典描述如下:
                    "name": 变量名称，只有任务2中新生成的变量需要重新生成名称；
                    "description": 变量的唯一定义;
                    "calculation_formula": 变量的计算公式;
                    "data_source": 变量的数据来源;
                    "time_window": 变量的时间窗口;
        '''
        param_dict = {
            "req": req,
            "fragmented_facts": fragmented_facts,
            "certainty_latent_variables": certainty_latent_variables,
            "uncertain_latent_variables": uncertain_latent_variables,
            "uncertain_latent_variable_reassess": uncertain_latent_variable_reassess,
            "gt_feedback": gt_feedback
        }
        regenerated_indicators: List[dict] = []
        llm_response = await self.get_response(input_prompt=info_prompt,
                                               input_param_dict=param_dict,
                                               is_first_call=False)
        try:
            regenerated_indicators = llm_response['regenerated_uncertain_indicators']
        except Exception as e:
            Print(f"A2 - Latent Variable Regeneration Error: {e}", 'red')

        return regenerated_indicators

    async def dfs(self,
                  idx: int = 0,
                  links: List[dict] = None,
                  tmp_links: List[dict] = None,
                  determined_competing_relationship: dict = None,
                  to_be_saved_info: List[dict] = None):
        # 遍历所有可能的解释组合
        if idx >= len(links):
            rating_param = await self.rating_and_selection(tmp_links)
            if rating_param['rating'] > determined_competing_relationship['rating_param']['rating']:
                determined_competing_relationship['rating_param'] = rating_param
                determined_competing_relationship['links'] = tmp_links.copy()
            to_be_saved_info.append({
                "links": tmp_links.copy(),
                "rating_param": rating_param
            })
            return
        for explanation in links[idx]['explanations']:
            tmp_links.append({
                "source": links[idx]['source'],
                "target": links[idx]['target'],
                "explanation": explanation
            })
            await self.dfs(idx + 1, links, tmp_links, determined_competing_relationship, to_be_saved_info)
            tmp_links.pop()


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

    agent = ConflictMediationAgent()
    # Task1：语言统一
    original_latent_variables = get_by_line("../mapper/Output_A1/task2.jsonl")
    latent_variables = []
    behavior_patterns = []
    for var in original_latent_variables:
        latent_variables.append({
            "perspective": var['perspective'],
            "latent_variables": var['latent_variables'],
        })
        behavior_patterns.append({
            "perspective": var['perspective'],
            "behavior_patterns": var['behavior_patterns'],
        })
    unified_latent_variables = await agent.language_unification(req=req,
                                                                fragmented_facts=sample_facts,
                                                                latent_variables=latent_variables)
    # Task2：确定变量关联
    links = await agent.determine_variable_links(req=req,
                                                 behavior_patterns=behavior_patterns,
                                                 unified_latent_variables=unified_latent_variables)
    # Task3：维护竞争解释
    competing_relationship = await agent.maintain_competing_explanations(req=req,
                                                                         latent_variables=latent_variables,
                                                                         behavior_patterns=behavior_patterns,
                                                                         fragmented_facts=sample_facts,
                                                                         variable_links=links)
    # Task4：评分与选择最佳世界观
    determined_competing_relationship = {
        "rating_param": {
            "rating": 0.0,
            "fit": 0,
            "simplicity": 0,
            "explainability": 0
        },
        "links": []
    }
    to_be_saved_info = []
    await agent.dfs(0, competing_relationship, [], determined_competing_relationship, to_be_saved_info)
    save_by_line("../mapper/Output_A2/task4.jsonl", to_be_saved_info,
                 prompt="A2 - Rating of Competing Relationship")


if __name__ == "__main__":
    asyncio.run(run())
