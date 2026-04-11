# CAMO: An Agentic Framework for Automated Causal Discovery from Micro Behaviors to Macro Emergence in LLM Agent Simulations

[English](#english) | [简体中文](#简体中文)

<a id="english"></a>
## 📖 Introduction

CAMO (Causal discovery from Micro behaviors to Macro Emergence in LLM agent simulations) is an automated causal discovery framework for identifying causal mechanisms from micro-level agent behaviors to macro-level emergence in Large Language Model (LLM)-empowered agent simulations.

CAMO automatically recovers causal mechanisms that link micro-level agent behaviors and meso-level interaction structures to macro-level emergent outcomes by integrating unstructured textual priors, observational data, and simulator-internal counterfactual interventions, supporting both explanation and intervention.

## 📊 CAMO Overview

![CAMO Overview](docs/images/main.png)



## 🎯 Key Features

- **Automated Causal Discovery**: Automatically discovers micro-to-macro causal structures from LLM-driven multi-agent simulations
- **Multi-Agent Collaboration**: Employs multiple specialized agents working together to achieve worldview construction, conflict mediation, causal cartography, experiment design, and counterfactual verification
- **Fast-Slow Self-Evolution Loop**: Mitigates hallucinated priors and noisy interventions through a fast-slow loop mechanism, enabling reliable causal analysis
- **Local Causal Identification**: Focuses on a minimal but sufficient causal interface around the target emergent outcome, rather than a complete global causal graph
- **Interpretable Causal Chains**: Provides clear causal explanation paths from upstream micro/meso causes to target outcomes
- **Markov Boundary Recovery**: Recovers computable Markov boundary using IAMB-like algorithm
- **True Mutual Information Estimation**: Computes conditional mutual information using k-nearest neighbor based KSG estimator
- **Counterfactual Edge Orientation**: Uses counterfactual interventions to orient ambiguous causal edges

## 📁 Project Structure

```
CAMO/
├── method/                    # Core methodology module
│   ├── agents/               # Multi-agent system
│   │   ├── WorldviewAnalysisAgent.py          # A1: Worldview Analysis Agent
│   │   ├── ConflictMediationAgent.py          # A2: Conflict Mediation Agent
│   │   ├── CausalCartographAgent.py           # A3: Causal Cartography Agent
│   │   ├── ScriptCraftsman.py                 # A4: Script Craftsman Agent
│   │   ├── CounterfactualVerificationAgent.py # A5: Counterfactual Verification Agent
│   │   └── BaseLLMAgent.py                    # Base LLM Agent class
│   ├── config/               # Configuration files
│   │   ├── Setting.py        # System settings (LLM model configuration, etc.)
│   │   └── FilePaths.py      # File path configuration
│   ├── server/               # Server module
│   │   ├── main.py           # Main execution workflow
│   │   └── memoryServer.py   # Memory server
│   └── tools/                # Utility functions
│       ├── dataProcess.py         # Data processing
│       └── printWithColor.py      # Colored printing utility
├── README.md                # English README (default)
```

## 🏗️ System Architecture

CAMO employs a multi-agent collaborative architecture with five core agents:

### A1: WorldviewAnalysisAgent (Worldview Analysis Agent)
- **Responsibility**: Constructs structured, computable worldviews from fragmented facts
- **Functions**:
  - Identifies stakeholders and their resources, constraints, and goals
  - Extracts latent variables and behavior patterns
  - Builds multi-perspective worldview representations

### A2: ConflictMediationAgent (Conflict Mediation Agent)
- **Responsibility**: Unifies language representations across different perspectives and maintains competing explanations
- **Functions**:
  - Language unification
  - Variable link determination
  - Competing explanation maintenance
  - Scoring and selecting the best worldview

### A3: CausalCartographAgent (Causal Cartography Agent)
- **Responsibility**: Draws causal graphs guided by data constraints and worldviews
- **Functions**:
  - **Node adaptation**: Validates variable computability in data, evaluates conditional information gain
  - **Markov boundary recovery**: Recovers computable Markov boundary using IAMB-like algorithm
  - **Redundant variable pruning**: Removes variables conditionally independent of Y given other variables
  - **Causal structure generation**: Integrates worldview-driven and data-driven structures
  - **Identifiability analysis**: Evaluates causal edge identifiability
  - **Counterfactual edge orientation**: Uses counterfactual interventions to orient ambiguous edges
  - **Feedback iteration**: Optimizes causal graphs through multiple rounds of iteration
  - **Explanatory subgraph construction**: Builds E_Y = {Y} ∪ MB^H(Y) ∪ Conn_min(R => MB^H(Y))

### A4: ScriptCraftsman (Script Craftsman Agent)
- **Responsibility**: Designs experiment scripts and evaluates causal edge importance
- **Functions**:
  - Edge importance evaluation
  - Experiment priority sorting

### A5: CounterfactualVerificationAgent (Counterfactual Verification Agent)
- **Responsibility**: Designs counterfactual experiments and verifies causal graph reliability
- **Functions**:
  - Model credibility evaluation
  - Counterfactual experiment design
  - Causal edge verification
  - Causal graph refinement


## 🚀 Quick Start

### Requirements

- Python 3.8+
- Supported Large Language Model (via MCP or API access)
- Recommended dependencies:
  - `numpy`
  - `scipy`
  - `hyppo` (for conditional independence testing)

### Installation

```bash
# Clone the repository
git clone <repository-url>
cd CAMO

# Install dependencies
pip install numpy scipy hyppo
```

### Configuration

1. **Configure LLM Model**: Edit `method/config/Setting.py` to set the LLM model to use:
```python
LLM_MODEL_NAME = "your-model-name"
```

2. **Configure File Paths**: Edit `method/config/FilePaths.py` to set data file paths

3. **Prepare Input Data**:
   - Requirement description file (requirements)
   - Sample facts data (sample_facts)
   - Dataset column information (data_columns)
   - Data edge information (data_edges, optional)

### Running

```bash
# Run main workflow
python method/server/main.py
```

## 📊 Workflow

CAMO's execution follows these steps:

1. **A1 Phase**: Worldview Analysis
   - Extracts structured worldviews from fragmented facts
   - Identifies latent variables and behavior patterns

2. **A2-A3 Fast-Slow Loop**: Variable Adaptation Iteration
   - **Fast Mode**: Rapidly updates causal structure
   - **Slow Mode**: Performs deep worldview reconstruction when evidence contradictions are detected
   - A3 performs node adaptation, evaluates conditional information gain, identifies uncertain variables
   - A2 reassesses and regenerates uncertain variables
   - Loop continues until uncertain variable ratio falls below threshold

3. **A2 Phase**: Worldview Refinement
   - Determines variable links
   - Maintains competing explanations
   - Selects best worldview

4. **A3 Phase**: Causal Graph Construction
   - Generates candidate causal structures
   - Performs identifiability analysis
   - **Uses counterfactual interventions to orient ambiguous edges**
   - Feedback iteration for optimization

5. **A4 Phase**: Experiment Design
   - Evaluates edge importance
   - Sorts experiment priorities

6. **A5 Phase**: Counterfactual Verification
   - Designs counterfactual experiments
   - Verifies causal edges
   - Refines causal graph

## 🔬 Core Algorithms

### Markov Boundary Recovery
Uses IAMB-like greedy algorithm:
- **Growth Phase**: Gradually adds variables most relevant to Y (given current MB)
- **Shrinkage Phase**: Removes variables conditionally independent of Y given other MB variables

### Conditional Mutual Information Estimation
Uses k-nearest neighbor based KSG estimator (Kraskov-Stögbauer-Grassberger):
- Estimates mutual information I(X; Y)
- Estimates conditional mutual information I(X; Y | Z)
- Provides both nats and bits units

### Fast-Slow Self-Evolution Loop
- **Evidence Consistency Checking**: Detects contradictions between worldview and data
- **Automatic Mode Switching**: Switches between Fast and Slow modes based on contradiction severity
- **Worldview Updates**: Performs deep reconstruction in Slow mode

### Counterfactual Edge Orientation
- Identifies ambiguous edges (non-identifiable or assumption-dependent)
- Designs bidirectional counterfactual experiments
- Determines edge direction based on experimental results

## 📝 Paper Information

**Title**: CAMO: An Agentic Framework for Automated Causal Discovery from Micro Behaviors to Macro Emergence in LLM Agent Simulations

**Abstract**: This paper presents CAMO, a framework for automatically discovering causal mechanisms from micro-level behaviors to macro-level emergence in LLM-driven agent simulations. CAMO recovers minimal but sufficient causal interfaces and explanation paths by integrating textual priors, observational data, and simulator-internal counterfactual interventions.

**Note**: This project is the code implementation of the paper "CAMO: An Agentic Framework for Automated Causal Discovery from Micro Behaviors to Macro Emergence in LLM Agent Simulations".

---

<a id="简体中文"></a>
## 📖 简介

CAMO (Causal discovery from Micro behaviors to Macro Emergence in LLM agent simulations) 是一个自动化的因果发现框架，用于在大语言模型 (LLM) 驱动的智能体模拟中，识别从微观智能体行为到宏观涌现机制的因果关系。

CAMO 通过整合非结构化的文本先验知识、观测数据以及模拟器内部的反事实干预，自动恢复连接微观智能体行为、中观交互结构到宏观涌现结果的因果机制，支持解释与干预。

## 📊 CAMO 概览

![CAMO Overview](docs/images/main.png)

## 🎯 主要特性

- **自动化因果发现**：自动从 LLM 驱动的多智能体模拟中发现微观到宏观的因果结构
- **多智能体协作**：采用多个专用智能体协同工作，实现世界观构建、冲突调解、因果制图、实验设计和反事实验证
- **快慢自进化循环**：通过快慢循环机制减轻先验幻觉和嘈杂干预的影响，实现可靠的因果分析
- **局部因果识别**：专注于目标涌现结果周围最小但足够的因果接口，而非完整的全局因果图
- **可解释的因果链**：提供从上游微观/中观原因到目标结果的清晰因果解释路径
- **马尔可夫边界恢复**：使用类似 IAMB 的算法恢复可计算的马尔可夫边界
- **真实互信息估计**：使用基于 k 最近邻的 KSG 估计器计算条件互信息
- **反事实边定向**：使用反事实干预来定向模糊的因果边

## 📁 项目结构

```
CAMO/
├── method/                    # 核心方法模块
│   ├── agents/               # 多智能体系统
│   │   ├── WorldviewAnalysisAgent.py          # A1: 世界观分析智能体
│   │   ├── ConflictMediationAgent.py          # A2: 冲突调解智能体
│   │   ├── CausalCartographAgent.py           # A3: 因果制图智能体
│   │   ├── ScriptCraftsman.py                 # A4: 脚本工匠智能体
│   │   ├── CounterfactualVerificationAgent.py # A5: 反事实验证智能体
│   │   └── BaseLLMAgent.py                    # 基础 LLM 智能体类
│   ├── config/               # 配置文件
│   │   ├── Setting.py        # 系统设置 (LLM 模型配置等)
│   │   └── FilePaths.py      # 文件路径配置
│   ├── server/               # 服务器模块
│   │   ├── main.py           # 主执行工作流
│   │   └── memoryServer.py   # 内存服务器
│   └── tools/                # 实用工具函数
│       ├── dataProcess.py         # 数据处理
│       └── printWithColor.py      # 彩色打印工具
├── README.md                # 英文 README (默认)
```

## 🏗️ 系统架构

CAMO 采用了包含五个核心智能体的多智能体协作架构：

### A1: WorldviewAnalysisAgent (世界观分析智能体)
- **职责**：从碎片化事实中构建结构化、可计算的世界观
- **功能**：
  - 识别利益相关者及其资源、约束和目标
  - 提取潜在变量和行为模式
  - 构建多视角的世界观表示

### A2: ConflictMediationAgent (冲突调解智能体)
- **职责**：统一不同视角的语言表示并维护竞争性解释
- **功能**：
  - 语言统一
  - 变量链接确定
  - 竞争性解释维​​护
  - 评分并选择最佳世界观

### A3: CausalCartographAgent (因果制图智能体)
- **职责**：在数据约束和世界观的指导下绘制因果图
- **功能**：
  - **节点自适应**：验证数据中的变量可计算性，评估条件信息增益
  - **马尔可夫边界恢复**：使用类似 IAMB 的算法恢复可计算的马尔可夫边界
  - **冗余变量修剪**：移除给定其他变量时与 Y 条件独立的变量
  - **因果结构生成**：整合数据驱动和世界观驱动的结构
  - **可识别性分析**：评估因果边的可识别性
  - **反事实边定向**：使用反事实干预来定义模糊边
  - **反馈迭代**：通过多轮迭代优化因果图
  - **解释子图构建**：构建 E_Y = {Y} ∪ MB^H(Y) ∪ Conn_min(R => MB^H(Y))

### A4: ScriptCraftsman (脚本工匠智能体)
- **职责**：设计实验脚本并评估因果边的重要性
- **功能**：
  - 边重要性评估
  - 实验优先级排序

### A5: CounterfactualVerificationAgent (反事实验证智能体)
- **职责**：设计反事实实验并验证因果图的可靠性
- **功能**：
  - 模型可信度评估
  - 反事实实验设计
  - 因果边验证
  - 因果图优化


## 🚀 快速开始

### 运行要求

- Python 3.8+
- 支持的大语言模型 (通过 MCP 或 API 访问)
- 推荐依赖：
  - `numpy`
  - `scipy`
  - `hyppo` (用于条件独立性测试)

### 安装

```bash
# 克隆仓库
git clone <repository-url>
cd CAMO

# 安装依赖
pip install numpy scipy hyppo
```

### 配置

1. **配置 LLM 模型**：编辑 `method/config/Setting.py` 设置要使用的 LLM 模型：
```python
LLM_MODEL_NAME = "your-model-name"
```

2. **配置文件路径**：编辑 `method/config/FilePaths.py` 设置数据文件路径

3. **准备输入数据**：
   - 需求描述文件 (requirements)
   - 样本事实数据 (sample_facts)
   - 数据集列信息 (data_columns)
   - 数据边信息 (data_edges, 可选)

### 运行

```bash
# 运行主工作流
python method/server/main.py
```

## 📊 工作流

CAMO 的执行遵循以下步骤：

1. **A1 阶段**：世界观分析
   - 从碎片化事实中提取结构化的世界观
   - 识别潜在变量和行为模式

2. **A2-A3 快慢循环**：变量适应迭代
   - **快速模式**：快速更新因果结构
   - **慢速模式**：当检测到证据矛盾时，执行深度世界观重构
   - A3 执行节点适应，评估条件信息增益，识别不确定变量
   - A2 重新评估并重新生成不确定变量
   - 循环继续直到不确定变量比例低于阈值

3. **A2 阶段**：世界观优化
   - 确定变量链接
   - 维护竞争性解释
   - 选择最佳世界观

4. **A3 阶段**：因果图构建
   - 生成候选因果结构
   - 执行可识别性分析
   - **使用反事实干预来定向模糊边**
   - 通过反馈迭代进行优化

5. **A4 阶段**：实验设计
   - 评估边重要性
   - 排序实验优先级

6. **A5 阶段**：反事实验证
   - 设计反事实实验
   - 验证因果边
   - 优化因果图

## 🔬 核心算法

### 马尔可夫边界恢复
使用类似 IAMB 的贪心算法：
- **增长阶段**：逐渐添加与 Y 最相关的变量（给定当前 MB）
- **缩减阶段**：移除在给定其他 MB 变量时与 Y 条件独立的变量

### 条件互信息估计
使用基于 k 最近邻的 KSG 估计器 (Kraskov-Stögbauer-Grassberger)：
- 估计互信息 I(X; Y)
- 估计条件互信息 I(X; Y | Z)
- 提供 nats 和 bits 两种单位

### 快慢自进化循环
- **证据一致性检查**：检测世界观和数据之间的矛盾
- **自动模式切换**：根据矛盾程度自动在快速和慢速模式之间切换
- **世界观更新**：在慢速模式下进行深度重构

### 反事实边定向
- 识别模糊的边（不可识别的或依赖假设的边）
- 设计双向反事实实验
- 根据实验结果确定边的方向

## 📝 论文信息

**标题**: CAMO: An Agentic Framework for Automated Causal Discovery from Micro Behaviors to Macro Emergence in LLM Agent Simulations

**摘要**: 本文提出了 CAMO，这是一个在大语言模型驱动的智能体模拟中，自动发现从微观行为到宏观涌现的因果机制的框架。CAMO 通过整合文本先验、观测数据以及模拟器内部的反事实干预，恢复了局部最小且充足的因果接口和解释路径。

**注意**: 该项目是论文 "CAMO: An Agentic Framework for Automated Causal Discovery from Micro Behaviors to Macro Emergence in LLM Agent Simulations" 的代码实现。
