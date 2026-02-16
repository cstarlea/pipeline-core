# Flow State Machine

This document describes the formal state machine for pipeline flow orchestration, inspired by CrewAI Flows.

## Overview

The pipeline implements a deterministic, event-driven workflow using two complementary state machines:
1. **Flow State Machine**: Manages overall run lifecycle
2. **Role State Machine**: Manages individual role execution within a flow

## Flow State Machine

The Flow State Machine manages the overall lifecycle of a pipeline run.

### States

- **CREATED**: Initial state when a run is created
- **PENDING**: Run is waiting to start orchestration
- **RUNNING**: Run is actively executing roles
- **COMPLETED**: All roles completed successfully
- **FAILED**: One or more roles failed
- **ARCHIVED**: Run is finalized and archived (terminal state)

### State Transitions

```
CREATED → PENDING → RUNNING → COMPLETED → ARCHIVED
                        ↓
                     FAILED → ARCHIVED
```

Valid transitions:
- `CREATED → PENDING`: When orchestration starts
- `PENDING → RUNNING`: When first role spawns
- `RUNNING → COMPLETED`: When all roles complete successfully
- `RUNNING → FAILED`: When any role fails
- `COMPLETED → ARCHIVED`: When run is finalized after success
- `FAILED → ARCHIVED`: When failure is recorded

### Terminal States

- **ARCHIVED**: No further transitions allowed

## Role State Machine

The Role State Machine manages individual role execution within a flow.

### States

- **PENDING**: Role is waiting to be spawned
- **RUNNING**: Role is actively executing
- **COMPLETED**: Role finished successfully
- **FAILED**: Role encountered an error

### State Transitions

```
PENDING → RUNNING → COMPLETED
              ↓
           FAILED
```

Valid transitions:
- `PENDING → RUNNING`: When role is spawned
- `RUNNING → COMPLETED`: When role finishes successfully
- `RUNNING → FAILED`: When role encounters an error

### Terminal States

- **COMPLETED**: Role finished successfully
- **FAILED**: Role failed (no recovery)

## Orchestration Rules

The state machine enforces the following orchestration rules:

1. **Sequential Execution**: Only one role can be in `RUNNING` state at a time
2. **No Parallel Runs**: Multiple runs can exist, but each has independent state
3. **Completion Contract**: A role must produce required outputs before transitioning to `COMPLETED`
4. **Failure Halts Flow**: If any role transitions to `FAILED`, the flow transitions to `FAILED`
5. **Deterministic Transitions**: All state transitions are logged and auditable

## Usage

### Creating a Flow State Machine

```python
from orchestration.flow_state_machine import FlowStateMachine, FlowState

# Create a new flow
flow = FlowStateMachine(initial_state=FlowState.CREATED)

# Start orchestration
flow.transition(FlowState.PENDING)

# Begin execution
flow.transition(FlowState.RUNNING)

# Complete successfully
flow.transition(FlowState.COMPLETED)

# Archive
flow.transition(FlowState.ARCHIVED)
```

### Creating a Role State Machine

```python
from orchestration.flow_state_machine import RoleStateMachine, RoleState

# Create a new role
role = RoleStateMachine(initial_state=RoleState.PENDING)

# Spawn the role
role.transition(RoleState.RUNNING)

# Complete successfully
role.transition(RoleState.COMPLETED)
```

### Validating Transitions

```python
# Check if a transition is valid before attempting it
if flow.can_transition(FlowState.RUNNING):
    flow.transition(FlowState.RUNNING)
else:
    print("Invalid transition")
```

## Integration with Existing Pipeline

The state machine is integrated into the existing pipeline orchestration:

1. **Run Creation** (`task-create`): Flow starts in `CREATED` state
2. **Orchestration Start** (`orchestrate`): Flow transitions to `PENDING`, then `RUNNING`
3. **Role Execution**: Each role follows its own state machine
4. **Completion**: Flow transitions to `COMPLETED` or `FAILED`
5. **Archival**: After PR creation or failure recording, flow transitions to `ARCHIVED`

## Benefits

1. **Deterministic**: All state transitions are explicit and validated
2. **Auditable**: State changes can be logged for debugging
3. **Safe**: Invalid transitions are prevented at runtime
4. **Clear**: The lifecycle is formally defined and documented
5. **Extensible**: New states or transitions can be added systematically

## See Also

- `orchestration/flow_state_machine.py`: Implementation
- `scripts/pipeline.py`: Orchestration logic
- `REVIEW.md`: Design principles and safeguards
