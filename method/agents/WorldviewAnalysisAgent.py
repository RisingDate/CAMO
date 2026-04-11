"""
    A1 的职责，是从“碎片事实”出发，给系统提供一张结构化、可计算的世界画像。
    这一过程遵循一个显式的“世界观构建协议”，核心包含以下四步。

"""

import asyncio
import json
from dataclasses import dataclass, field, asdict, is_dataclass
from itertools import combinations
from typing import Any, Dict, List

from method.agents.BaseLLMAgent import BaseLLMAgent
from method.tools.printWithColor import Print
from method.config.Setting import LLM_MODEL_NAME


@dataclass
class StakeholderProfile:
    """
        结构化描述利益主体画像
        name: 利益主体名称
        resources: 资源列表
        constraints: 约束列表
        goals: 目标列表
    """

    name: str
    resources: List[str] = field(default_factory=list)
    constraints: List[str] = field(default_factory=list)
    goals: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class BehaviorPattern:
    """
        行为模式与潜在变量：描述“如果-那么”式行为模式
        if_cause: 条件描述
        then_clause: 结果描述
        drivers: 行为背后的驱动因素
        tag: 提取行为模式的基本规则（出现在多个独立来源 or 在多个案例中反复出现）
    """

    if_clause: str
    then_clause: str
    drivers: List[str] = field(default_factory=list)
    tag: str = "multi_sources"

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class LatentVariable:
    """
        潜在机制变量及其标签
        name: 潜在变量名称
        description: 变量描述
        label: 变量标签（directly observed/inferred/severely underspecified）
    """

    name: str
    description: str
    label: str = "directly observed"

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class ScaleStructure:
    """
        多尺度结构假设与数据映射
        包含：微观中观和宏观三个尺度，每个尺度包含以下字段
            structural_assumption: 结构假设（如网络拓扑类型、匹配规则）
            mapping: 与数据字段的映射关系（哪些指标对应这些结构要素）
    """

    micro: Dict[str, Any] = field(default_factory=lambda: {
        "structural_assumption": "",
        "mapping": []
    })
    meso: Dict[str, Any] = field(default_factory=lambda: {
        "structural_assumption": "",
        "mapping": []
    })
    macro: Dict[str, Any] = field(default_factory=lambda: {
        "structural_assumption": "",
        "mapping": []
    })

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class ConsistencyScore:
    """世界观一致性与稳定性报告"""
    source: str
    target: str
    distance_score: float

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class WorldviewAnalysisAgent(BaseLLMAgent):
    """
        执行世界观构建协议的 A1 智能体
        包含四个阶段：
        1) 识别多利益主体及其资源-约束-目标；
        2) 提炼行为模式与潜在变量；
        3) 构建多尺度结构并映射数据字段；
        4) 计算世界观一致性与稳定性。
    """

    def __init__(self,
                 name: str = "WorldviewAnalysisAgent",
                 model_name: str = LLM_MODEL_NAME,
                 stability_threshold: float = 0.3,
                 mcp_session=None):
        super().__init__(agent_name=name,
                         has_chat_history=False,
                         llm_model_name=model_name,
                         json_format=True,
                         system_prompt='',
                         mcp_session=mcp_session)
        self.stability_threshold = stability_threshold
        self.system_prompt = '''
            你是一个构建世界观的智能体，你需要从“碎片事实”出发，给系统提供一张结构化、可计算的世界画像。这一过程遵循一个显式的“世界观构建协议”
        '''

    async def identify_stakeholders(self,
                                    req: str = "",
                                    fragmented_facts=None) -> List[StakeholderProfile]:
        """
            阶段1：识别多方主体及资源-约束-目标
            Input:
                req: 用户需求
                fragmented_facts: 碎片事实
            Output：
                利益主体列表，每项均为一个 StakeholderProfile 对象
        """
        Print("-------A1 - Task1: 识别多利益主体与资源–约束–目标-------", 'blue')
        info_prompt = '''
            - 你需要根据需求：{req}，提取“碎片事实”：{fragmented_facts}中的多利益主体。
            - 你抽取到的系统主体类似于如下：
                如用户、美团骑手、服务提供者、平台运营方、监管者、第三方合作方等。
            - 你需要为每类主体构建结构化“画像”，包括：
                资源：如资金、产能、技术、数据等；
                约束：如成本、法规、运营能力、技术边界；
                目标：如利润、增长、体验、稳定性、合规程度等。
            - 你的回复必须严格遵循 JSON 格式，具体字段如下：
                "stakeholders": 利益主体列表，每项均为一个dict，包含：
                    "name": 主体名称；
                    "resources": 资源列表（字符串列表）；
                    "constraints": 约束列表（字符串列表）；
                    "goals": 目标列表（字符串列表）；
        '''
        param_dict = {
            "req": req,
            "fragmented_facts": fragmented_facts
        }
        llm_response = await self.get_response(input_prompt=info_prompt,
                                               input_param_dict=param_dict,
                                               is_first_call=False)
        profiles: List[StakeholderProfile] = []
        try:
            for item in llm_response.get("stakeholders", []) if isinstance(llm_response, dict) else []:
                profiles.append(
                    StakeholderProfile(
                        name=item.get("name", "defaultName"),
                        resources=item.get("resources"),
                        constraints=item.get("constraints"),
                        goals=item.get("goals"),
                    )
                )
        except Exception as e:
            Print(f"A1 - Identify Stakeholders Error: {e}", 'red')

        Print(f"解析到的利益主体数量：{len(profiles)}", 'yellow')
        self._save_by_line(file_path="../mapper/Output_A1/task1.jsonl",
                           data_list=profiles,
                           prompt="A1 - Stakeholder Profiles")

        return profiles

    async def extract_behavior_and_latent_factors(self,
                                                  req: str = "",
                                                  profile: Dict = None,
                                                  fragmented_facts=None) -> Dict[str, List[Any]]:
        """
            阶段2：提炼行为模式 与 潜在变量
            req: 用户需求
            profile: 当前利益主体画像
            fragmented_facts: 碎片事实
        """
        # 提炼行为模式
        Print("-------A1 - Task2: 提炼行为模式与潜在变量-------", 'blue')
        Print(f"-----当前正在以 {profile['name']} 视角分析-----", 'yellow')
        info_prompt = '''
            - 你是一名负责从世界观中提炼'行为模式'的分析代理，请根据以下输入开展工作：
                你分析问题的视角描述: {profile}
                你的需求为: {req}
                碎片事实: {fragmented_facts} 
            - 你的任务是从提供的碎片事实中识别并提炼行为模式。行为模式必须符合：
                形式为'如果…那么…'或其等价表达，例如'等待时间过长'+'报酬偏低'导致'取消概率显著上升'。
                注意，你提取的行为模式必须满足“至少出现在多个独立来源”或“在多个案例中反复出现”
            - 你的回复必须严格遵循 JSON 格式，具体字段如下：
                "patterns": 行为模式列表，每项均为一个 dict，包含：
                    "if_clause": 条件描述；
                    "then_clause": 结果描述；
                    "drivers": 行为背后的驱动因素，'dirvers'是一个字符串列表；
                    "tag": 提取行为模式的基本规则，只能为'multi_sources'(出现在多个独立来源)或'multi_cases'(出现在多个案例中)
        '''
        param_dict = {
            "req": req,
            "profile": profile,
            "fragmented_facts": fragmented_facts
        }
        llm_response = await self.get_response(input_prompt=info_prompt,
                                               input_param_dict=param_dict,
                                               is_first_call=False)
        patterns: List[BehaviorPattern] = []
        for item in llm_response.get("patterns", []) if isinstance(llm_response, dict) else []:
            patterns.append(
                BehaviorPattern(
                    if_clause=item.get("if_clause", ""),
                    then_clause=item.get("then_clause", ""),
                    drivers=item.get("drivers"),
                    tag=item.get("tag", "")
                )
            )

        # 提炼潜在变量
        info_prompt = '''
            - 你是一名负责从行为模式中提炼'潜在变量'的分析代理，请根据以下输入开展工作：
                你分析问题的视角描述: {profile}
                你的需求目标为: {req}
                从世界观中解析出的行为模式为：{patterns}
                碎片事实: {fragmented_facts} 
            - 你的任务是需要根据行为模式和碎片事实，提取行为模式背后的动机和机制
            - 你的回复必须严格遵循 JSON 格式，具体字段如下：
                "latent_factors": 潜在变量列表，每项均为一个 dict，包含：
                    "name": 潜在变量名称；
                    "description": 变量描述；
                    "label": 按照信息来源对变量打上标签，标签必须从'directly observed', 'inferred', 'severely underspecified'中进行选择。
        '''
        param_dict = {
            "req": req,
            "profile": profile,
            "fragmented_facts": fragmented_facts,
            "patterns": [pattern.to_dict() for pattern in patterns],
        }
        llm_response = await self.get_response(input_prompt=info_prompt,
                                               input_param_dict=param_dict,
                                               is_first_call=False)
        latent_vars: List[LatentVariable] = []
        for latent in llm_response.get("latent_factors", []) if isinstance(llm_response, dict) else []:
            latent_vars.append(
                LatentVariable(
                    name=latent.get("name", ""),
                    description=latent.get("description", ""),
                    label=latent.get("label", "inferred"),
                )
            )

        res = {
            "perspective": profile['name'],
            "behavior_patterns": [pattern.to_dict() for pattern in patterns],
            "latent_variables": [latent_var.to_dict() for latent_var in latent_vars],
        }

        return res

    async def map_multiscale_structures(self,
                                        req: str = "",
                                        profile=None,
                                        fragmented_facts=None,
                                        latent_variables=None) -> Dict[str, Any]:
        """阶段3：构建多尺度结构并映射数据字段"""
        Print("-------A1 - Task3: 构建多尺度结构关系与宏观指标-------", 'blue')
        info_prompt = '''
            - 你正在'碎片事实'中分析世界观，你需要根据世界观中提取出的'因果关系'构建多尺度结构关系，请根据以下输入开展工作：
                你分析问题的视角描述: {profile}
                你的需求为: {req}
                碎片事实: {fragmented_facts}
                潜在变量: {latent_variables}
            - 多尺度结构关系包含微观、中观和宏观三个尺度，举例如下：
                微观层面：单个主体的互动机制与局部规则，例如订单撮合逻辑，骑手接单决策规则，平台的动态调价/补贴规则等；
                中观层面：由多次互动累积形成的结构，例如骑手配送路径网络，订单空间分布网络，供需失衡区的动态边界，信息传播网络等；
                宏观层面：系统整体状态、性能指标及其演化趋势，例如系统拥堵指数，订单完成率与准时率，系统稳定性、供需匹配稳定性，风险外部性等指标及其演化趋势。
            - 你的任务是分析每个层次的结构假设，并将其与潜在变量和宏观指标进行映射。
            - 你的回复必须严格遵循 JSON 格式，具体字段如下：
                "micro": 微观层面信息，这是一个字典；
                "meso": 中观层面信息，这是一个字典；
                "macro": 宏观层面信息，这是一个字典。
            - 每个尺度均包含以下字段：
                "structural_assumption": 结构假设（如网络拓扑类型、匹配规则）",
                "mapping": 与给出的潜在关系之间可能存在的映射关系（哪些潜在变量属于该层次），'mapping'是一个列表，里面存放的是潜在变量的name属性，每个潜在变量应该只属于一个层面。
        '''
        param_dict = {
            "profile": profile,
            "req": req,
            "fragmented_facts": fragmented_facts,
            "latent_variables": latent_variables
        }
        llm_response = await self.get_response(input_prompt=info_prompt,
                                               input_param_dict=param_dict,
                                               is_first_call=False)
        structure = ScaleStructure()
        try:
            structure.micro = llm_response.get('micro', {})
            structure.meso = llm_response.get('meso', {})
            structure.macro = llm_response.get('macro', {})
        except Exception as e:
            Print(f"WorldviewAnalysisAgent - Map Multiscale Structures Error: {e}", 'red')

        res = {
            "perspective": profile['name'],
            "micro": structure.micro,
            "meso": structure.meso,
            "macro": structure.macro,
        }
        return res

    async def score_consistency(self,
                                latent_variables: List,
                                threshold=0.5):
        """阶段4：计算世界观一致性与稳定性"""
        Print("-------A1 - Task4: 世界观一致性与稳定性度量-------", 'blue')
        consistency_score: List[ConsistencyScore] = []
        try:
            for a, b in combinations(latent_variables, 2):
                distance_score = await self._jaccard_distance(a['latent_variables'], b['latent_variables'])
                consistency_score.append(
                    ConsistencyScore(
                        source=a['perspective'],
                        target=b['perspective'],
                        distance_score=distance_score
                    )
                )
        except Exception as e:
            Print(f"A1 - Consistency Scoring Error: {e}", 'red')

        self._save_by_line(file_path="../mapper/Output_A1/task4.jsonl",
                           data_list=consistency_score,
                           prompt="A4 - Consistency Scores")
        return consistency_score

    async def run_protocol(self,
                           req="",
                           fragmented_facts=None):
        # 串联四个阶段，返回完整世界观结构

        worldview_list = []
        task2_outputs = []
        task3_outputs = []
        stakeholders_profiles = await self.identify_stakeholders(req=req, fragmented_facts=fragmented_facts)
        for profile in stakeholders_profiles:
            task2_output = await self.extract_behavior_and_latent_factors(req=req,
                                                                          profile=profile.to_dict(),
                                                                          fragmented_facts=fragmented_facts)
            task2_outputs.append(task2_output)

            task3_output = await self.map_multiscale_structures(req=req,
                                                                profile=profile.to_dict(),
                                                                fragmented_facts=fragmented_facts,
                                                                latent_variables=task2_output['latent_variables'])
            task3_outputs.append(task3_output)

        # 保存结果
        self._save_by_line(file_path="../mapper/Output_A1/task2.jsonl",
                           data_list=task2_outputs,
                           prompt="A1 - Behavior patterns and latent variables")
        self._save_by_line(file_path="../mapper/Output_A1/task3.jsonl",
                           data_list=task3_outputs,
                           prompt="A1 - Map Multiscale Structures")

        await self.score_consistency(task2_outputs)

    @staticmethod
    def _save_by_line(file_path, data_list, prompt=""):
        # 按行保存 JSONL 文件
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

    async def _jaccard_distance(self,
                                req: str = "",
                                a: List[str] = None,
                                b: List[str] = None) -> float:
        """计算 Jaccard 距离"""
        info_prompt = '''
            - 你正在分析的问题为：{req}。
            - 你的任务是计算两个集合之间的并集的大小和交集的大小
                你需要判断这两个集合中的元素的含义是否相同或相近，含义类似的元素应被视为相同元素。
            - 你的输出必须严格遵循 JSON 格式，具体字段如下：
                "intersection_size": 交集的大小（整数）；
                "union_size": 并集的大小（整数）；
        '''
        param_dict = {
            "req": req,
            "a": a,
            "b": b
        }
        llm_response = await self.get_response(input_prompt=info_prompt,
                                               input_param_dict=param_dict,
                                               is_first_call=False)
        try:
            intersection_size = llm_response.get("intersection_size", 0)
            union_size = llm_response.get("union_size", 1)
            if union_size == 0:
                return 0.0
            else:
                return 1 - intersection_size / union_size
        except Exception as e:
            Print(f"WorldviewAnalysisAgent - Jaccard Distance Calculation Error: {e}", 'red')
            return 0.0


async def run():
    # 用户需求
    req_file_path = "../mapper/Requirement.json"
    try:
        with open(req_file_path, 'r', encoding='utf-8') as f:
            req_data = json.load(f)
    except Exception as e:
        Print(f"Load requirement from {req_file_path} Error: {e}", 'red')
    req = req_data['req']
    # 碎片事实样本
    sample_facts = req_data['sample_facts']
    agent = WorldviewAnalysisAgent()
    await agent.run_protocol(req=req, fragmented_facts=sample_facts)


if __name__ == "__main__":
    asyncio.run(run())
