#!/usr/bin/env python3
"""
Flow state machine for deterministic pipeline orchestration.

Inspired by CrewAI Flows, this module provides a formal state machine
for managing run lifecycle transitions.
"""
from __future__ import annotations
from enum import Enum


class FlowState(Enum):
    """States in the pipeline flow lifecycle."""
    CREATED = "created"
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    ARCHIVED = "archived"


class RoleState(Enum):
    """States for individual roles within a flow."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class StateTransitionError(Exception):
    """Raised when an invalid state transition is attempted."""
    pass


class FlowStateMachine:
    """
    State machine for managing flow lifecycle.
    
    Valid transitions:
    - CREATED -> PENDING (when orchestration starts)
    - PENDING -> RUNNING (when first role spawns)
    - RUNNING -> COMPLETED (when all roles complete)
    - RUNNING -> FAILED (when any role fails)
    - COMPLETED -> ARCHIVED (when run is finalized)
    - FAILED -> ARCHIVED (when failure is recorded)
    """
    
    VALID_TRANSITIONS = {
        FlowState.CREATED: {FlowState.PENDING},
        FlowState.PENDING: {FlowState.RUNNING},
        FlowState.RUNNING: {FlowState.COMPLETED, FlowState.FAILED},
        FlowState.COMPLETED: {FlowState.ARCHIVED},
        FlowState.FAILED: {FlowState.ARCHIVED},
        FlowState.ARCHIVED: set(),  # Terminal state
    }
    
    def __init__(self, initial_state: FlowState = FlowState.CREATED):
        self.state = initial_state
    
    def transition(self, new_state: FlowState) -> None:
        """
        Transition to a new state.
        
        Args:
            new_state: The target state
            
        Raises:
            StateTransitionError: If the transition is invalid
        """
        if new_state not in self.VALID_TRANSITIONS.get(self.state, set()):
            raise StateTransitionError(
                f"Invalid transition from {self.state.value} to {new_state.value}"
            )
        self.state = new_state
    
    def can_transition(self, new_state: FlowState) -> bool:
        """Check if a transition is valid without performing it."""
        return new_state in self.VALID_TRANSITIONS.get(self.state, set())
    
    @property
    def is_terminal(self) -> bool:
        """Check if the current state is terminal (no further transitions)."""
        return len(self.VALID_TRANSITIONS.get(self.state, set())) == 0


class RoleStateMachine:
    """
    State machine for managing individual role lifecycle.
    
    Valid transitions:
    - PENDING -> RUNNING (when role is spawned)
    - RUNNING -> COMPLETED (when role finishes successfully)
    - RUNNING -> FAILED (when role encounters an error)
    """
    
    VALID_TRANSITIONS = {
        RoleState.PENDING: {RoleState.RUNNING},
        RoleState.RUNNING: {RoleState.COMPLETED, RoleState.FAILED},
        RoleState.COMPLETED: set(),  # Terminal state
        RoleState.FAILED: set(),  # Terminal state
    }
    
    def __init__(self, initial_state: RoleState = RoleState.PENDING):
        self.state = initial_state
    
    def transition(self, new_state: RoleState) -> None:
        """
        Transition to a new state.
        
        Args:
            new_state: The target state
            
        Raises:
            StateTransitionError: If the transition is invalid
        """
        if new_state not in self.VALID_TRANSITIONS.get(self.state, set()):
            raise StateTransitionError(
                f"Invalid role transition from {self.state.value} to {new_state.value}"
            )
        self.state = new_state
    
    def can_transition(self, new_state: RoleState) -> bool:
        """Check if a transition is valid without performing it."""
        return new_state in self.VALID_TRANSITIONS.get(self.state, set())
    
    @property
    def is_terminal(self) -> bool:
        """Check if the current state is terminal (no further transitions)."""
        return len(self.VALID_TRANSITIONS.get(self.state, set())) == 0
