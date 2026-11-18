# Ślad Decyzji i Promptów LLM – [03_graph_pathfinding] Heurystyczna Optymalizacja Ścieżek na Siatkach Przestrzennych: Ważony Algorytm A* z Metryką Oktilową

- **Domena:** Graph Algorithms & Heuristic Search
- **Dostawca LLM:** `OLLAMA` (Modele: LRM=`qwen3.6:35b`, SML=`qwen3.5:4b`)
- **Liczba zapytań LLM:** 1 (w tym zapytań sieciowych API: 1)
- **Łączny czas inferencji:** 108.29 s (108294.7 ms)

Dokument zawiera pełny zapis wszystkich zapytań skierowanych do modeli LLM w trakcie realizacji zadania benchmarkowego,
w tym dokładne prompty systemowe, przekazane dane (JSON payload), podjęte decyzje i surowe odpowiedzi modeli.

---

## 📋 Tabela Podsumowująca Podjęte Decyzje

| Krok | Agent | Warstwa Architektury | Model (Tier) | Czas | Podjęta Decyzja / Działanie |
|:---:|:---|:---|:---|:---:|:---|
| 1 | `task_planner` | Warstwa 1 (Planowanie / Gate HITL) | qwen3.6:35b (LRM) | 108295 ms | Plan: 12 zadan [T1, T2, T3, T4, T5, T6, T7, T8, T9, T10, T11, T12], cel: 'Efektywność przeszukiwania ważonego A* z heurystyką oktilową na siatkach z przeszkodami w porównaniu do algorytmu Dijkstry' |

---

## 🔍 Szczegółowy Zapis Promptów i Odpowiedzi Krok po Kroku

### Krok 1: Agent `task_planner`

- **Warstwa:** Warstwa 1 (Planowanie / Gate HITL)
- **Dostawca / Model:** `ollama` / `qwen3.6:35b` (LRM)
- **Czas wykonania:** 108294.7 ms
- **Kluczowa decyzja:** **Plan: 12 zadan [T1, T2, T3, T4, T5, T6, T7, T8, T9, T10, T11, T12], cel: 'Efektywność przeszukiwania ważonego A* z heurystyką oktilową na siatkach z przeszkodami w porównaniu do algorytmu Dijkstry'**

<details>
<summary><b>📥 Prompt wysłany do LLM (System Prompt + JSON Payload) — 16194 znaków [Kliknij, aby rozwinąć]</b></summary>

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
  "user_prompt": "[DOCUMENT FORMAT: Artykuł Naukowy IEEE Conference Paper | thesis_type=paper | template_name=paper_ieee (IEEEtran.cls)] The workspace already contains a graph pathfinding project with a baseline Dijkstra search; read it before changing anything and keep the baseline working. Research question: does a weighted A* pathfinding search with an admissible octile heuristic expand fewer nodes than the baseline on 8-connected obstacle grids, and at what cost in path optimality? Design the experiment yourself: choose the parameters, training or search budget, number of repetitions and seeds, the metrics you will report and the success criterion, and declare the metrics and the experiment entrypoint in the plan before running anything. Implement the solution as small, single-purpose modules with unit tests, produce every result by running the declared entrypoint, and write the thesis so that every reported number is a symbolic pointer to the code or to a results file.",
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
    "domain": "Graph Algorithms & Heuristic Search Optimization",
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
      "description": "[Increment 1: Assumptions] Chapter 1: Introduction and Thesis Statement in thesis.md",
      "target_node": "thesis.md",
      "assigned_agent": "seed_writer"
    },
    {
      "task_id": "T2",
      "description": "[Increment 1: Assumptions] Implement grid generation utilities (8-connected) in src/env/grid.py",
      "target_node": "src/env/grid.py",
      "assigned_agent": "seed_coder"
    },
    {
      "task_id": "T3",
      "description": "[Increment 2: Method] Implement Octile Heuristic and Weighted A* algorithm in src/search/wa_star.py",
      "target_node": "src/search/wa_star.py",
      "assigned_agent": "seed_coder"
    },
    {
      "task_id": "T4",
      "description": "[Increment 2: Method] Implement Dijkstra baseline in src/search/dijkstra.py (preserve existing working code)",
      "target_node": "src/search/dijkstra.py",
      "assigned_agent": "seed_coder"
    },
    {
      "task_id": "T5",
      "description": "[Increment 2: Method] Unit tests for Grid generation in tests/test_grid.py",
      "target_node": "tests/test_grid.py",
      "assigned_agent": "seed_tester"
    },
    {
      "task_id": "T6",
      "description": "[Increment 2: Method] Unit tests for Octile Heuristic in tests/test_heuristic.py",
      "target_node": "tests/test_heuristic.py",
      "assigned_agent": "seed_tester"
    },
    {
      "task_id": "T7",
      "description": "[Increment 2: Method] Unit tests for Weighted A* correctness and node expansion counting in tests/test_wa_star.py",
      "target_node": "tests/test_wa_star.py",
      "assigned_agent": "seed_tester"
    },
    {
      "task_id": "T8",
      "description": "[Increment 3: Experiment] Implement experiment runner and entrypoint in src/experiment/run_experiment.py",
      "target_node": "src/experiment/run_experiment.py",
      "assigned_agent": "seed_coder"
    },
    {
      "task_id": "T9",
      "description": "[Increment 3: Results] Plot results script (nodes expanded vs path optimality cost) in src/experiment/plot_results.py",
      "target_node": "src/experiment/plot_results.py",
      "assigned_agent": "seed_coder"
    },
    {
      "task_id": "T10",
      "description": "[Increment 3: Writing] Chapter 2: Literature Review (SOTA) in thesis.md",
      "target_node": "thesis.md",
      "assigned_agent": "sota_researcher"
    },
    {
      "task_id": "T11",
      "description": "[Increment 3: Writing] Chapter 3: Methodology and Implementation Details in thesis.md",
      "target_node": "thesis.md",
      "assigned_agent": "seed_writer"
    },
    {
      "task_id": "T12",
      "description": "[Increment 3: Writing] Chapter 4: Experimental Results and Discussion in thesis.md",
      "target_node": "thesis.md",
      "assigned_agent": "seed_writer"
    }
  ],
  "interfaces": {
    "src/env/grid.py": "\"\"\"Utilities for generating and manipulating 8-connected obstacle grids.\"\"\"\n\nfrom typing import List, Tuple\nimport random\n\nclass Grid:\n    \"\"\"Represents an 8-connected grid with obstacles.\n    \n    Attributes:\n        width (int): Grid width.\n        height (int): Grid height.\n        obstacles (set): Set of (x, y) tuples representing obstacle coordinates.\n    \"\"\"\n    width: int\n    height: int\n    obstacles: set\n\n    def __init__(self, width: int, height: int, density: float = 0.3, seed: int = None) -> None:\n        \"\"\"Initialize grid with random obstacles.\n        \n        Args:\n            width: Width of the grid.\n            height: Height of the grid.\n            density: Probability of a cell being an obstacle (0.0 to 1.0).\n            seed: Random seed for reproducibility.\n        \"\"\"\n        if seed is not None:\n            random.seed(seed)\n        self.width = width\n        self.height = height\n        self.obstacles = set()\n        for x in range(width):\n            for y in range(height):\n                if random.random() < density:\n                    self.obstacles.add((x, y))\n\n    def get_neighbors(self, pos: Tuple[int, int]) -> List[Tuple[int, int]]:\n        \"\"\"Return list of valid 8-connected neighbors within bounds and not in obstacles.\n        \n        Args:\n            pos: Current (x, y) position.\n            \n        Returns:\n            List of valid neighbor positions.\n            \n        Example:\n        >>> g = Grid(5, 5, density=0.0, seed=42)\n        >>> len(g.get_neighbors((2, 2)))\n        8\n        \"\"\"\n        neighbors = []\n        for dx in [-1, 0, 1]:\n            for dy in [-1, 0, 1]:\n                if dx == 0 and dy == 0:\n                    continue\n                nx, ny = pos[0] + dx, pos[1] + dy\n                if 0 <= nx < self.width and 0 <= ny < self.height:\n                    if (nx, ny) not in self.obstacles:\n                        neighbors.append((nx, ny))\n        return neighbors\n",
    "src/search/wa_star.py": "\"\"\"Weighted A* search implementation using octile heuristic.\"\"\"\n\nfrom typing import List, Tuple, Dict, Set, Optional\nimport heapq\n\n# Constants for Octile Heuristic\nDIAGONAL_COST = 1.4142135623730951\nCARDINAL_COST = 1.0\n\ndef octile_heuristic(start: Tuple[int, int], goal: Tuple[int, int]) -> float:\n    \"\"\"Calculate the admissible octile distance between two points.\n    \n    Args:\n        start: Starting (x, y) coordinate.\n        goal: Goal (x, y) coordinate.\n        \n    Returns:\n        Estimated cost to reach goal from start using 8-way moves.\n        \n    Example:\n    >>> octile_heuristic((0, 0), (3, 4))\n    7.0\n    \"\"\"\n    dx = abs(start[0] - goal[0])\n    dy = abs(start[1] - goal[1])\n    return min(dx, dy) * (DIAGONAL_COST - CARDINAL_COST) + max(dx, dy) * CARDINAL_COST\n\nclass WeightedAStar:\n    \"\"\"Implements weighted A* search with configurable weight and octile heuristic.\n    \n    Attributes:\n        w (float): Weight of the heuristic (w >= 1). Higher values prioritize speed over optimality.\n        nodes_expanded (int): Number of nodes popped from the priority queue during search.\n    \"\"\"\n    w: float\n    nodes_expanded: int\n\n    def __init__(self, weight: float = 2.0) -> None:\n        \"\"\"Initialize weighted A* with a specific heuristic weight.\n        \n        Args:\n            weight: The weight factor for the heuristic function (w > 1).\n        \"\"\"\n        if weight < 1.0:\n            raise ValueError(\"Weight must be >= 1.0\")\n        self.w = weight\n        self.nodes_expanded = 0\n\n    def search(self, grid, start: Tuple[int, int], goal: Tuple[int, int]) -> Optional[List[Tuple[int, int]]]:\n        \"\"\"Run weighted A* search on the provided grid.\n        \n        Args:\n            grid: Grid instance containing obstacles and dimensions.\n            start: Start position (x, y).\n            goal: Goal position (x, y).\n            \n        Returns:\n            List of coordinates representing the path from start to goal, or None if no path exists.\n        \"\"\"\n        self.nodes_expanded = 0\n        open_set = [(octile_heuristic(start, goal), 0, start, [])]\n        closed_set: Set[Tuple[int, int]] = set()\n        \n        while open_set:\n            _, g_score, current, path = heapq.heappop(open_set)\n            \n            if current == goal:\n                return path + [current]\n            \n            if current in closed_set:\n                continue\n            closed_set.add(current)\n            self.nodes_expanded += 1\n            \n            # Update path list for children to avoid deep copying at every step\n            current_path = path + [current]\n            \n            for neighbor in grid.get_neighbors(current):\n                if neighbor in closed_set:\n                    continue\n                    \n                tentative_g_score = g_score + (CARDINAL_COST if abs(neighbor[0] - current[0]) == 0 or abs(neighbor[1] - current[1]) == 0 else DIAGONAL_COST)\n                \n                # Weighted heuristic cost f(n) = g(n) + w * h(n)\n                f_score = tentative_g_score + self.w * octile_heuristic(neighbor, goal)\n                heapq.heappush(open_set, (f_score, tentative_g_score, neighbor, current_path))\n                \n        return None\n",
    "src/search/dijkstra.py": "\"\"\"Baseline Dijkstra search implementation.\"\"\"\n\nfrom typing import List, Tuple, Dict, Set, Optional\nimport heapq\n\nclass Dijkstra:\n    \"\"\"Implements standard Dijkstra's algorithm for shortest path on a grid.\n    \n    Attributes:\n        nodes_expanded (int): Number of nodes popped from the priority queue during search.\n    \"\"\"\n    nodes_expanded: int\n\n    def __init__(self) -> None:\n        \"\"\"Initialize Dijkstra instance.\"\"\"\n        self.nodes_expanded = 0\n\n    def search(self, grid, start: Tuple[int, int], goal: Tuple[int, int]) -> Optional[List[Tuple[int, int]]]:\n        \"\"\"Run Dijkstra search on the provided grid.\n        \n        Args:\n            grid: Grid instance containing obstacles and dimensions.\n            start: Start position (x, y).\n            goal: Goal position (x, y).\n            \n        Returns:\n            List of coordinates representing the shortest path, or None if no path exists.\n        \"\"\"\n        self.nodes_expanded = 0\n        open_set = [(0, start)]\n        closed_set: Set[Tuple[int, int]] = set()\n        parent_map: Dict[Tuple[int, int], Tuple[int, int]] = {}\n        dist_map: Dict[Tuple[int, int], float] = {start: 0.0}\n        \n        while open_set:\n            current_dist, current = heapq.heappop(open_set)\n            \n            if current == goal:\n                path = []\n                while current in parent_map:\n                    path.append(current)\n                    current = parent_map[current]\n                return [start] + path[::-1]\n            \n            if current in closed_set:\n                continue\n            closed_set.add(current)\n            self.nodes_expanded += 1\n            \n            for neighbor in grid.get_neighbors(current):\n                tentative_dist = current_dist + (1.0 if abs(neighbor[0] - current[0]) == 0 or abs(neighbor[1] - current[1]) == 0 else 1.4142135623730951)\n                \n                if neighbor not in dist_map or tentative_dist < dist_map[neighbor]:\n                    dist_map[neighbor] = tentative_dist\n                    parent_map[neighbor] = current\n                    heapq.heappush(open_set, (tentative_dist, neighbor))\n        return None\n",
    "src/experiment/run_experiment.py": "\"\"\"Experiment runner for comparing Dijkstra and Weighted A*.\"\"\"\n\nfrom typing import Dict, List, Any\nimport csv\nimport os\nimport random\n\nfrom src.env.grid import Grid\nfrom src.search.dijkstra import Dijkstra\nfrom src.search.wa_star import WeightedAStar\n\n# Experiment Parameters\nGRID_SIZES: List[int] = [10, 20, 50]\nOBSTACLE_DENSITIES: List[float] = [0.1, 0.3, 0.5]\nWEIGHTS: List[float] = [1.0, 1.5, 2.0, 5.0]\nREPETITIONS: int = 10\nSEED: int = 42\n\ndef calculate_path_length(path: List[Tuple[int, int]]) -> float:\n    \"\"\"Calculate the Euclidean-like path length for 8-connected moves.\n    \n    Args:\n        path: List of (x, y) coordinates.\n        \n    Returns:\n        Total cost of the path.\n    \"\"\"\n    if not path or len(path) < 2:\n        return 0.0\n    total = 0.0\n    for i in range(len(path) - 1):\n        dx = abs(path[i][0] - path[i+1][0])\n        dy = abs(path[i][1] - path[i+1][1])\n        if dx + dy == 2: # Diagonal\n            total += 1.4142135623730951\n        else:\n            total += 1.0\n    return total\n\ndef run_experiment() -> List[Dict[str, Any]]:\n    \"\"\"Run the full experiment comparing Dijkstra and Weighted A*.\n    \n    Returns:\n        List of result dictionaries containing grid size, density, weight, nodes expanded, path length, and optimality gap.\n    \"\"\"\n    results = []\n    random.seed(SEED)\n    \n    for size in GRID_SIZES:\n        for density in OBSTACLE_DENSITIES:\n            for w in WEIGHTS:\n                dijkstra_nodes_sum = 0\n                wa_nodes_sums = {w: 0.0 for w in WEIGHTS}\n                path_lengths = {}\n                optimal_path_length = None\n                valid_trials = 0\n                \n                for rep in range(REPETITIONS):\n                    # Ensure start and goal are free\n                    grid = Grid(size, size, density, seed=SEED + rep)\n                    start = (0, 0)\n                    goal = (size - 1, size - 1)\n                    \n                    while start in grid.obstacles:\n                        start = random.randint(0, size-1), random.randint(0, size-1)\n                    while goal in grid.obstacles:\n                        goal = random.randint(0, size-1), random.randint(0, size-1)\n                    \n                    # Run Dijkstra\n                    d_search = Dijkstra()\n                    path_d = d_search.search(grid, start, goal)\n                    \n                    if path_d is None:\n                        continue\n                    \n                    if optimal_path_length is None:\n                        optimal_path_length = calculate_path_length(path_d)\n                    \n                    dijkstra_nodes_sum += d_search.nodes_expanded\n                    \n                    # Run Weighted A* for all weights\n                    for w_curr in WEIGHTS:\n                        wa_search = WeightedAStar(weight=w_curr)\n                        path_wa = wa_search.search(grid, start, goal)\n                        \n                        if path_wa is None:\n                            continue\n                        \n                        wa_nodes_sums[w_curr] += wa_search.nodes_expanded\n                        path_lengths[w_curr] = calculate_path_length(path_wa)\n                    valid_trials += 1\n                \n                if valid_trials == 0:\n                    continue\n                    \n                # Calculate averages and optimality gap\n                avg_dijkstra_nodes = dijkstra_nodes_sum / valid_trials\n                \n                for w_curr in WEIGHTS:\n                    avg_wa_nodes = wa_nodes_sums[w_curr] / valid_trials\n                    avg_path_len = path_lengths[w_curr] / valid_trials\n                    \n                    # Optimality Gap: (PathWeighted - PathOptimal) / PathOptimal * 100\n                    gap = ((avg_path_len - optimal_path_length) / optimal_path_length) * 100.0 if optimal_path_length > 0 else 0.0\n                    \n                    results.append({\n                        \"grid_size\": size,\n                        \"density\": density,\n                        \"weight\": w_curr,\n                        \"avg_dijkstra_nodes\": avg_dijkstra_nodes,\n                        \"avg_wa_nodes\": avg_wa_nodes,\n                        \"path_expansion_reduction\": (1 - (avg_wa_nodes / avg_dijkstra_nodes)) * 100.0 if avg_dijkstra_nodes > 0 else 0.0,\n                        \"optimality_gap_percent\": gap\n                    })\n                    \n    # Save results to CSV for analysis and plotting\n    output_dir = \"results\"\n    os.makedirs(output_dir, exist_ok=True)\n    file_path = os.path.join(output_dir, \"experiment_results.csv\")\n    with open(file_path, 'w', newline='') as f:\n        if not results:\n            return results\n        writer = csv.DictWriter(f, fieldnames=results[0].keys())\n        writer.writeheader()\n        writer.writerows(results)\n        \n    return results\n"
  },
  "thesis_type": "paper",
  "template_name": "paper_ieee",
  "academic_blueprint": {
    "thesis_title": "Efektywność przeszukiwania ważonego A* z heurystyką oktilową na siatkach z przeszkodami w porównaniu do algorytmu Dijkstry",
    "thesis_statement": "Przeszukiwanie ważone A* z heurystyką oktilową redukuje liczbę rozszerzonych węzłów o min. 20% w stosunku do algorytmu Dijkstry na gęstych siatkach, przy dopuszczalnym wzroście kosztu ścieżki (optimality gap) poniżej 15% dla w < 3.0.",
    "baseline_comparison": "Porównanie z implementacją bazową algorytmu Dijkstry na identycznych siatkach 8-połączonych. Miernikiem wydajności jest liczba rozszerzonych węzłów (nodes expanded), a miernikiem jakości rozwiązania jest gap optymalności ścieżki.",
    "entrypoint": "src/experiment/run_experiment.py:run_experiment",
    "metrics": [
      "avg_dijkstra_nodes",
      "avg_wa_nodes",
      "path_expansion_reduction",
      "optimality_gap_percent"
    ],
    "planned_chapters": [
      {
        "index": 1,
        "title": "Rozdział 1: Wstęp i Cel Pracy",
        "focus": "Formalizacja problemu porównania złożoności obliczeniowej (liczba rozszerzeń węzłów) Dijkstry vs Weighted A* na siatkach z przeszkodami, cel pracy i teza."
      },
      {
        "index": 2,
        "title": "Rozdział 2: Przegląd Literatury",
        "focus": "Przegląd najnowszych osiągnięć (SOTA) w zakresie heurystyk dla przeszukiwań grafowych, algorytmów A* ważonych i metod optymalizacji ścieżek na siatkach."
      },
      {
        "index": 3,
        "title": "Rozdział 3: Metodologia",
        "focus": "Opis implementacji heurystyki oktilowej, algorytmu Weighted A*, modyfikacji istniejącego kodu bazowego Dijkstry oraz definicji metryk eksperymentalnych."
      },
      {
        "index": 4,
        "title": "Rozdział 4: Wyniki i Dyskusja",
        "focus": "Prezentacja wyników eksperymentu (redukcja węzłów vs optymalność), analiza wpływu wagi heurystyki i gęstości przeszkód, wnioski końcowe."
      }
    ]
  }
}
```

</details>

---
