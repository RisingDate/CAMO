# CAMO: An Agentic Framework for Automated Causal Discovery from Micro Behaviors to Macro Emergence in LLM Agent Simulations

[English](README.md) | [简体中文](README_zh.md)

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
