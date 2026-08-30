"""
MAXXX OS - Hermes Agent
ReAct-style agent that uses Hermes for thinking and tools for execution
"""

import sys
sys.stdout.reconfigure(encoding='utf-8')

import json
import re
from typing import Optional
from dataclasses import dataclass, field

from ollama_client import ollama
from tools import tool_registry, ToolResult


@dataclass
class AgentStep:
    thought: str
    action: str
    action_input: dict
    observation: str


@dataclass
class AgentResult:
    success: bool
    output: str
    steps: list[AgentStep] = field(default_factory=list)


class HermesAgent:
    def __init__(self, model: str = "hermes3:8b", max_steps: int = 10):
        self.model = model
        self.max_steps = max_steps
        self.tools = tool_registry

    def _build_system_prompt(self) -> str:
        tool_descriptions = self.tools.get_tool_descriptions()
        
        return f"""You are MAXXX OS, an autonomous AI agent that manages social media posting.

You have access to these tools:
{tool_descriptions}

To use a tool, respond with EXACTLY this JSON format (nothing else):
{{"action": "tool_name", "action_input": {{"param1": "value1", "param2": "value2"}}}}

When the task is complete, respond with:
{{"action": "DONE", "action_input": {{"result": "summary of what was done"}}}}

If you need information before acting, respond with:
{{"action": "think", "action_input": {{"thought": "what you need to figure out"}}}}

RULES:
1. Always respond with valid JSON
2. Only use the tools listed above
3. One tool call per response
4. After each tool execution, you'll see the result
5. Keep going until the task is done
6. If a tool fails, try an alternative approach"""

    def _parse_response(self, response: str) -> dict:
        # Try to extract JSON from response
        json_match = re.search(r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}', response, re.DOTALL)
        
        if json_match:
            try:
                return json.loads(json_match.group())
            except json.JSONDecodeError:
                pass
        
        # Fallback: try to parse the whole response as JSON
        try:
            return json.loads(response)
        except json.JSONDecodeError:
            pass
        
        # Last resort: check for DONE
        if "DONE" in response.upper():
            return {"action": "DONE", "action_input": {"result": "Task completed"}}
        
        # Default: treat as a thought
        return {"action": "think", "action_input": {"thought": response}}

    def _execute_tool(self, action: str, action_input: dict) -> ToolResult:
        # Handle special actions
        if action == "think":
            return ToolResult(
                success=True,
                output=action_input.get("thought", "Thinking...")
            )
        
        if action == "DONE":
            return ToolResult(
                success=True,
                output=action_input.get("result", "Task completed")
            )
        
        # Execute the actual tool
        return self.tools.execute(action, **action_input)

    def run(self, task: str) -> AgentResult:
        print(f"\n{'='*60}")
        print(f"HERMES AGENT - Starting task")
        print(f"{'='*60}")
        print(f"Task: {task}\n")
        
        # Check if Ollama is available
        if not ollama.is_available():
            return AgentResult(
                success=False,
                output="Ollama is not running. Please start Ollama first."
            )
        
        # Initialize conversation
        system_prompt = self._build_system_prompt()
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": task}
        ]
        
        steps = []
        
        for step_num in range(1, self.max_steps + 1):
            print(f"--- Step {step_num} ---")
            
            # Get response from Hermes
            response = ollama.generate(
                prompt=messages[-1]["content"],
                model=self.model,
                system=system_prompt,
                temperature=0.2,
                max_tokens=1000
            )
            
            response_text = response.response
            print(f"Agent: {response_text[:200]}...")
            
            # Parse the response
            parsed = self._parse_response(response_text)
            action = parsed.get("action", "think")
            action_input = parsed.get("action_input", {})
            
            # Execute the action
            print(f"Action: {action}")
            if action not in ["think", "DONE"]:
                print(f"Input: {action_input}")
            
            result = self._execute_tool(action, action_input)
            
            # Record the step
            step = AgentStep(
                thought=response_text if action == "think" else "",
                action=action,
                action_input=action_input,
                observation=result.output
            )
            steps.append(step)
            
            print(f"Result: {result.output[:200]}...")
            print()
            
            # Check if done
            if action == "DONE":
                return AgentResult(
                    success=True,
                    output=result.output,
                    steps=steps
                )
            
            # Feed result back to conversation
            messages.append({"role": "assistant", "content": response_text})
            messages.append({"role": "user", "content": f"Tool result: {result.output}"})
        
        # Max steps reached
        return AgentResult(
            success=False,
            output=f"Agent reached max steps ({self.max_steps}) without completing task",
            steps=steps
        )


# Convenience function
def run_agent(task: str, model: str = "hermes3:8b", max_steps: int = 10) -> AgentResult:
    agent = HermesAgent(model=model, max_steps=max_steps)
    return agent.run(task)
