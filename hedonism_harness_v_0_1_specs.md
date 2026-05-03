# Hedonism Harness v0.1 — Technical Specification Draft

## 1. Project Purpose

**Hedonism Harness** is a 2D artificial-life experiment for testing whether survival, exploration, paralysis, reproduction, and risk-taking can emerge from inherited pleasure/pain thresholds interacting with sensory limits, memory, and environmental tradeoffs.

This is not primarily an optimization project. The purpose is to observe what kinds of behaviors emerge when agents are not given handcrafted drives such as “seek food,” “be brave,” “explore,” “mate,” or “avoid danger.” Instead, agents experience internal and external conditions as gradients of pleasure and pain.

The core thesis:

> All primitive drives can be modeled as valence gradients: organisms pursue states that relieve pain or produce pleasure, avoid states that create pain, and inherit different thresholds/tolerances that shape their behavior over generations.

The project should begin with interpretable artificial-life agents before adding reinforcement-learning agents. RL can be introduced later as a comparison layer, but v0.1 should prioritize clarity, determinism, observability, and testability.

---

## 2. v0.1 Research Question

The first experiment should answer:

> Can agents with inherited pleasure/pain thresholds produce recognizable survival strategies in a simple 2D world without hardcoded behavior rules?

Secondary questions:

* Does hunger pain eventually overcome fear paralysis?
* Do different pain/pleasure thresholds produce distinct behavioral phenotypes?
* Do some trait profiles survive by hiding while others survive by risk-taking?
* Does reproduction select for different thresholds under different environmental conditions?
* Does simple valence memory improve survival or create over-avoidance/cowardice?

---

## 3. v0.1 Scope

### Included

* 2D grid world
* Food cells
* Hazard cells
* Safe/barren regions
* Energy decay
* Health damage
* Agent death by starvation or injury
* Minimal reproduction
* Trait inheritance with mutation
* Pleasure/pain harness
* Simple local sensors
* Optional explicit valence memory map
* Deterministic seeded runs
* Metrics logging
* Basic visualization, preferably ASCII first, then optional Pygame-CE
* Pytest-based test suite

### Excluded from v0.1

* Unity
* Complex physics
* Sexual reproduction
* Parenting behavior
* Social bonding
* Predators as separate learning entities
* Neural network agents
* Stable-Baselines3 / PPO training
* Complex ecology balancing
* Raw pixel observations
* LLM agents

---

## 4. Recommended Repo Structure

```text
hedonism-harness/
    README.md
    pyproject.toml
    .gitignore
    docs/
        SPEC.md
        EXPERIMENTS.md
        TRAITS.md
        ROADMAP.md
    src/
        hedonism_harness/
            __init__.py
            config.py
            core/
                __init__.py
                world.py
                cell.py
                agent.py
                traits.py
                sensors.py
                actions.py
                valence.py
                memory.py
                reproduction.py
                metrics.py
                simulation.py
            agents/
                __init__.py
                random_agent.py
                reflex_agent.py
                hedonism_agent.py
            experiments/
                __init__.py
                fear_hunger_chamber.py
                run_batch.py
                compare_lineages.py
            viz/
                __init__.py
                ascii_renderer.py
                pygame_renderer.py
            utils/
                __init__.py
                rng.py
                serialization.py
    tests/
        test_world.py
        test_agent_body.py
        test_traits.py
        test_valence.py
        test_memory.py
        test_reproduction.py
        test_simulation.py
        test_metrics.py
```

---

## 5. Core Design Principle

Agents should not be directly instructed to seek food, flee hazards, explore, reproduce, or be brave.

Instead:

1. The world creates bodily and environmental pressures.
2. The agent senses only part of the world.
3. The Hedonism Harness converts sensed and internal conditions into felt pleasure/pain.
4. The agent evaluates possible actions through that felt valence.
5. The agent chooses the action with the highest predicted net valence.
6. Reproduction passes trait thresholds with mutation.

The agent’s apparent behavior should emerge from competing pressures.

Example:

```text
fear pain says: stay safe
hunger pain says: move toward food
movement cost says: conserve energy
hazard memory says: avoid this route
reproductive pleasure says: reproduce if surplus exists
```

The agent acts based on which felt pressure dominates.

---

## 6. World Model

### 6.1 Grid

The world should be a deterministic 2D grid.

Initial v0.1 defaults:

```python
width = 64
height = 64
max_ticks = 5000
seed = 12345
```

Each cell may contain:

```python
EMPTY
FOOD
HAZARD
WALL
SAFE
```

For v0.1, avoid stacking too many features. A cell can hold one primary terrain/content type plus optional numeric fields.

### 6.2 Cell Fields

Recommended `Cell` fields:

```python
@dataclass
class Cell:
    kind: CellKind
    food_value: float = 0.0
    hazard_damage: float = 0.0
    safe_value: float = 0.0
```

### 6.3 World Responsibilities

`World` should handle:

* grid creation
* seeded random generation
* bounds checking
* cell lookup
* food consumption
* hazard application
* optional food regrowth
* agent placement
* occupancy checks

Do not put agent decision logic inside the world.

---

## 7. Agent Body State

Each agent should have:

```python
@dataclass
class Agent:
    id: int
    lineage_id: int
    parent_id: int | None
    x: int
    y: int
    energy: float
    health: float
    age: int
    traits: Traits
    memory: ValenceMemory | None
    alive: bool = True
```

Recommended defaults:

```python
max_energy = 100.0
starting_energy = 60.0
max_health = 100.0
starting_health = 100.0
base_metabolic_cost = 0.25
move_cost = 1.0
stay_cost = 0.1
reproduction_energy_cost = 35.0
offspring_start_energy = 30.0
```

Death conditions:

```python
energy <= 0 -> starvation death
health <= 0 -> injury death
```

Age death should be excluded from v0.1 unless needed later.

---

## 8. Trait Genome

Traits are inherited parameters that transform world states into felt pleasure/pain.

Recommended v0.1 trait set:

```python
@dataclass
class Traits:
    hunger_pain_sensitivity: float
    injury_pain_sensitivity: float
    fear_sensitivity: float
    pleasure_sensitivity: float
    reproduction_drive: float
    novelty_drive: float
    uncertainty_aversion: float
    pain_tolerance: float
    risk_tolerance: float
    memory_strength: float
    memory_decay_rate: float
    sensor_radius: int
    metabolic_rate: float
```

### 8.1 Trait Ranges

Suggested ranges:

```python
hunger_pain_sensitivity: 0.25 - 2.5
injury_pain_sensitivity: 0.25 - 2.5
fear_sensitivity: 0.0 - 3.0
pleasure_sensitivity: 0.25 - 2.5
reproduction_drive: 0.0 - 3.0
novelty_drive: 0.0 - 2.0
uncertainty_aversion: 0.0 - 2.0
pain_tolerance: 0.0 - 1.0
risk_tolerance: 0.0 - 1.0
memory_strength: 0.0 - 1.0
memory_decay_rate: 0.0 - 0.1
sensor_radius: 1 - 6
metabolic_rate: 0.5 - 2.0
```

### 8.2 Mutation

Each offspring inherits parent traits with mutation.

Recommended approach:

```python
child_trait = parent_trait + normal_random(0, mutation_sigma)
child_trait = clamp(child_trait, min_value, max_value)
```

Suggested defaults:

```python
mutation_rate = 0.15
mutation_sigma = 0.08
```

Mutation should be deterministic under seed control.

---

## 9. Actions

v0.1 action set:

```python
class Action(Enum):
    MOVE_NORTH
    MOVE_SOUTH
    MOVE_EAST
    MOVE_WEST
    STAY
    EAT
    REPRODUCE
```

Avoid explicit actions like `FLEE`, `SEEK_FOOD`, or `EXPLORE`. Those should emerge from valence scoring.

---

## 10. Sensors

Agents should have partial world access.

### 10.1 Internal Sensors

Always available:

```python
energy_ratio = energy / max_energy
health_ratio = health / max_health
hunger_level = 1.0 - energy_ratio
injury_level = 1.0 - health_ratio
age
```

### 10.2 External Sensors

For each direction, estimate nearby food and hazard signal within `sensor_radius`.

```python
food_signal_north
food_signal_south
food_signal_east
food_signal_west
hazard_signal_north
hazard_signal_south
hazard_signal_east
hazard_signal_west
```

Signals should decay by distance.

Example:

```python
signal += cell_value / distance
```

### 10.3 Memory Sensors

If memory is enabled:

```python
remembered_good_north
remembered_good_south
remembered_good_east
remembered_good_west
remembered_bad_north
remembered_bad_south
remembered_bad_east
remembered_bad_west
```

---

## 11. Hedonism Harness

The Hedonism Harness converts a predicted or current state into felt valence.

### 11.1 Conceptual Formula

```text
net_valence = pleasure - pain - fear - uncertainty - effort_cost
```

Each component is filtered by traits.

### 11.2 Pain Components

Recommended pain sources:

```python
hunger_pain = hunger_level * traits.hunger_pain_sensitivity * (1.0 - traits.pain_tolerance)
injury_pain = injury_level * traits.injury_pain_sensitivity * (1.0 - traits.pain_tolerance)
hazard_pain = expected_damage * traits.injury_pain_sensitivity
energy_cost_pain = action_energy_cost * traits.hunger_pain_sensitivity
```

### 11.3 Fear Components

Fear is predicted pain, not actual damage.

```python
fear = predicted_hazard_risk * traits.fear_sensitivity * (1.0 - traits.risk_tolerance)
```

Fear should be capable of causing paralysis, but hunger should be able to override it under the right trait conditions.

### 11.4 Pleasure Components

Recommended pleasure sources:

```python
eating_pleasure = food_gain * hunger_level * traits.pleasure_sensitivity
safety_pleasure = reduction_in_predicted_hazard * traits.pleasure_sensitivity
recovery_pleasure = health_recovered * traits.pleasure_sensitivity
reproduction_pleasure = reproduction_opportunity * traits.reproduction_drive * traits.pleasure_sensitivity
novelty_pleasure = novelty_score * traits.novelty_drive
```

Eating when full should provide little or no pleasure.

### 11.5 Uncertainty

Unknown or poorly remembered cells may produce uncertainty pain.

```python
uncertainty_pain = uncertainty_score * traits.uncertainty_aversion
```

This allows high-uncertainty agents to become cautious and low-uncertainty agents to become exploratory.

### 11.6 Output

The harness should return both scalar score and explainable components.

```python
@dataclass
class ValenceBreakdown:
    total: float
    pleasure: float
    pain: float
    fear: float
    uncertainty: float
    effort: float
    details: dict[str, float]
```

This is critical for debugging and research.

---

## 12. Action Selection

The `HedonismAgent` should evaluate each possible action shallowly.

Pseudo-code:

```python
possible_actions = get_valid_actions(agent, world)

best_action = None
best_score = -inf

for action in possible_actions:
    predicted = predict_one_step(agent, world, action)
    breakdown = hedonism_harness.evaluate(agent, world, predicted)
    score = breakdown.total

    if score > best_score:
        best_score = score
        best_action = action

return best_action
```

Add small stochasticity so populations do not become fully deterministic clones.

```python
if rng.random() < exploration_noise:
    choose weighted random action
else:
    choose best action
```

Suggested default:

```python
exploration_noise = 0.03
```

---

## 13. Valence Memory

Memory stores compressed pain/pleasure associations.

### 13.1 Memory Cell

```python
@dataclass
class MemoryCell:
    pleasure_ema: float = 0.0
    pain_ema: float = 0.0
    visits: int = 0
    last_seen_tick: int = 0
```

### 13.2 Update Rule

After each action, update memory at the agent’s current location:

```python
pleasure_ema = (1 - alpha) * old_pleasure + alpha * current_pleasure
pain_ema = (1 - alpha) * old_pain + alpha * current_pain
visits += 1
last_seen_tick = tick
```

`alpha` should be affected by `traits.memory_strength`.

### 13.3 Decay

Memory decays over time:

```python
pleasure_ema *= (1 - memory_decay_rate)
pain_ema *= (1 - memory_decay_rate)
```

### 13.4 Memory Inheritance

For v0.1, memory should probably **not** be inherited by default. Traits should be inherited; individual memories should not.

Optional experiment later:

* inherited memory fragments
* species-level shared memory
* cultural memory

---

## 14. Reproduction

v0.1 should use minimal asexual reproduction.

Conditions:

```python
agent.energy >= reproduction_energy_threshold
agent.age >= min_reproduction_age
local_hazard_risk <= reproduction_hazard_threshold
```

When reproduction occurs:

```python
parent.energy -= reproduction_energy_cost
child.energy = offspring_start_energy
child.health = parent starting health or default health
child.traits = mutate(parent.traits)
child.lineage_id = parent.lineage_id
child.parent_id = parent.id
child placed in adjacent empty cell
```

Reproduction should create pleasure, but also cost energy.

This is necessary so over-reproduction can become a failure mode.

---

## 15. Agent Types

### 15.1 RandomAgent

Chooses random valid action.

Purpose:

* baseline chaos
* smoke testing environment

### 15.2 ReflexAgent

Uses simple handwritten rules.

Example priority:

```text
if on food and hungry -> eat
if hazard nearby -> move away
if food signal nearby -> move toward food
else random move/stay
```

Purpose:

* baseline authored survival behavior
* compare against emergent valence behavior

### 15.3 HedonismAgent

Uses the Hedonism Harness to score possible actions.

Purpose:

* primary experimental agent

### 15.4 HedonismAgentWithMemory

Same as HedonismAgent, but includes explicit valence memory in scoring.

Purpose:

* test whether memory improves survival, increases caution, or creates paralysis

---

## 16. First Canonical Experiment: Fear-Hunger Conflict Chamber

### 16.1 Purpose

Test whether hunger pain can overcome fear-based paralysis.

### 16.2 World Layout

```text
safe zone -> hazard field -> food zone
```

Agent starts in safe zone.
Food exists outside the safe zone.
A hazard band lies between safety and food.
Energy decays every tick.
Hazard creates expected fear before it creates injury.

### 16.3 Expected Phenotypes

Possible emergent outcomes:

* high fear + low hunger sensitivity -> paralysis and starvation
* low fear + high hunger sensitivity -> reckless crossing, possible injury death
* moderate fear + memory -> cautious movement around hazard
* high pain tolerance -> hazard crossing
* high novelty drive -> exploration despite risk
* high reproduction drive -> reproduce early, possibly unsustainably

### 16.4 Metrics

Track:

```python
survival_ticks
death_cause
offspring_count
hazard_entries
food_events
starvation_ticks
paralysis_ticks
unique_cells_visited
total_distance_traveled
total_pleasure
total_pain
total_fear
average_net_valence
lineage_depth
```

Define paralysis ticks as:

```text
Ticks where the agent stays still or oscillates locally while hunger pain increases and available food remains outside the safe zone.
```

The exact implementation can start simpler:

```python
paralysis_tick = action == STAY and hunger_level > 0.5
```

Then refine later.

---

## 17. Metrics and Logging

Use CSV or JSONL for early metrics.

Recommended files:

```text
runs/{run_id}/config.json
runs/{run_id}/episode_metrics.csv
runs/{run_id}/agent_lifetimes.csv
runs/{run_id}/trait_snapshots.csv
runs/{run_id}/lineages.csv
```

### 17.1 Episode Metrics

```python
run_id
seed
ticks_completed
population_start
population_end
total_births
total_deaths
starvation_deaths
injury_deaths
average_survival_ticks
average_offspring
average_pain
average_pleasure
average_fear
average_exploration
```

### 17.2 Agent Lifetime Metrics

```python
agent_id
lineage_id
parent_id
birth_tick
death_tick
death_cause
offspring_count
food_events
hazard_entries
unique_cells_visited
total_pain
total_pleasure
total_fear
traits_json
```

---

## 18. Testing Plan

Use pytest. Do not begin ML or visualization before core tests pass.

### 18.1 World Tests

* World initializes deterministically from seed.
* Same seed creates same grid.
* Different seed creates different grid.
* Cell lookup respects bounds.
* Food can be consumed once.
* Hazard applies damage.

### 18.2 Agent Body Tests

* Energy decreases each tick.
* Movement costs more energy than staying.
* Eating increases energy.
* Health decreases when hazard is applied.
* Agent dies when energy <= 0.
* Agent dies when health <= 0.

### 18.3 Trait Tests

* Trait generation respects configured ranges.
* Mutation respects configured ranges.
* Mutation is deterministic under seed.
* Offspring traits differ from parent within expected mutation bounds.

### 18.4 Valence Tests

* Hunger pain increases as energy decreases.
* Eating pleasure is higher when hungry than when full.
* Fear increases with predicted hazard risk.
* Pain tolerance reduces felt pain.
* Risk tolerance reduces fear.
* Reproduction pleasure scales with reproduction drive.
* Valence breakdown total equals component sum.
* No valence result returns NaN or infinity.

### 18.5 Memory Tests

* Memory updates after pleasure.
* Memory updates after pain.
* Memory decays over time.
* Memory confidence increases with visits.
* Memory sensor returns directional good/bad values.

### 18.6 Reproduction Tests

* Agent cannot reproduce below energy threshold.
* Agent can reproduce above energy threshold if space exists.
* Parent pays energy cost.
* Child receives mutated traits.
* Child receives correct parent_id and lineage_id.

### 18.7 Simulation Tests

* Simulation advances ticks.
* Dead agents are removed or marked inactive.
* Metrics are recorded.
* Batch run with fixed seed is reproducible.
* No run produces invalid metrics.

---

## 19. Implementation Order

Chronus should implement in this order:

1. Create repo skeleton and pyproject.
2. Implement config objects.
3. Implement `Cell`, `World`, deterministic generation.
4. Implement `Traits` generation and mutation.
5. Implement `Agent` body state and lifecycle.
6. Implement actions and action application.
7. Implement sensors.
8. Implement `ValenceBreakdown` and Hedonism Harness.
9. Implement `RandomAgent`.
10. Implement `ReflexAgent`.
11. Implement `HedonismAgent` without memory.
12. Implement `ValenceMemory`.
13. Implement `HedonismAgentWithMemory`.
14. Implement minimal reproduction.
15. Implement simulation loop.
16. Implement metrics logging.
17. Implement Fear-Hunger Conflict Chamber.
18. Add ASCII renderer.
19. Add batch experiment runner.
20. Add basic charts or CSV output.

Every step should include tests before proceeding.

---

## 20. Development Standards

* Python 3.11+
* Use dataclasses or Pydantic-style configs, but avoid overengineering.
* Prefer pure Python + NumPy initially.
* Keep the simulation deterministic under seeded RNG.
* Avoid hidden global random state.
* Keep agent decision logic separate from world update logic.
* Keep valence scoring explainable.
* Every major calculation should be testable.
* Avoid premature RL integration.
* Avoid visual polish until core metrics are trustworthy.

Recommended dependencies:

```text
numpy
pandas
matplotlib
pytest
rich
pygame-ce optional
```

Do not add Gymnasium or Stable-Baselines3 until the core artificial-life experiment works.

---

## 21. README Draft

```markdown
# Hedonism Harness

A 2D artificial-life experiment testing whether survival, exploration, paralysis, risk-taking, and reproduction can emerge from inherited pleasure/pain thresholds rather than handcrafted behavior rules.

The project models agents as embodied organisms with internal states, limited sensors, valence memory, and inherited traits. Agents are not told to seek food, flee danger, or explore. Instead, they evaluate possible actions through a pleasure/pain harness and reproduce with mutated thresholds.

## Core Question

Can different tolerances to hunger, fear, pain, novelty, pleasure, and uncertainty produce distinct survival strategies over generations?

## v0.1 Experiment

The first canonical experiment is the Fear-Hunger Conflict Chamber:

- Agent starts in a safe but food-poor zone.
- Food exists beyond a hazardous region.
- Hunger pain rises over time.
- Fear rises near danger.
- The experiment observes when hunger overcomes paralysis, which trait profiles survive, and which reproduce.

## Status

Draft specification stage.
```

---

## 22. Open Design Questions

These can remain unresolved during initial repo creation:

1. Should memory influence action scoring directly, or only through sensor features?
2. Should reproduction happen automatically when valence favors it, or only as an evaluated action?
3. Should agents be allowed to stay indefinitely, or should stillness create discomfort over time?
4. Should novelty pleasure be included in v0.1 or saved for v0.2?
5. Should safe zones create pleasure, reduce pain, or both?
6. Should offspring inherit any memory fragments later?
7. Should high sensor radius increase metabolic cost in v0.1?

Recommended v0.1 defaults:

* Memory influences action scoring through directional remembered good/bad signals.
* Reproduction is an evaluated action.
* Staying has low energy cost but can still lead to hunger pain.
* Include novelty drive but keep it weak.
* Safe zones reduce fear rather than directly creating strong pleasure.
* No inherited memory yet.
* Sensor radius should increase metabolic cost slightly.

---

## 23. Definition of Done for v0.1

v0.1 is complete when:

1. The simulation runs from a seed and produces reproducible results.
2. RandomAgent, ReflexAgent, HedonismAgent, and HedonismAgentWithMemory exist.
3. Agents can eat, take damage, die, and reproduce.
4. Traits inherit and mutate.
5. The Hedonism Harness returns explainable pleasure/pain/fear/uncertainty components.
6. The Fear-Hunger Conflict Chamber runs successfully.
7. Batch experiments produce CSV or JSONL metrics.
8. Tests cover world logic, traits, valence, memory, reproduction, and simulation loop.
9. A basic renderer allows visual inspection of agent/world state.
10. At least one batch comparison can be run between agent types.

---

## 24. Future Roadmap

### v0.2

* More world layouts
* Food regrowth
* Sensor cost tradeoffs
* Better memory visualization
* Lineage tree visualization
* Stable population experiments
* More refined paralysis metric

### v0.3

* Gymnasium environment wrapper
* Stable-Baselines3 PPO comparison
* RecurrentPPO comparison
* Learned policies using same valence reward harness

### v0.4

* Multi-species environments
* Predators/prey
* Social pleasure/pain
* Offspring bonding
* Cultural/shared memory

### v0.5

* Continuous 2D world
* Pygame or lightweight browser visualization
* Interactive experiment dashboard

---

## 25. Instruction to Chronus

Start with the v0.1 artificial-life implementation. Do not implement RL yet. Do not build Unity. Do not overbuild visualization. The priority is a deterministic, testable, interpretable simulation where the Hedonism Harness is the central experimental object.

Before writing major code, create:

1. `README.md`
2. `docs/SPEC.md`
3. `pyproject.toml`
4. initial package skeleton
5. first pytest files for world, traits, valence, and simulation determinism

Then proceed in the implementation order above.

---

## 26. Software Leverage Decisions

The project should use mature libraries where they reduce boilerplate without hiding the experimental logic. The rule is:

> Use libraries for plumbing, validation, metrics, testing, and visualization scaffolding. Keep the novel science — traits, sensors, valence, memory, reproduction pressure, and decision scoring — in our own clear modules.

### 26.1 Adopt Mesa as the Backbone

Use Mesa 3.x as the simulation backbone.

Mesa should provide:

* model lifecycle
* agent lifecycle scaffolding
* grid / spatial structures
* scheduling
* data collection
* batch runs
* optional later visualization

This changes the earlier pure custom architecture. Instead of writing our own full `Simulation` orchestrator, we use a Mesa `Model` subclass as the imperative shell.

However, our domain logic remains independent:

```text
traits.py
sensors.py
valence.py
memory.py
actions.py
reproduction.py
```

Mesa may own the outer simulation loop, but it should not own the Hedonism Harness.

Decision:

```text
Use Mesa for ABM plumbing.
Keep Hedonism Harness logic pure and framework-light.
Do not let Agent.step() become a god method.
```

### 26.2 Adjusted Architecture with Mesa

Recommended structure:

```text
src/hedonism_harness/
    model.py              # Mesa Model subclass
    mesa_agents.py        # Mesa Agent wrappers
    core/
        traits.py
        sensors.py
        valence.py
        memory.py
        actions.py
        reproduction.py
        events.py
        config.py
    experiments/
        fear_hunger_chamber.py
        batch.py
    viz/
        terminal.py
        mesa_viz.py
    tests/
```

Mesa `Agent.step()` should remain thin:

```python
observation = observe(model.world, self.body, self.memory, config)
action, breakdown = self.policy.decide(observation, self.body.traits, rng)
result = apply_action(model.world, self.body, action, config, rng)
self.memory = update_memory(self.memory, result, config)
emit_events(result.events)
```

The agent wrapper coordinates. The real logic lives in testable modules.

### 26.3 State Mutation Compromise

Mesa is stateful by design. That is acceptable as long as we keep pure functions at the domain layer.

Revised decision:

```text
Use Mesa's stateful model/agent lifecycle.
Keep valence, sensors, trait mutation, memory update, and action scoring pure or near-pure.
Use tests to protect those modules from framework coupling.
```

This is a practical compromise: less plumbing, faster experimentation, still scientifically inspectable.

### 26.4 Event and Metrics Stack

Use both:

* Mesa `DataCollector` for snapshot-style metrics.
* Blinker or a lightweight typed event layer for event-style metrics.

Mesa DataCollector is good for:

```text
population count
average energy
average fear
average pain
average offspring
trait averages per tick
```

Events are better for:

```text
agent born
agent died
food eaten
hazard entered
reproduction failed
memory updated
paralysis tick
```

Decision:

```text
Use Mesa DataCollector for periodic snapshots.
Use a lightweight event layer for discrete life-history events.
Do not write CSV from core logic.
```

### 26.5 Configuration

Use Pydantic v2 for configuration validation and JSON serialization.

Use composed configs:

```python
SimulationConfig
WorldConfig
TraitConfig
HarnessConfig
MemoryConfig
ReproductionConfig
ExperimentConfig
```

Every run should write the resolved config to:

```text
runs/{run_id}/config.json
```

Hydra is deferred. Pydantic plus a small CLI is enough for v0.1.

Decision:

```text
Pydantic v2 now.
Hydra later if experiment sweeps become painful.
```

### 26.6 Lineage Tracking

Use a simple internal lineage tracker first, but leave an adapter seam for Phylotrackpy.

Phylotrackpy is strongly aligned with the long-term project, but it may be more dependency than needed before the reproduction model stabilizes.

v0.1 should record:

```text
agent_id
parent_id
lineage_id
birth_tick
death_tick
death_cause
offspring_count
traits_json
```

Add Phylotrackpy once:

* reproduction semantics are stable
* lineage metrics become central
* population size grows
* pruning extinct lineages matters

Decision:

```text
Do not block v0.1 on Phylotrackpy.
Design lineage logging so Phylotrackpy can be added later.
```

### 26.7 Testing Stack

Use:

```text
pytest
hypothesis
pytest-benchmark optional
```

Hypothesis should be added immediately because many core truths are properties, not single examples.

Good Hypothesis targets:

```text
mutation always stays in range
valence total equals component sum
no valid trait genome produces NaN
memory decay never increases absolute memory unless updated
same seed produces same world
same seed produces same first N events
```

Decision:

```text
Use pytest + Hypothesis from the start.
Add benchmark tests after the model is stable.
```

### 26.8 Numerical and Signal Computation

Start with NumPy only.

Use SciPy later if sensor calculations become expensive.

Decision:

```text
Naive sensor loops are acceptable in v0.1.
Keep sensor API swappable for future NumPy/SciPy convolution acceleration.
```

### 26.9 Dev Tooling

Use:

```text
uv
ruff
mypy or pyright
pre-commit
```

Suggested default:

```text
uv for project/dependency management
ruff for linting and formatting
mypy for type checking
pre-commit for enforcement
```

Decision:

```text
Adopt uv + ruff immediately.
Add mypy once core types settle.
```

### 26.10 Deferred Libraries

Do not add these in v0.1:

```text
Gymnasium
Stable-Baselines3
Ray/RLlib
PyTorch
JAX
DEAP
Hydra
Aim
Streamlit
Gradio
full dashboard stack
```

Reason: each one is potentially useful later, but each increases surface area before the artificial-life core has proven itself.

### 26.11 Final v0.1 Dependency Recommendation

Core dependencies:

```text
mesa
numpy
pandas
pydantic
pytest
hypothesis
rich
blinker
```

Dev dependencies:

```text
ruff
mypy
pre-commit
pytest-benchmark optional
```

Deferred:

```text
phylotrackpy
scipy
pyarrow
hydra-core
hydra-zen
deap
aim
gymnasium
stable-baselines3
pygame-ce
```

### 26.12 Updated Instruction to Chronus

Proceed with Mesa as the backbone unless installation or API friction becomes obvious in the first scaffold.

Chronus should first build a thin Mesa model with one RandomAgent and one deterministic test world. Then add the Hedonism Harness modules one at a time.

Immediate implementation sequence:

1. Set up `uv`, `pyproject.toml`, `ruff`, `pytest`, `hypothesis`.
2. Install Mesa, NumPy, Pydantic, Pandas, Rich, and Blinker.
3. Create a minimal Mesa model and grid.
4. Add deterministic seed handling using NumPy RNG streams.
5. Add RandomAgent smoke test.
6. Add Traits and trait-range tests.
7. Add ValenceBreakdown and valence property tests.
8. Add HedonismAgent.
9. Add reproduction and lineage CSV logging.
10. Add Fear-Hunger Conflict Chamber.

The first proof point is not visual beauty. The first proof point is:

```text
Given the same seed, the same model config produces the same world, same first N events, and same final metrics.
```
