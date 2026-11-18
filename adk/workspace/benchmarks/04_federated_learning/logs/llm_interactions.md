# Ślad Decyzji i Promptów LLM – [04_federated_learning] Optymalizacja Uczenia Sfederowanego w Warunkach Niejednorodności Danych: Adaptacyjny FedProx

- **Domena:** Distributed Systems & Federated Machine Learning
- **Dostawca LLM:** `OLLAMA` (Modele: LRM=`qwen3.6:35b`, SML=`qwen3.5:4b`)
- **Liczba zapytań LLM:** 1 (w tym zapytań sieciowych API: 1)
- **Łączny czas inferencji:** 69.94 s (69942.3 ms)

Dokument zawiera pełny zapis wszystkich zapytań skierowanych do modeli LLM w trakcie realizacji zadania benchmarkowego,
w tym dokładne prompty systemowe, przekazane dane (JSON payload), podjęte decyzje i surowe odpowiedzi modeli.

---

## 📋 Tabela Podsumowująca Podjęte Decyzje

| Krok | Agent | Warstwa Architektury | Model (Tier) | Czas | Podjęta Decyzja / Działanie |
|:---:|:---|:---|:---|:---:|:---|
| 1 | `task_planner` | Warstwa 1 (Planowanie / Gate HITL) | qwen3.6:35b (LRM) | 69942 ms | Plan: 15 zadan [T1, T2, T3, T4, T5, T6, T7, T8, T9, T10, T11, T12, T13, T14, T15], cel: 'Robustness Analysis of FedProx vs FedAvg Under Non-IID Data and Straggler Conditions' |

---

## 🔍 Szczegółowy Zapis Promptów i Odpowiedzi Krok po Kroku

### Krok 1: Agent `task_planner`

- **Warstwa:** Warstwa 1 (Planowanie / Gate HITL)
- **Dostawca / Model:** `ollama` / `qwen3.6:35b` (LRM)
- **Czas wykonania:** 69942.3 ms
- **Kluczowa decyzja:** **Plan: 15 zadan [T1, T2, T3, T4, T5, T6, T7, T8, T9, T10, T11, T12, T13, T14, T15], cel: 'Robustness Analysis of FedProx vs FedAvg Under Non-IID Data and Straggler Conditions'**

<details>
<summary><b>📥 Prompt wysłany do LLM (System Prompt + JSON Payload) — 16098 znaków [Kliknij, aby rozwinąć]</b></summary>

#### Instrukcja Systemowa Agenta:
```markdown
# ROLE: Task Planner — Academic & Engineering Planner (Layer 1 — `planning` Domain)

You are the master **Task Planner** (`task_planner`) in the **Artificial-Degree-Printer (Neuro-Symbolic Harness)**.
Your mission is to decompose academic degree thesis requirements (Inżynierska, Magisterska, Scientific Paper) and human prompts into an atomic, deterministic sequence of tasks executed by specialized Layer 2 (`building`) agents, along with the unified academic thesis blueprint (`academic_blueprint`).

You design the project yourself: its modules and file names, its parameters, its metrics and its experiment. Nothing in this prompt prescribes them. Names written as `<...>` below are placeholders, never values to copy.

---

## 1. ELASTIC TASK GRANULARITY & VERTICAL FEATURE SLICES
Do NOT use a rigid waterfall model (all code first, then all tests, then the thesis), and do NOT force a fixed number of tasks.
- **Elastic Task Count ($N$ tasks)**: Plan as many atomic tasks as the problem genuinely requires. Simple parts can be handled concisely; complex algorithms, several baselines or dense chapters can be decomposed into finer tasks (`T1..TN`).
- **Topological Ordering (code before its tests)**: a test task runs `pytest` as soon as it completes, so a module must be written before the task that tests it. A test that imports a module which does not exist yet fails immediately with `ModuleNotFoundError`.
- **Hierarchical Task Decomposition**:
  - Split a large module (environment, model, baseline, training loop, evaluation) into several small, single-purpose modules or sequential steps (`T2.1`, `T2.2` or `T2`, `T3`).
  - Keep each code task bounded to roughly 50–150 lines. A single task that has to generate a whole application causes truncation, escaping errors and lost context.
  - Every task has exactly one `target_node` and a clearly bounded responsibility.
- **Granular Subsection Decomposition**: academic prose is better when one task writes one subsection (~300–450 words). Split a chapter into subsection tasks when it has distinct facets; scale the number of subsections to the topic, not to a fixed count.
- **Complete Coverage**: the queue must cover configuration, implementation, tests, the experiment that produces results, and every planned chapter of `academic_blueprint.planned_chapters`.
- **Vertical Feature Slices (Przyrosty Funkcjonalne)** — code, tests and text progress together:
  - **Increment 1 — assumptions, literature, interfaces**: literature review (`background_researcher` / `discoverer_researcher`), chapters 1–2 (`seed_writer`). There is no skeleton task: before any task runs, the harness imports every module of your `interfaces` (section 4) as a stub (every function body becomes `raise NotImplementedError`) and returns the plan to you if a stub does not import or the interfaces do not fit together. The stubs are the shared interface the remaining tasks build on.
  - **Increment 2 — method, baseline, architecture**: filling in the skeleton's modules — the proposed method and the baseline (`seed_coder`), their unit tests written against the skeleton's signatures (`seed_tester`), chapters 3–4 (`seed_writer`).
  - **Increment 3 — experiment, results, conclusions**: the experiment module with its entrypoint and `plot_results.py` (`seed_coder`), chapters 5–6 (`seed_writer`).
  - Results files (`*.csv`) and figures are produced by running the entrypoint; they are never a task's `target_node`. A task that should produce them targets the module that writes them. `seed_tester` writes only test files.

---

## 2. 3-TIER RESEARCH ROUTING BY `thesis_type`
- **I stopień (`inzynierska` / `licencjacka`)**: **`background_researcher`** — foundational theoretical funnel.
- **II stopień (`magisterska`)**: **`background_researcher`** followed by **`discoverer_researcher`** — foundations, then recent work.
- **III stopień (`paper` / scientific article)**: **`discoverer_researcher`** — recent related work only.

---

## 3. HITL CHECKPOINTS, FILES & BLAST RADIUS
- **Gate 1 (`GATE_1_OUTLINE_APPROVAL`)**: thesis statement, objectives and task outline are confirmed before coding.
- **One file per task (`target_node`)**: a workspace-relative file path you choose (e.g. `<package>/<module>.py`, `tests/test_<module>.py`, `thesis.md`). Your `interfaces`, tasks and chapters become the project hypergraph: every later task gets its own interface and the interfaces of the modules it uses, nothing else. Prefer several small modules over one large file.
  - Harness contracts, not suggestions: the thesis document is `thesis.md`; test modules are `tests/test_<module>.py`; if the experiment produces figures, the harness runs `plot_results.py:generate_plots(output_dir)` after the experiment.
- **Experiment entrypoint & metrics — declared in the plan**: in `academic_blueprint` declare
  - `entrypoint`: `<path>.py:<function>`, called WITHOUT arguments (every setting lives in the configuration module);
  - `metrics`: the metric names the experiment will report, chosen for this research question;
  - the success criterion in `thesis_statement` / `baseline_comparison`.
  Declare them before any experiment runs; the thesis must report against exactly this declaration.
- **Blast Radius**: a change to code requires re-running its tests and the experiment, and updating the chapters that cite that code or its results.
- **Agent Assignment & Dynamic Specialization**:
  - Assign to active agents in `state/agent_registry.json` (`seed_coder`, `seed_tester`, `seed_writer`, `background_researcher`, `discoverer_researcher`, `sota_researcher`).
  - If the project needs expertise no registered agent has, declare `"missing_agent_specialization": "<specialization_name>"` at the top level of the JSON. Layer 4 (`evolution_architect`) creates the specialist before the queue runs, and tasks can then be assigned to `dyn_<specialization_name>`.

---

## 4. REQUIRED JSON OUTPUT SCHEMA
Return strictly a valid JSON object where **`tasks`** is the first, top-level array (`T1..TN`, as many tasks as the project needs, covering all increments and all planned chapters).

**Schema Guidelines**:
- Adapt the number of tasks and chapters to the actual research scope.
- Each task: `task_id`, `description`, `target_node`, `assigned_agent` (the orchestrator sets `status`). Write task descriptions in English; thesis titles and chapter titles stay in Polish, because they appear in the thesis.
- **`interfaces` (required)**: for every code module (not tests) a task targets, its public interface as Python source: imports, configuration constants with their values, classes and functions with full signatures (every parameter typed, `__init__` with all its parameters, return type) and a one-sentence docstring saying what is returned. Bodies may be `...`; the harness replaces every body with `raise NotImplementedError`. Design the interfaces together, so that they fit: the entrypoint calls only what the other modules define, every agent class has one interface, each concept has one name and one encoding (e.g. players, states, actions). Every module imports what its annotations use (`from typing import List` or `list[...]`). Constants hold plain values of their declared type (no `dataclasses.field` outside a dataclass). The entrypoint function takes **no required arguments**: the harness calls it without arguments, so it reads configuration from the configuration module. Public attributes that tests may read are declared as class annotations (`mean_: float`); anything not declared is private. For every public function and method that returns something, give 1–2 doctest examples in its docstring (`>>> f(...)` followed by the expected output): they specify the behaviour that the implementation and the tests must agree on. The harness runs every example on the stubs before any code exists: everything before the first call into a stub must already be valid, deterministic Python (no assignment into a tuple, no unseeded randomness); a call whose value you do not show is written `_ = obj.method(...)`, because a bare call prints its return value. Examples of different methods must agree (what `reset()` returns is what `step()` receives).
- **The experiment runs the plan**: put the configuration constants in their own module and the entrypoint in an experiment module. The entrypoint module imports, **at its top level**, the modules it runs (the proposed method, the baseline, the environment or data), directly or through other planned modules; the harness rejects a plan in which a planned module is never imported by the experiment (except `plot_results.py`, which the harness calls itself). The experiment never reimplements a planned module.
- **Plan critic**: after the harness checks, a critic reviews the whole plan (does the experiment answer the thesis, do the doctests specify correct behaviour, do tasks cover every module and chapter). Its blocking findings come back to you as `error_feedback`, together with your plan as `current_plan`; a plan still blocked after two corrections stops the run.
- **Chapter tasks name their chapter**: a `seed_writer` task says "Chapter N" with the index from `planned_chapters`.
- **Descriptions use the interface names**: a code or test task names the classes, methods and functions exactly as `interfaces` defines them. The harness checks this and returns the plan if a description names something `interfaces` does not define.
- `planned_chapters`: `index`, `title`, `focus` for every chapter.
- Every `<...>` is a placeholder for your own decision.

```json
{
  "tasks": [
    {
      "task_id": "T1",
      "description": "[Increment 1: Assumptions] Chapter 1: introduction, aim of the work and thesis statement in thesis.md",
      "target_node": "thesis.md",
      "assigned_agent": "seed_writer"
    },
    {
      "task_id": "T2",
      "description": "[Increment 1: Assumptions] Configuration module with the experiment parameters in <config_module>.py",
      "target_node": "<config_module>.py",
      "assigned_agent": "seed_coder"
    },
    {
      "task_id": "T3",
      "description": "[Increment 2: Method] Implement <Class> in <method_module>.py",
      "target_node": "<method_module>.py",
      "assigned_agent": "seed_coder"
    },
    {
      "task_id": "T4",
      "description": "[Increment 2: Method] Unit tests of <Class>.<method> from <method_module>.py in tests/test_<method_module>.py",
      "target_node": "tests/test_<method_module>.py",
      "assigned_agent": "seed_tester"
    }
  ],
  "interfaces": {
    "<config_module>.py": "\"\"\"<one sentence>\"\"\"

<PARAMETER>: <type> = <value>
",
    "<method_module>.py": "\"\"\"<one sentence>\"\"\"


class <Class>:
    \"\"\"<one sentence>\"\"\"

    def __init__(self, <arg>: <type>) -> None:
        \"\"\"<one sentence>\"\"\"

    def <method>(self, <arg>: <type>) -> <type>:
        \"\"\"<what it returns>\"\"\"
"
  },
  "thesis_type": "inzynierska | magisterska | paper",
  "template_name": "thesis_plodz | paper_ieee",
  "academic_blueprint": {
    "thesis_title": "<tytuł pracy>",
    "thesis_statement": "<teza i kryterium sukcesu>",
    "baseline_comparison": "<metoda odniesienia i sposób porównania>",
    "entrypoint": "<experiment_module>.py:<function>",
    "metrics": ["<metryka_1>", "<metryka_2>"],
    "planned_chapters": [
      {
        "index": 1,
        "title": "Rozdział 1: Wstęp, Cel i Teza Pracy",
        "focus": "Formalna definicja problemu, cel, teza i zakres pracy"
      },
      {
        "index": 2,
        "title": "Rozdział 2: Stan Badań i Przegląd Literatury",
        "focus": "Przegląd prac powiązanych i specyfikacja metody odniesienia"
      }
    ]
  }
}
```

---

## 5. REFLEXIVE PROMPT EVOLUTION & AGENT SPECIALIZATION
- **Correcting a plan (`current_plan` + `error_feedback`)**: you are correcting YOUR plan, not writing a new one. Read each problem, find its cause in `current_plan` at the place named in brackets, and change only that. Return a patch, not the plan: `interfaces` with the full new source of each module you change or add, `remove_interfaces` with the paths of modules to drop, `entrypoint` if it changes, `academic_blueprint` with only the fields that change, `tasks` (the whole list) only if the tasks change. Everything you do not return stays as it is: do not rename modules, classes or functions that no problem is about. If the feedback says your previous patch was not applied, `current_plan` is still the plan before it: fix the problems without causing the ones listed.
- **Reflection feedback without `current_plan`**: if the payload contains `reflection_feedback` or `error_feedback` but no `current_plan`, address it first (e.g. put the `"tasks"` array as the first key, with tasks for every increment) and return the whole plan.
- **Missing Domain Specialization**: never assign an unqualified agent; set `"missing_agent_specialization": "<specialization_name>"` so Layer 4 creates the specialist.

Do not output conversational text or markdown wrappers outside the JSON.
```

#### Przekazany Payload Danych (Input JSON):
```json
{
  "user_prompt": "[DOCUMENT FORMAT: Artykuł Naukowy IEEE Conference Paper | thesis_type=paper | template_name=paper_ieee (IEEEtran.cls)] Research question: does a proximal federated optimizer (FedProx-style) converge more robustly than FedAvg on non-IID Dirichlet-partitioned clients with straggler dropout? Ground the related work in contemporary federated optimization literature (2023-2026). Design the experiment yourself: choose the parameters, training or search budget, number of repetitions and seeds, the metrics you will report and the success criterion, and declare the metrics and the experiment entrypoint in the plan before running anything. Implement the solution as small, single-purpose modules with unit tests, produce every result by running the declared entrypoint, and write the thesis so that every reported number is a symbolic pointer to the code or to a results file.",
  "agent_registry": {
    "agents": {
      "seed_coder": {
        "domain": "building",
        "path": "agents/building/seed_coder.md",
        "specialization": "python_coding",
        "active": true
      },
      "seed_tester": {
        "domain": "building",
        "path": "agents/building/seed_tester.md",
        "specialization": "unit_testing",
        "active": true
      },
      "seed_writer": {
        "domain": "building",
        "path": "agents/building/seed_writer.md",
        "specialization": "academic_writing",
        "active": true
      },
      "sota_researcher": {
        "domain": "building",
        "path": "agents/building/sota_researcher.md",
        "specialization": "literature_review",
        "active": true
      },
      "background_researcher": {
        "domain": "building",
        "path": "agents/building/background_researcher.md",
        "specialization": "background_literature",
        "active": true
      },
      "discoverer_researcher": {
        "domain": "building",
        "path": "agents/building/discoverer_researcher.md",
        "specialization": "sota_discovery",
        "active": true
      }
    }
  },
  "include_docs": true,
  "missing_agent_specialization": null,
  "domain_context": {
    "domain": "Distributed Systems & Federated Machine Learning",
    "topic_canonical": null,
    "canonical_baselines": [],
    "standard_metrics": [],
    "open_research_gaps": [],
    "suggested_sections": [],
    "detected_thesis_type": "paper",
    "detected_template_name": "paper_ieee",
    "template_is_certain": true
  },
  "detected_template": {
    "thesis_type": "paper",
    "template_name": "paper_ieee",
    "is_certain": true,
    "question": null
  }
}
```

</details>

<details open>
<summary><b>📤 Odpowiedź zwrócona przez LLM (Decyzja / Wygenerowany JSON) [Kliknij, aby zwinąć]</b></summary>

```json
{
  "tasks": [
    {
      "task_id": "T1",
      "description": "[Increment 1: Literature] Discover recent related work (2023-2026) on FedProx vs FedAvg under non-IID and straggler conditions. Write the 'Related Work' section in paper.tex.",
      "target_node": "paper.tex",
      "assigned_agent": "sota_researcher"
    },
    {
      "task_id": "T2",
      "description": "[Increment 1: Assumptions] Configure experiment parameters (Dirichlet alpha, dropout rate, client count) in config.py.",
      "target_node": "config.py",
      "assigned_agent": "seed_coder"
    },
    {
      "task_id": "T3",
      "description": "[Increment 1: Assumptions] Implement the non-IID data partitioning logic (Dirichlet distribution) in datamodule.py.",
      "target_node": "datamodule.py",
      "assigned_agent": "seed_coder"
    },
    {
      "task_id": "T4",
      "description": "[Increment 2: Method] Implement the proposed FedProx-style optimizer class in optimizers/fedprox.py.",
      "target_node": "optimizers/fedprox.py",
      "assigned_agent": "seed_coder"
    },
    {
      "task_id": "T5",
      "description": "[Increment 2: Baseline] Implement the baseline FedAvg optimizer class in optimizers/fedavg.py.",
      "target_node": "optimizers/fedavg.py",
      "assigned_agent": "seed_coder"
    },
    {
      "task_id": "T6",
      "description": "[Increment 2: Method] Implement the Federated Training Loop (including straggler handling) in train_loop.py.",
      "target_node": "train_loop.py",
      "assigned_agent": "seed_coder"
    },
    {
      "task_id": "T7",
      "description": "[Increment 2: Baseline] Implement the baseline FedAvg logic wrapper in optimizers/fedavg_wrapper.py to align interfaces.",
      "target_node": "optimizers/fedavg_wrapper.py",
      "assigned_agent": "seed_coder"
    },
    {
      "task_id": "T8",
      "description": "[Increment 2: Tests] Unit tests for DataPartitioner in tests/test_datamodule.py.",
      "target_node": "tests/test_datamodule.py",
      "assigned_agent": "seed_tester"
    },
    {
      "task_id": "T9",
      "description": "[Increment 2: Tests] Unit tests for FedProx optimizer steps in tests/test_fedprox.py.",
      "target_node": "tests/test_fedprox.py",
      "assigned_agent": "seed_tester"
    },
    {
      "task_id": "T10",
      "description": "[Increment 2: Tests] Unit tests for FedAvg optimizer steps in tests/test_fedavg.py.",
      "target_node": "tests/test_fedavg.py",
      "assigned_agent": "seed_tester"
    },
    {
      "task_id": "T11",
      "description": "[Increment 3: Experiment] Implement the main entrypoint to run experiments and save results in experiment/run_experiment.py.",
      "target_node": "experiment/run_experiment.py",
      "assigned_agent": "seed_coder"
    },
    {
      "task_id": "T12",
      "description": "[Increment 3: Results] Implement plot_results.py to generate convergence plots and comparison bar charts.",
      "target_node": "experiment/plot_results.py",
      "assigned_agent": "seed_coder"
    },
    {
      "task_id": "T13",
      "description": "[Increment 3: Writing] Write Section III (Methodology) describing FedProx formulation and non-IID setup in paper.tex.",
      "target_node": "paper.tex",
      "assigned_agent": "seed_writer"
    },
    {
      "task_id": "T14",
      "description": "[Increment 3: Writing] Write Section IV (Experiments & Results) including analysis of robustness against stragglers in paper.tex.",
      "target_node": "paper.tex",
      "assigned_agent": "seed_writer"
    },
    {
      "task_id": "T15",
      "description": "[Increment 3: Writing] Write Section V (Conclusion) summarizing findings and future work in paper.tex.",
      "target_node": "paper.tex",
      "assigned_agent": "seed_writer"
    }
  ],
  "interfaces": {
    "config.py": "\"\"\"Configuration constants for the federated optimization experiment.\"\"\"\n\nN_CLIENTS: int = 100\nTOTAL_ROUNDS: int = 200\nLOCAL_EPOCHS: int = 5\nBATCH_SIZE: int = 32\nLEARNING_RATE: float = 0.01\nDROPOUT_PROBABILITY: float = 0.2\nDIRICHLET_ALPHA: float = 0.1\nMU_PARAM: float = 0.01\nSEED: int = 42\n",
    "datamodule.py": "\"\"\"Module for generating non-IID data partitions using Dirichlet distribution.\"\"\"\nimport torch\nfrom typing import List, Dict\n\nclass DataPartitioner:\n    \"\"\"Partitions dataset among clients according to Dirichlet distribution.\"\"\"\n\n    def __init__(self, n_clients: int, alpha: float) -> None:\n        \"\"\"Initialize partitioner.\n        \n        Args:\n            n_clients: Number of clients.\n            alpha: Dirichlet concentration parameter (lower = more skewed).\n        \"\"\"\n        pass\n\n    def split(self, dataset_labels: torch.Tensor) -> Dict[int, List[int]]:\n        \"\"\"Split labels into client-specific index lists.\n        \n        Args:\n            dataset_labels: Tensor of shape (N,) with class labels.\n            \n        Returns:\n            Dictionary mapping client_id to list of data indices.\n        \"\"\"\n        pass\n",
    "optimizers/fedprox.py": "\"\"\"Implementation of the FedProx optimizer algorithm.\"\"\"\nimport torch\nfrom typing import Dict\n\nclass FedProxOptimizer:\n    \"\"\"FedProx optimizer that minimizes local loss with proximal term.\"\"\"\n\n    def __init__(self, lr: float, mu: float) -> None:\n        \"\"\"Initialize FedProx.\n        \n        Args:\n            lr: Learning rate.\n            mu: Proximal coefficient (mu).\n        \"\"\"\n        pass\n\n    def step(self, local_model_params: Dict[str, torch.Tensor], global_model_params: Dict[str, torch.Tensor]) -> Dict[str, torch.Tensor]:\n        \"\"\"Perform one optimization step with proximal regularization.\n        \n        Args:\n            local_model_params: Current local model state dict.\n            global_model_params: Current global model state dict.\n            \n        Returns:\n            Updated local model state dict after gradient descent.\n        \"\"\"\n        pass\n",
    "optimizers/fedavg.py": "\"\"\"Implementation of the standard FedAvg optimizer algorithm.\"\"\"\nimport torch\nfrom typing import Dict\n\nclass FedAvgOptimizer:\n    \"\"\"FedAvg optimizer performing standard local SGD.\"\"\"\n\n    def __init__(self, lr: float) -> None:\n        \"\"\"Initialize FedAvg.\n        \n        Args:\n            lr: Learning rate.\n        \"\"\"\n        pass\n\n    def step(self, local_model_params: Dict[str, torch.Tensor]) -> Dict[str, torch.Tensor]:\n        \"\"\"Perform one standard optimization step.\n        \n        Args:\n            local_model_params: Current local model state dict.\n            \n        Returns:\n            Updated local model state dict after gradient descent.\n        \"\"\"\n        pass\n",
    "optimizers/fedavg_wrapper.py": "\"\"\"Wrapper to align FedAvg with FedProx interface for comparison.\"\"\"\nimport torch\nfrom typing import Dict, Tuple\n\ndef init_fedavg(lr: float) -> 'FedAvgOptimizer':\n    \"\"\"Initialize FedAvg optimizer.\n    \n    Args:\n        lr: Learning rate.\n        \n    Returns:\n        Initialized FedAvgOptimizer instance.\n    \"\"\"\n    pass\n",
    "train_loop.py": "\"\"\"Core federated training loop with straggler handling.\"\"\"\nimport torch\nfrom typing import Dict, List, Any\nfrom optimizers.fedprox import FedProxOptimizer\nfrom optimizers.fedavg import FedAvgOptimizer\n\ndef run_federated_training(\n    n_clients: int,\n    total_rounds: int,\n    local_epochs: int,\n    batch_size: int,\n    lr: float,\n    dropout_prob: float,\n    data_partitioner: 'DataPartitioner',\n    optimizer_class: Any\n) -> Dict[str, List[float]]:\n    \"\"\"Execute the full federated training loop.\n    \n    Args:\n        n_clients: Total number of clients.\n        total_rounds: Number of communication rounds.\n        local_epochs: Local training epochs per round.\n        batch_size: Batch size for local SGD.\n        lr: Learning rate.\n        dropout_prob: Probability of a client dropping out (straggler).\n        data_partitioner: Pre-configured DataPartitioner instance.\n        optimizer_class: Class constructor for the optimizer (FedProx or FedAvg).\n        \n    Returns:\n        Dictionary containing 'train_loss' and 'test_acc' histories.\n    \"\"\"\n    pass\n",
    "experiment/run_experiment.py": "\"\"\"Entrypoint to execute the experiment and save results.\"\"\"\nimport torch\nimport pandas as pd\nfrom config import *\nfrom datamodule import DataPartitioner\nfrom train_loop import run_federated_training\nfrom optimizers.fedprox import FedProxOptimizer\nfrom optimizers.fedavg_wrapper import init_fedavg\n\ndef execute_experiment() -> pd.DataFrame:\n    \"\"\"Run experiments for both FedProx and FedAvg and return aggregated results.\n    \n    Returns:\n        DataFrame with columns: 'method', 'round', 'metric_name', 'value'.\n    \"\"\"\n    pass\n",
    "experiment/plot_results.py": "\"\"\"Script to generate visualizations from experiment results.\"\"\"\nimport pandas as pd\nimport matplotlib.pyplot as plt\n\ndef generate_plots(df: pd.DataFrame, output_dir: str) -> None:\n    \"\"\"Generate convergence plots and comparison charts.\n    \n    Args:\n        df: DataFrame containing experimental results.\n        output_dir: Directory to save generated figures.\n    \"\"\"\n    pass\n"
  },
  "thesis_type": "paper",
  "template_name": "paper_ieee",
  "academic_blueprint": {
    "thesis_title": "Robustness Analysis of FedProx vs FedAvg Under Non-IID Data and Straggler Conditions",
    "thesis_statement": "FedProx converges more robustly than FedAvg in non-IID settings with significant client dropout, maintaining higher final accuracy and lower variance.",
    "baseline_comparison": "Standard FedAvg (Konečný et al., 2016) vs. Proposed FedProx (Li et al., 2020). Comparison based on final test accuracy and convergence stability (variance across seeds).",
    "entrypoint": "experiment/run_experiment.py:execute_experiment",
    "metrics": [
      "final_test_accuracy",
      "convergence_variance",
      "communication_rounds_to_target"
    ],
    "planned_chapters": [
      {
        "index": 1,
        "title": "I. Introduction",
        "focus": "Problem statement: non-IID data and stragglers in FL; thesis statement and contributions."
      },
      {
        "index": 2,
        "title": "II. Related Work",
        "focus": "Review of FedAvg limitations and recent proximal methods (2023-2026)."
      },
      {
        "index": 3,
        "title": "III. Methodology",
        "focus": "Formulation of FedProx; non-IID Dirichlet partitioning; straggler dropout model."
      },
      {
        "index": 4,
        "title": "IV. Experiments and Results",
        "focus": "Experimental setup; accuracy convergence plots; statistical significance analysis."
      },
      {
        "index": 5,
        "title": "V. Conclusion",
        "focus": "Summary of findings; implications for robust FL deployment."
      }
    ]
  }
}
```

</details>

---
