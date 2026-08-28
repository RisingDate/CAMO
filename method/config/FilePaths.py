import os

# Base directory of the project (your_project_path/AgentFlow)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Mapper directory (your_project_path/AgentFlow\method\mapper)
MAPPER_DIR = os.path.join(BASE_DIR, 'method', 'mapper')

REQUIREMENTS = os.path.join(MAPPER_DIR, 'Requirement.json')
DATA_COLUMNS = os.path.join(MAPPER_DIR, 'Baseline_mt', 'baseline_nodes.json')
ORIGINAL_LATENT_VARIABLES = os.path.join(MAPPER_DIR, 'Output_A1', 'task2.jsonl')
DATA_EDGES = os.path.join(MAPPER_DIR, 'Baseline_mt', 'baseline_edges.json')
NODE_ADAPTION_REs = os.path.join(MAPPER_DIR, 'Output_A3', 'task1.jsonl')

# Output paths
OUTPUT_A2_TASK1 = os.path.join(MAPPER_DIR, 'Output_A2', 'task1.jsonl')
OUTPUT_A3_TASK1_SET = os.path.join(MAPPER_DIR, 'Output_A3', 'task1_set.jsonl')
OUTPUT_A3_TASK1_CERTAIN = os.path.join(MAPPER_DIR, 'Output_A3', 'task1_certain.jsonl')
OUTPUT_A2_TASK5 = os.path.join(MAPPER_DIR, 'Output_A2', 'task5.jsonl')
OUTPUT_A2_TASK6 = os.path.join(MAPPER_DIR, 'Output_A2', 'task6.jsonl')
OUTPUT_A2_TASK4 = os.path.join(MAPPER_DIR, 'Output_A2', 'task4.jsonl')
