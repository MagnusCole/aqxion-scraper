#!/usr/bin/env python3
"""
Demo script showing complete task execution with dependencies
"""

import asyncio
import sys
import os

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from task_manager import task_manager, create_example_task

async def demo_task_execution():
    """Demonstrate complete task execution with dependencies"""

    print("🎯 Demo: Sistema de Gestión de Tareas para Aqxion Scraper")
    print("=" * 60)

    # Create example task
    task_id = create_example_task()
    print(f"📋 Task created: {task_id}")

    # Define step functions
    async def analyze_keywords():
        print("🔍 Analyzing keywords...")
        await asyncio.sleep(1)
        return {"keywords": ["limpieza de piscina lima", "agencia marketing lima", "dashboard pymes peru"]}

    async def config_limpieza():
        print("⚙️ Configuring scraping for 'limpieza de piscina lima'...")
        await asyncio.sleep(0.5)
        return {"keyword": "limpieza de piscina lima", "search_engines": ["google", "bing"]}

    async def config_marketing():
        print("⚙️ Configuring scraping for 'agencia marketing lima'...")
        await asyncio.sleep(0.5)
        return {"keyword": "agencia marketing lima", "search_engines": ["google", "bing"]}

    async def config_dashboard():
        print("⚙️ Configuring scraping for 'dashboard pymes peru'...")
        await asyncio.sleep(0.5)
        return {"keyword": "dashboard pymes peru", "search_engines": ["google", "bing"]}

    async def scrape_limpieza():
        print("🕷️ Scraping 'limpieza de piscina lima'...")
        await asyncio.sleep(2)
        return {"results": 25, "success": True}

    async def scrape_marketing():
        print("🕷️ Scraping 'agencia marketing lima'...")
        await asyncio.sleep(2)
        return {"results": 30, "success": True}

    async def scrape_dashboard():
        print("🕷️ Scraping 'dashboard pymes peru'...")
        await asyncio.sleep(2)
        return {"results": 15, "success": True}

    async def validate_results():
        print("✅ Validating all scraping results...")
        await asyncio.sleep(1)
        return {"total_results": 70, "quality_score": 85, "success": True}

    # Map step functions
    step_functions = {
        "analyze_keywords": analyze_keywords,
        "config_limpieza_piscina": config_limpieza,
        "config_marketing_agencia": config_marketing,
        "config_dashboard_pymes": config_dashboard,
        "scrape_limpieza": scrape_limpieza,
        "scrape_marketing": scrape_marketing,
        "scrape_dashboard": scrape_dashboard,
        "validate_results": validate_results
    }

    # Progress callback
    async def progress_callback(task_id, step_id, status, result):
        print(f"📊 Progress: {step_id} -> {status.value}")
        if result:
            print(f"   Result: {result}")

    # Set progress callback
    task_manager.tasks[task_id].progress_callback = progress_callback

    # Execute the task
    print("\n🚀 Starting task execution...")
    print("-" * 40)

    start_time = asyncio.get_event_loop().time()
    success = await task_manager.execute_task(task_id, step_functions)
    end_time = asyncio.get_event_loop().time()

    print(f"\n⏱️ Total execution time: {end_time - start_time:.2f} seconds")

    # Show final status
    final_status = task_manager.get_task_status(task_id)

    if final_status:
        print("\n📈 Final Status:")
        print(f"   Status: {final_status['status']}")
        print(f"   Progress: {final_status['progress']:.1f}%")
        print(f"   Completed: {final_status['completed_steps']}/{final_status['total_steps']}")
        print(f"   Failed: {final_status['failed_steps']}")
    else:
        print("\n❌ Could not retrieve final task status")

    if success:
        print("\n🎉 Task completed successfully!")
        print("✅ All dependencies respected")
        print("✅ Parallel execution where possible")
        print("✅ Error handling and recovery")
    else:
        print("\n❌ Task execution failed")

    return success

async def main():
    """Main demo function"""
    try:
        success = await demo_task_execution()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n⏹️ Demo interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 Demo failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
