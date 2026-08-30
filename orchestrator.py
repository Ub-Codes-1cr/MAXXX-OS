"""
MAXXX OS - Task Orchestrator
High-level task management and execution
"""

import sys
sys.stdout.reconfigure(encoding='utf-8')

from agent import HermesAgent, AgentResult
from tools import tool_registry


class TaskOrchestrator:
    def __init__(self, model: str = "hermes3:8b"):
        self.model = model
        self.agent = HermesAgent(model=model)

    def post_to_single_platform(self, content_idea: str, platform: str) -> AgentResult:
        task = f"""Post to {platform}:
Content idea: {content_idea}

Steps:
1. Check Ollama is running
2. Get platform rules for {platform}
3. Generate a post for {platform}
4. Validate the post
5. Stage the post on {platform} using browser
6. Report success"""
        
        return self.agent.run(task)

    def post_to_all_platforms(self, content_idea: str, division: str = "tech") -> dict:
        platform_map = {
            "tech": ["x", "linkedin", "github", "devto", "reddit", "hashnode", "hackernews"],
            "media": ["instagram", "youtube", "threads", "facebook", "substack"],
            "saas": ["x", "linkedin", "producthunt", "reddit"],
            "all": ["x", "linkedin", "github", "devto", "reddit", "instagram", "youtube"]
        }
        
        platforms = platform_map.get(division, platform_map["tech"])
        results = {}
        
        for platform in platforms:
            print(f"\n{'='*60}")
            print(f"Posting to: {platform.upper()}")
            print(f"{'='*60}")
            
            result = self.post_to_single_platform(content_idea, platform)
            results[platform] = result
        
        # Summary
        successful = sum(1 for r in results.values() if r.success)
        total = len(results)
        
        print(f"\n{'='*60}")
        print(f"SUMMARY: {successful}/{total} platforms posted successfully")
        print(f"{'='*60}")
        
        return results

    def quick_post(self, content_idea: str, platform: str = "x") -> AgentResult:
        task = f"Quick post to {platform}: {content_idea}"
        return self.agent.run(task)


# Global instance
orchestrator = TaskOrchestrator()


if __name__ == "__main__":
    import sys
    sys.stdout.reconfigure(encoding='utf-8')
    
    if len(sys.argv) < 2:
        print("Usage: python orchestrator.py <content_idea> [platform]")
        print("Example: python orchestrator.py 'Building MAXXX OS' x")
        sys.exit(1)
    
    content_idea = sys.argv[1]
    platform = sys.argv[2] if len(sys.argv) > 2 else "x"
    
    result = orchestrator.quick_post(content_idea, platform)
    
    print(f"\n{'='*60}")
    print(f"RESULT")
    print(f"{'='*60}")
    print(f"Success: {result.success}")
    print(f"Output: {result.output}")
    print(f"Steps taken: {len(result.steps)}")
