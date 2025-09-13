"""
Planning System for Complex Scraping Tasks
Based on Cline AI planning patterns
"""

import asyncio
import json
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum


class PlanningMode(Enum):

class PlanningPhase(Enum):
    ANALYSIS = "analysis"
    PLANNING = "planning"
    EXECUTION = "execution"
    VALIDATION = "validation"

@dataclass
class PlanningStep:
    """Individual step in a planning process"""
    id: str
    description: str
    phase: PlanningPhase
    dependencies: List[str] = field(default_factory=list)
    estimated_effort: str = "medium"  # low, medium, high
    tools_needed: List[str] = field(default_factory=list)
    success_criteria: str = ""
    completed: bool = False
    result: Optional[Any] = None

@dataclass
class ScrapingPlan:
    """Complete plan for a scraping task"""
    id: str
    title: str
    description: str
    mode: PlanningMode = PlanningMode.PLAN
    current_phase: PlanningPhase = PlanningPhase.ANALYSIS
    steps: List[PlanningStep] = field(default_factory=list)
    context: Dict[str, Any] = field(default_factory=dict)
    mermaid_diagram: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

class PlanningSystem:
    """Planning system for complex scraping tasks"""

    def __init__(self):
        self.plans: Dict[str, ScrapingPlan] = {}
        self.current_plan: Optional[str] = None

    def create_plan(self, title: str, description: str) -> str:
        """Create a new scraping plan"""
        plan_id = f"plan_{int(datetime.now().timestamp())}_{len(self.plans)}"
        plan = ScrapingPlan(
            id=plan_id,
            title=title,
            description=description
        )
        self.plans[plan_id] = plan
        self.current_plan = plan_id
        return plan_id

    def add_step(self, plan_id: str, step_id: str, description: str,
                 phase: PlanningPhase, dependencies: Optional[List[str]] = None,
                 estimated_effort: str = "medium", tools_needed: Optional[List[str]] = None,
                 success_criteria: str = "") -> bool:
        """Add a step to a plan"""
        if plan_id not in self.plans:
            return False

        step = PlanningStep(
            id=step_id,
            description=description,
            phase=phase,
            dependencies=dependencies or [],
            estimated_effort=estimated_effort,
            tools_needed=tools_needed or [],
            success_criteria=success_criteria
        )

        self.plans[plan_id].steps.append(step)
        self.plans[plan_id].updated_at = datetime.now()
        return True

    def generate_mermaid_diagram(self, plan_id: str) -> Optional[str]:
        """Generate a Mermaid diagram for the plan"""
        if plan_id not in self.plans:
            return None

        plan = self.plans[plan_id]

        # Group steps by phase
        phases = {}
        for step in plan.steps:
            if step.phase.value not in phases:
                phases[step.phase.value] = []
            phases[step.phase.value].append(step)

        # Create Mermaid diagram
        diagram = ["graph TD"]

        # Add phase nodes
        for phase in PlanningPhase:
            phase_name = phase.value
            diagram.append(f"    {phase_name}[\"{phase_name.title()}\"]")

        # Add step nodes and connections
        step_count = 0
        for phase_name, steps in phases.items():
            for step in steps:
                step_node = f"S{step_count}"
                diagram.append(f"    {step_node}[\"{step.description[:30]}...\"]")
                diagram.append(f"    {phase_name} --> {step_node}")
                step_count += 1

        # Add dependencies
        step_map = {step.id: f"S{i}" for i, step in enumerate(plan.steps)}
        for step in plan.steps:
            for dep in step.dependencies:
                if dep in step_map:
                    diagram.append(f"    {step_map[dep]} --> {step_map[step.id]}")

        return "\n".join(diagram)

    def get_next_executable_steps(self, plan_id: str) -> List[PlanningStep]:
        """Get steps that can be executed in current phase"""
        if plan_id not in self.plans:
            return []

        plan = self.plans[plan_id]
        current_phase_steps = [s for s in plan.steps if s.phase == plan.current_phase]

        # Get completed step IDs
        completed_ids = {s.id for s in plan.steps if s.completed}

        # Find executable steps
        executable = []
        for step in current_phase_steps:
            if not step.completed:
                # Check dependencies
                if all(dep in completed_ids for dep in step.dependencies):
                    executable.append(step)

        return executable

    def complete_step(self, plan_id: str, step_id: str, result: Any = None) -> bool:
        """Mark a step as completed"""
        if plan_id not in self.plans:
            return False

        plan = self.plans[plan_id]
        for step in plan.steps:
            if step.id == step_id:
                step.completed = True
                step.result = result
                plan.updated_at = datetime.now()
                return True

        return False

    def advance_phase(self, plan_id: str) -> bool:
        """Advance to the next planning phase"""
        if plan_id not in self.plans:
            return False

        plan = self.plans[plan_id]

        # Check if current phase is complete
        current_phase_steps = [s for s in plan.steps if s.phase == plan.current_phase]
        if not all(step.completed for step in current_phase_steps):
            return False

        # Advance phase
        phases = list(PlanningPhase)
        current_index = phases.index(plan.current_phase)

        if current_index < len(phases) - 1:
            plan.current_phase = phases[current_index + 1]
            plan.updated_at = datetime.now()
            return True

        return False

    def switch_mode(self, plan_id: str, mode: PlanningMode) -> bool:
        """Switch between PLAN and ACT modes"""
        if plan_id not in self.plans:
            return False

        plan = self.plans[plan_id]
        plan.mode = mode
        plan.updated_at = datetime.now()
        return True

    def get_plan_status(self, plan_id: str) -> Optional[Dict[str, Any]]:
        """Get detailed status of a plan"""
        if plan_id not in self.plans:
            return None

        plan = self.plans[plan_id]

        # Calculate progress
        total_steps = len(plan.steps)
        completed_steps = len([s for s in plan.steps if s.completed])
        progress = (completed_steps / total_steps * 100) if total_steps > 0 else 0

        # Phase breakdown
        phase_stats = {}
        for phase in PlanningPhase:
            phase_steps = [s for s in plan.steps if s.phase == phase]
            phase_completed = len([s for s in phase_steps if s.completed])
            phase_stats[phase.value] = {
                "total": len(phase_steps),
                "completed": phase_completed,
                "progress": (phase_completed / len(phase_steps) * 100) if phase_steps else 100
            }

        return {
            "id": plan.id,
            "title": plan.title,
            "description": plan.description,
            "mode": plan.mode.value,
            "current_phase": plan.current_phase.value,
            "progress": progress,
            "total_steps": total_steps,
            "completed_steps": completed_steps,
            "phase_stats": phase_stats,
            "mermaid_diagram": plan.mermaid_diagram,
            "created_at": plan.created_at.isoformat(),
            "updated_at": plan.updated_at.isoformat(),
            "steps": [
                {
                    "id": step.id,
                    "description": step.description,
                    "phase": step.phase.value,
                    "dependencies": step.dependencies,
                    "estimated_effort": step.estimated_effort,
                    "tools_needed": step.tools_needed,
                    "success_criteria": step.success_criteria,
                    "completed": step.completed,
                    "result": step.result
                }
                for step in plan.steps
            ]
        }

    async def analyze_requirements(self, plan_id: str, user_query: str) -> Dict[str, Any]:
        """Analyze user requirements and gather context"""
        print(f"🔍 Analyzing requirements for: {user_query}")

        # Use context optimizer to understand the query
        analysis_prompt = f"""
        Analiza la siguiente consulta del usuario y determina qué tipo de tarea de scraping se necesita:

        Consulta: {user_query}

        Determina:
        1. ¿Qué tipo de datos se necesitan scrapear?
        2. ¿Qué fuentes son relevantes?
        3. ¿Qué complejidad tiene la tarea?
        4. ¿Qué herramientas se necesitan?

        Responde en formato JSON:
        {{
            "data_type": "tipo de datos",
            "sources": ["fuente1", "fuente2"],
            "complexity": "low|medium|high",
            "required_tools": ["tool1", "tool2"],
            "estimated_time": "horas"
        }}
        """

        # This would use GPT-5 Nano for analysis
        # For demo, return mock analysis
        analysis = {
            "data_type": "marketing content",
            "sources": ["google", "websites"],
            "complexity": "medium",
            "required_tools": ["scraper", "classifier", "analyzer"],
            "estimated_time": "4 hours"
        }

        # Store in plan context
        if plan_id in self.plans:
            self.plans[plan_id].context["requirements_analysis"] = analysis

        return analysis

    async def generate_execution_plan(self, plan_id: str) -> bool:
        """Generate detailed execution plan"""
        if plan_id not in self.plans:
            return False

        plan = self.plans[plan_id]
        analysis = plan.context.get("requirements_analysis", {})

        # Create execution steps based on analysis
        if analysis.get("data_type") == "marketing content":
            # Add analysis phase steps
            self.add_step(plan_id, "keyword_analysis", "Analyze target keywords and search volumes",
                         PlanningPhase.ANALYSIS, estimated_effort="low",
                         tools_needed=["keyword_research"], success_criteria="Keywords identified")

            self.add_step(plan_id, "source_identification", "Identify relevant websites and sources",
                         PlanningPhase.ANALYSIS, dependencies=["keyword_analysis"],
                         estimated_effort="medium", tools_needed=["search_engine"],
                         success_criteria="Sources cataloged")

            # Add planning phase steps
            self.add_step(plan_id, "scraping_strategy", "Design scraping strategy and rate limits",
                         PlanningPhase.PLANNING, dependencies=["source_identification"],
                         estimated_effort="medium", tools_needed=["strategy_planner"],
                         success_criteria="Strategy documented")

            self.add_step(plan_id, "data_structure", "Define data collection and storage structure",
                         PlanningPhase.PLANNING, dependencies=["scraping_strategy"],
                         estimated_effort="low", tools_needed=["data_modeler"],
                         success_criteria="Schema defined")

            # Add execution phase steps
            self.add_step(plan_id, "initial_scraping", "Execute initial scraping batch",
                         PlanningPhase.EXECUTION, dependencies=["data_structure"],
                         estimated_effort="high", tools_needed=["scraper", "proxy_manager"],
                         success_criteria="First batch completed")

            self.add_step(plan_id, "content_processing", "Process and classify scraped content",
                         PlanningPhase.EXECUTION, dependencies=["initial_scraping"],
                         estimated_effort="medium", tools_needed=["classifier", "nlp_processor"],
                         success_criteria="Content categorized")

            # Add validation phase steps
            self.add_step(plan_id, "quality_check", "Validate data quality and completeness",
                         PlanningPhase.VALIDATION, dependencies=["content_processing"],
                         estimated_effort="medium", tools_needed=["validator", "metrics"],
                         success_criteria="Quality metrics met")

            self.add_step(plan_id, "results_summary", "Generate final report and insights",
                         PlanningPhase.VALIDATION, dependencies=["quality_check"],
                         estimated_effort="low", tools_needed=["reporter"],
                         success_criteria="Report delivered")

        # Generate Mermaid diagram
        plan.mermaid_diagram = self.generate_mermaid_diagram(plan_id)

        return True

# Global planning system instance
planning_system = PlanningSystem()

# Example usage
async def demo_planning_system():
    """Demonstrate the planning system"""
    print("📋 Demo: Planning System for Complex Scraping Tasks")
    print("=" * REPORT_WIDTH)

    # Create a plan
    user_query = "Necesito scrapear información sobre agencias de marketing digital en Lima para identificar oportunidades de negocio"
    plan_id = planning_system.create_plan(
        "Marketing Research Campaign",
        f"Planning execution for: {user_query}"
    )

    print(f"📝 Created plan: {plan_id}")

    # Analyze requirements
    print("\n🔍 Phase 1: ANALYSIS")
    analysis = await planning_system.analyze_requirements(plan_id, user_query)
    print(f"   Data type: {analysis['data_type']}")
    print(f"   Complexity: {analysis['complexity']}")
    print(f"   Tools needed: {', '.join(analysis['required_tools'])}")

    # Generate execution plan
    print("\n📊 Phase 2: PLANNING")
    success = await planning_system.generate_execution_plan(plan_id)
    if success:
        print("   ✅ Execution plan generated")

        # Show plan status
        status = planning_system.get_plan_status(plan_id)
        if status:
            print("\n📈 Plan Overview:")
            print(f"   Total steps: {status['total_steps']}")
            print(f"   Current phase: {status['current_phase']}")
            print(f"   Progress: {status['progress']:.1f}%")

            # Show phase breakdown
            print("\n📊 Phase Breakdown:")
            for phase_name, phase_data in status['phase_stats'].items():
                print(f"   {phase_name.title()}: {phase_data['completed']}/{phase_data['total']} ({phase_data['progress']:.1f}%)")

    # Switch to ACT mode
    print("\n🚀 Switching to ACT mode for execution...")
    planning_system.switch_mode(plan_id, PlanningMode.ACT)

    # Simulate step completion
    print("\n⚡ Simulating step execution...")
    executable_steps = planning_system.get_next_executable_steps(plan_id)
    for step in executable_steps[:2]:  # Complete first 2 steps
        print(f"   ✅ Completing: {step.description}")
        planning_system.complete_step(plan_id, step.id, "Simulated result")

    # Check if we can advance phase
    if planning_system.advance_phase(plan_id):
        print("   📈 Advanced to next phase")

    # Final status
    final_status = planning_system.get_plan_status(plan_id)
    if final_status:
        print("\n🏁 Final Status:")
        print(f"   Mode: {final_status['mode']}")
        print(f"   Phase: {final_status['current_phase']}")
        print(f"   Progress: {final_status['progress']:.1f}%")
        print(f"   Completed: {final_status['completed_steps']}/{final_status['total_steps']}")

if __name__ == "__main__":
    asyncio.run(demo_planning_system())