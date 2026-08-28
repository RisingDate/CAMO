"""
运行主函数
"""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

import asyncio
import json
from copy import deepcopy
from dataclasses import is_dataclass

from method.agents.CausalCartographAgent import CausalCartographAgent
from method.agents.ConflictMediationAgent import ConflictMediationAgent
from method.agents.ScriptCraftsman import ScriptCraftsman
from method.agents.WorldviewAnalysisAgent import WorldviewAnalysisAgent
from method.agents.CounterfactualVerificationAgent import CounterfactualVerificationAgent
from method.tools.printWithColor import Print
import method.config.FilePaths as fp


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

async def main(begin_step=1):
    # 数据初始化
    requirement = get_dict(fp.REQUIREMENTS)
    req = requirement.get('req', 'Mock Requirement')
    sample_facts = requirement.get('sample_facts', [])
    dataset_column = get_dict(file_path=fp.DATA_COLUMNS)

    # Agent初始化  A1: 世界观分析; A2: 冲突调解; A3: 因果制图; A4: 剧本工匠; A5: 反事实验证
    A1 = WorldviewAnalysisAgent()
    A2 = ConflictMediationAgent()
    A3 = CausalCartographAgent()
    A4 = ScriptCraftsman()
    A5 = CounterfactualVerificationAgent()

    # ---------------  A1  ---------------
    # A1 完整执行，解析世界观
    await A1.run_protocol(req=req, fragmented_facts=sample_facts)

    # ---------------  A2  ---------------
    # A2 - Task1：语言统一
    original_latent_variables = get_by_line(fp.ORIGINAL_LATENT_VARIABLES)
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
    unified_latent_variables = await A2.language_unification(req=req,
                                                             fragmented_facts=sample_facts,
                                                             latent_variables=latent_variables)
    # A2-A3 小循环（A2-Task1, A3-Task1 <--> A2-Task5, Task6）
    cycle_cnt = 0
    certainty_variables_names = []
    A2_reassessed_variables_list = []
    A2_regenerated_variables_list = []
    A3_node_adaption_list = []
    A3_certainty_variables_list = []
    while cycle_cnt < 50:
        cycle_cnt += 1
        Print(f'-------第 {cycle_cnt} 次 A2-A3 循环-------', 'yellow')
        # A3 - Task1: 节点适配
        A3_used_latent_variable = []
        for line in unified_latent_variables:
            A3_used_latent_variable.append({
                'name': line['name'],
                'description': line['description']
            })
        node_adaption_res = await A3.node_adaption(req=req,
                                                   data_columns=dataset_column,
                                                   latent_variable=A3_used_latent_variable,
                                                   certain_variables_names=certainty_variables_names)
        A3_node_adaption_list.append(deepcopy(node_adaption_res))
        uncertain_variables = [v for v in node_adaption_res if v.get('flag') == 'uncertain']
        certainty_variables_names = [v['name'] for v in node_adaption_res if v.get('flag') != 'uncertain']
        print(f'确定保存的变量名称: {certainty_variables_names}')

        certainty_latent_variables = [v for v in unified_latent_variables if v['name'] in certainty_variables_names]
        uncertain_latent_variables = [v for v in unified_latent_variables if v['name'] not in certainty_variables_names]
        A3_certainty_variables_list.append(deepcopy(certainty_latent_variables))
        # 结束条件：不确定变量 < 15%
        if len(uncertain_variables) / len(node_adaption_res) < 0.15:
            Print('不确定变量 < 15%，结束 A2-A3 循环', 'green')
            break
        feedback_for_A2 = ""
        # A3 - Task1.5: 根据数据集生成给A2的反馈信息
        feedback_for_A2 = await A3.node_adaption_feedback(req=req,
                                                          data_columns=dataset_column,
                                                          certainty_variables=certainty_latent_variables)
        print(f'A3 反馈给 A2 的信息：{feedback_for_A2}')

        # A2 - Task5: 不确定变量再评估
        A2_uncertain_variable_reassess = await A2.reassess_uncertain_variables(req=req,
                                                                               fragmented_facts=sample_facts,
                                                                               uncertain_latent_variables=uncertain_latent_variables,
                                                                               uncertain_variables=uncertain_variables,
                                                                               gt_feedback=feedback_for_A2)

        A2_reassessed_variables_list.append(deepcopy(A2_uncertain_variable_reassess))
        # 删除统一化后的潜在变量中被移除的变量
        removed_var_names = []
        for var in A2_uncertain_variable_reassess:
            if not var['is_important']:
                removed_var_names.append(var['name'])
        uncertain_latent_variables = [var for var in uncertain_latent_variables if var['name'] not in removed_var_names]
        A2_uncertain_variable_reassess = [var for var in A2_uncertain_variable_reassess if
                                          var['name'] not in removed_var_names]

        #  A2 - Task6: 变量重新生成
        regenerated_uncertain_latent_variables = await A2.uncertain_latent_variables_regeneration(req=req,
                                                                                                  fragmented_facts=sample_facts,
                                                                                                  certainty_latent_variables=certainty_latent_variables,
                                                                                                  uncertain_latent_variables=uncertain_latent_variables,
                                                                                                  uncertain_latent_variable_reassess=A2_uncertain_variable_reassess,
                                                                                                  gt_feedback=feedback_for_A2)
        A2_regenerated_variables_list.append(deepcopy(regenerated_uncertain_latent_variables))
        # 将重新生成的变量加入统一化后的潜在变量中
        unified_latent_variables = deepcopy(regenerated_uncertain_latent_variables + certainty_latent_variables)
        print(f'重新生成后潜在变量数量：{len(unified_latent_variables)}')
        tmp_names = []
        for var in unified_latent_variables:
            tmp_names.append(var['name'])
        print(f"重新生成后潜在变量名称：{tmp_names}")
    save_by_line(file_path=fp.OUTPUT_A3_TASK1_SET, data_list=A3_node_adaption_list,
                 prompt='A3 - Node Adaption List')
    save_by_line(file_path=fp.OUTPUT_A3_TASK1_CERTAIN, data_list=A3_certainty_variables_list,
                 prompt='A3 - Node Adaption Certainty List')
    save_by_line(file_path=fp.OUTPUT_A2_TASK5, data_list=A2_reassessed_variables_list,
                 prompt='A2 - Reassessed Variables')
    save_by_line(file_path=fp.OUTPUT_A2_TASK6, data_list=A2_regenerated_variables_list,
                 prompt='A2 - Variables Regenerated')

    # A2 - Task2：确定变量关联
    links = await A2.determine_variable_links(req=req,
                                              behavior_patterns=behavior_patterns,
                                              unified_latent_variables=unified_latent_variables)
    # A2 - Task3：维护竞争解释
    dfs_cnt = 1e9
    cycle_cnt = 0
    competing_relationship = []
    while dfs_cnt > 64:
        cycle_cnt += 1
        extra_hint = ""
        if cycle_cnt > 20:
            extra_hint = "每个变量的竞争解释数量请控制在1个以内。"
        elif cycle_cnt > 10:
            extra_hint = "每个变量的竞争解释数量请控制在2个以内。"
        competing_relationship = await A2.maintain_competing_explanations(req=req,
                                                                          latent_variables=latent_variables,
                                                                          behavior_patterns=behavior_patterns,
                                                                          fragmented_facts=sample_facts,
                                                                          variable_links=links,
                                                                          extra_hint=extra_hint)
        # 获取并计算递归层数
        dfs_cnt = 1
        for link in competing_relationship:
            dfs_cnt *= len(link['explanations'])

    # A2 - Task4：评分与选择最佳世界观
    determined_competing_relationship = {
        "rating_param": {
            "rating": 0.0,
            "fit": 0,
            "simplicity": 0,
            "explainability": 0
        },
        "links": []
    }
    world_driven_structure = []
    await A2.dfs(0, competing_relationship, [], determined_competing_relationship, world_driven_structure)
    save_by_line(fp.OUTPUT_A2_TASK4, world_driven_structure,
                 prompt="A2 - Rating of Competing Relationship")

    # ---------------  A3  ---------------
    # A3 - Task2: 因果结构生成
    world_driven_node = unified_latent_variables
    world_driven_structure = determined_competing_relationship['links']
    # 获取 data-driven 结构（通常使用简单的因果算法获取根据数据列生成的因果图，这里暂时用已生成好的基线图替代演示）
    data_driven_node = dataset_column
    data_driven_structure = get_dict(fp.DATA_EDGES)
    node_adaption_res = get_by_line(fp.NODE_ADAPTION_REs)
    candidate_structure_res = await A3.candidate_structure(req=req,
                                                           world_driven_node=world_driven_node,
                                                           world_driven_structure=world_driven_structure,
                                                           data_driven_node=data_driven_node,
                                                           data_driven_structure=data_driven_structure,
                                                           node_adaption_res=node_adaption_res)
    # Task3: 可识别性
    edge_identifiability_res = await A3.edge_identifiability(req=req,
                                                             candidate_structure=candidate_structure_res)
    # Task4: 反馈迭代
    feed_back = await A3.feedback_iteration(req=req,
                                            candidate_structure=edge_identifiability_res,
                                            outcome_variable="涌现现象")
    # ---------------  A4  ---------------
    # A4 - Task1: 边重要性评估（评估A3 Task3 的输出）
    candidate_structure = edge_identifiability_res

    edge_importance_res = await A4.edge_importance(req=req,
                                                   candidate_structure=candidate_structure)

    # A4 - Task2: 实验优先级排序
    priority_res = A4.experiment_priority(edge_importance_res=edge_importance_res, beta=1.0)

    # ---------------  A5  ---------------
    # A5 - Task1: 模型可信度评价
    # Mock data for demonstration
    sim_output = {"metric_a": 10, "metric_b": 0.5}
    real_obs = {"metric_a": 12, "metric_b": 0.45}
    credibility_res = await A5.evaluate_model_credibility(sim_output, real_obs)
    credibility_score = credibility_res.get("credibility_score", 0.5)

    # A5 - Task2: 实验设计
    # Extract variables for demonstration (using first line for target)
    task1_data = original_latent_variables
    task2_data = original_latent_variables if original_latent_variables else [{}]
    experiment_design = await A5.design_counterfactual_experiments(task1_data, task2_data)

    # A5 - Task3: 因果边验证
    # Mock simulation result based on experiment design
    sim_results = {"exp_1": "result_1", "exp_2": "result_2"}
    task3_data = edge_identifiability_res
    verified_edges = await A5.verify_causal_edges(sim_results, task3_data, credibility_score)

    # A5 - Task4: 修正因果图
    refined_graph = await A5.refine_causal_graph(verified_edges)

if __name__ == '__main__':
    Print('-------实验运行-------', 'green')
    asyncio.run(main())
