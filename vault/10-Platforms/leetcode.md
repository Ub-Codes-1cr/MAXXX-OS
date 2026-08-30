# LeetCode Platform Rules

## Division: Tech

## Content Types
- Problem solutions
- Approach explanations
- Algorithm breakdowns

## Golden Rules
1. **Must include Time and Space Complexity (Big O) notes**
2. **Code must be heavily commented explaining the algorithmic logic**

## Solution Structure
```python
class Solution:
    def twoSum(self, nums: List[int], target: int) -> List[int]:
        # Time Complexity: O(n)
        # Space Complexity: O(n)
        # Approach: Hash map for O(1) lookups
        
        seen = {}  # value -> index
        for i, num in enumerate(nums):
            complement = target - num
            if complement in seen:
                return [seen[complement], i]
            seen[num] = i
        return []
```

## Anti-Patterns
- No uncommented code
- No missing complexity analysis
- No copy-paste without understanding

## Best Practices
- Explain your thought process
- Include multiple approaches if relevant
- Discuss edge cases
- Use clear variable names
