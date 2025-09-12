"""
Task Management System for Aqxion Scraper
Based on Manus and Devin AI task management patterns
"""

import asyncio
import json
import time
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum

class TaskStatus(Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class TaskPriority(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

@dataclass
class TaskStep:
    """Individual step within a task"""
    id: str
    description: str
    status: TaskStatus = TaskStatus.PENDING
    dependencies: List[str] = field(default_factory=list)
    estimated_duration: Optional[int] = None  # in seconds
    actual_duration: Optional[int] = None
    result: Optional[Any] = None
    error: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

@dataclass
class ScrapingTask:
    """Main task for scraping operations"""
    id: str
    title: str
    description: str
    priority: TaskPriority = TaskPriority.MEDIUM
    status: TaskStatus = TaskStatus.PENDING
    steps: List[TaskStep] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)
    progress_callback: Optional[Callable] = None

class TaskManager:
    """Manages complex scraping tasks with dependencies and progress tracking"""

    def __init__(self):
        self.tasks: Dict[str, ScrapingTask] = {}
        self.active_tasks: Dict[str, asyncio.Task] = {}

    def create_task(self, title: str, description: str, priority: TaskPriority = TaskPriority.MEDIUM) -> str:
        """Create a new scraping task"""
        task_id = f"task_{int(time.time())}_{len(self.tasks)}"
        task = ScrapingTask(
            id=task_id,
            title=title,
            description=description,
            priority=priority
        )
        self.tasks[task_id] = task
        return task_id

    def add_step(self, task_id: str, step_id: str, description: str,
                 dependencies: Optional[List[str]] = None, estimated_duration: Optional[int] = None) -> bool:
        """Add a step to an existing task"""
        if task_id not in self.tasks:
            return False

        step = TaskStep(
            id=step_id,
            description=description,
            dependencies=dependencies or [],
            estimated_duration=estimated_duration
        )

        self.tasks[task_id].steps.append(step)
        self.tasks[task_id].updated_at = datetime.now()
        return True

    def get_next_executable_steps(self, task_id: str) -> List[TaskStep]:
        """Get steps that can be executed (all dependencies completed)"""
        if task_id not in self.tasks:
            return []

        task = self.tasks[task_id]
        completed_step_ids = {step.id for step in task.steps if step.status == TaskStatus.COMPLETED}

        executable_steps = []
        for step in task.steps:
            if step.status == TaskStatus.PENDING:
                # Check if all dependencies are completed
                if all(dep in completed_step_ids for dep in step.dependencies):
                    executable_steps.append(step)

        return executable_steps

    async def execute_step(self, task_id: str, step_id: str, step_function: Callable) -> bool:
        """Execute a specific step with error handling"""
        if task_id not in self.tasks:
            return False

        task = self.tasks[task_id]
        step = next((s for s in task.steps if s.id == step_id), None)

        if not step or step.status != TaskStatus.PENDING:
            return False

        # Update step status
        step.status = TaskStatus.IN_PROGRESS
        step.started_at = datetime.now()
        task.updated_at = datetime.now()

        try:
            # Execute the step function
            result = await step_function()

            # Mark as completed
            step.status = TaskStatus.COMPLETED
            step.result = result
            step.completed_at = datetime.now()
            step.actual_duration = int((step.completed_at - step.started_at).total_seconds())

            # Notify progress if callback exists
            if task.progress_callback:
                await task.progress_callback(task_id, step_id, TaskStatus.COMPLETED, result)

            return True

        except Exception as e:
            # Mark as failed
            step.status = TaskStatus.FAILED
            step.error = str(e)
            step.completed_at = datetime.now()
            step.actual_duration = int((step.completed_at - step.started_at).total_seconds())

            # Notify progress if callback exists
            if task.progress_callback:
                await task.progress_callback(task_id, step_id, TaskStatus.FAILED, str(e))

            return False

    async def execute_task(self, task_id: str, step_functions: Dict[str, Callable]) -> bool:
        """Execute a complete task with all its steps"""
        if task_id not in self.tasks:
            return False

        task = self.tasks[task_id]
        task.status = TaskStatus.IN_PROGRESS

        print(f"🚀 Starting task: {task.title}")
        print(f"📝 Description: {task.description}")

        while True:
            # Get next executable steps
            executable_steps = self.get_next_executable_steps(task_id)

            if not executable_steps:
                # Check if all steps are completed
                all_completed = all(step.status == TaskStatus.COMPLETED for step in task.steps)
                if all_completed:
                    task.status = TaskStatus.COMPLETED
                    print(f"✅ Task completed: {task.title}")
                    return True
                else:
                    # Check for failed steps
                    failed_steps = [s for s in task.steps if s.status == TaskStatus.FAILED]
                    if failed_steps:
                        task.status = TaskStatus.FAILED
                        print(f"❌ Task failed: {task.title}")
                        return False
                    else:
                        # Deadlock - no steps can be executed but not all are complete
                        print(f"⚠️ Task deadlock detected: {task.title}")
                        return False

            # Execute steps (in parallel if no conflicts)
            execution_tasks = []
            for step in executable_steps:
                if step.id in step_functions:
                    execution_tasks.append(self.execute_step(task_id, step.id, step_functions[step.id]))

            if execution_tasks:
                await asyncio.gather(*execution_tasks)

            # Small delay to prevent tight loops
            await asyncio.sleep(0.1)

    def get_task_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Get detailed status of a task"""
        if task_id not in self.tasks:
            return None

        task = self.tasks[task_id]

        total_steps = len(task.steps)
        completed_steps = len([s for s in task.steps if s.status == TaskStatus.COMPLETED])
        failed_steps = len([s for s in task.steps if s.status == TaskStatus.FAILED])

        progress = (completed_steps / total_steps * 100) if total_steps > 0 else 0

        return {
            "id": task.id,
            "title": task.title,
            "description": task.description,
            "status": task.status.value,
            "priority": task.priority.value,
            "progress": progress,
            "total_steps": total_steps,
            "completed_steps": completed_steps,
            "failed_steps": failed_steps,
            "created_at": task.created_at.isoformat(),
            "updated_at": task.updated_at.isoformat(),
            "steps": [
                {
                    "id": step.id,
                    "description": step.description,
                    "status": step.status.value,
                    "dependencies": step.dependencies,
                    "estimated_duration": step.estimated_duration,
                    "actual_duration": step.actual_duration,
                    "error": step.error
                }
                for step in task.steps
            ]
        }

    def cancel_task(self, task_id: str) -> bool:
        """Cancel a running task"""
        if task_id not in self.tasks:
            return False

        task = self.tasks[task_id]
        if task.status == TaskStatus.IN_PROGRESS:
            task.status = TaskStatus.CANCELLED
            for step in task.steps:
                if step.status == TaskStatus.IN_PROGRESS:
                    step.status = TaskStatus.CANCELLED
            task.updated_at = datetime.now()
            return True

        return False

# Global task manager instance
task_manager = TaskManager()

# Example usage functions for scraping tasks
async def analyze_keywords(keywords: List[str]) -> Dict[str, Any]:
    """Analyze keywords for scraping task"""
    print(f"🔍 Analyzing {len(keywords)} keywords...")
    await asyncio.sleep(1)  # Simulate work
    return {"analyzed": len(keywords), "valid": len(keywords)}

async def configure_scraping(keyword: str) -> Dict[str, Any]:
    """Configure scraping for a specific keyword"""
    print(f"⚙️ Configuring scraping for: {keyword}")
    await asyncio.sleep(0.5)  # Simulate work
    return {"keyword": keyword, "config": "ready"}

async def execute_scraping(config: Dict[str, Any]) -> Dict[str, Any]:
    """Execute the actual scraping"""
    keyword = config["keyword"]
    print(f"🕷️ Scraping data for: {keyword}")
    await asyncio.sleep(2)  # Simulate work
    return {"keyword": keyword, "results": 25, "success": True}

async def validate_results(results: Dict[str, Any]) -> Dict[str, Any]:
    """Validate scraping results"""
    print(f"✅ Validating results for: {results['keyword']}")
    await asyncio.sleep(0.5)  # Simulate work
    return {"validated": results["results"], "quality_score": 85}

def create_example_task() -> str:
    """Create an example scraping task with dependencies"""
    task_id = task_manager.create_task(
        "Scraping Campaign: Marketing Digital Perú",
        "Complete scraping workflow for marketing digital keywords in Perú"
    )

    # Add steps with dependencies
    task_manager.add_step(task_id, "analyze_keywords",
                         "Analyze and validate target keywords",
                         estimated_duration=30)

    task_manager.add_step(task_id, "config_limpieza_piscina",
                         "Configure scraping for 'limpieza de piscina lima'",
                         dependencies=["analyze_keywords"],
                         estimated_duration=15)

    task_manager.add_step(task_id, "config_marketing_agencia",
                         "Configure scraping for 'agencia marketing lima'",
                         dependencies=["analyze_keywords"],
                         estimated_duration=15)

    task_manager.add_step(task_id, "config_dashboard_pymes",
                         "Configure scraping for 'dashboard pymes peru'",
                         dependencies=["analyze_keywords"],
                         estimated_duration=15)

    task_manager.add_step(task_id, "scrape_limpieza",
                         "Execute scraping for piscina cleaning services",
                         dependencies=["config_limpieza_piscina"],
                         estimated_duration=120)

    task_manager.add_step(task_id, "scrape_marketing",
                         "Execute scraping for marketing agencies",
                         dependencies=["config_marketing_agencia"],
                         estimated_duration=120)

    task_manager.add_step(task_id, "scrape_dashboard",
                         "Execute scraping for business dashboards",
                         dependencies=["config_dashboard_pymes"],
                         estimated_duration=120)

    task_manager.add_step(task_id, "validate_results",
                         "Validate and quality-check all scraping results",
                         dependencies=["scrape_limpieza", "scrape_marketing", "scrape_dashboard"],
                         estimated_duration=45)

    return task_id

if __name__ == "__main__":
    # Example usage
    task_id = create_example_task()
    status = task_manager.get_task_status(task_id)
    print(json.dumps(status, indent=2, default=str))
