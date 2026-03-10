# Batch Generation Guide

## Overview

The `ManualTestGenerator` now supports efficient batch generation with parallel processing, progress tracking, and graceful error handling. This guide explains how to use these features effectively.

## Key Features

### 1. Parallel Processing

Process multiple requirements concurrently to significantly reduce generation time.

**Benefits:**
- Faster test generation for large requirement sets
- Configurable concurrency limit to respect API rate limits
- Automatic semaphore-based throttling

**Example:**
```python
from qa_agent.generators.manual_test_generator import ManualTestGenerator
from qa_agent.llm.client import LLMClient

# Create generator with custom concurrency
generator = ManualTestGenerator(llm_client, max_concurrent=5)

# Generate tests in parallel
artifacts = await generator.generate(
    requirements=requirements,
    include_positive=True,
    include_negative=True,
    include_edge_cases=True,
)
```

### 2. Progress Tracking

Monitor generation progress with optional callbacks.

**Benefits:**
- Real-time visibility into generation progress
- Track which requirements are being processed
- Useful for long-running operations

**Example:**
```python
def progress_callback(completed, total, requirement_id):
    percentage = (completed / total) * 100
    print(f"Progress: {completed}/{total} ({percentage:.1f}%) - {requirement_id}")

artifacts = await generator.generate(
    requirements=requirements,
    progress_callback=progress_callback,
)
```

### 3. Graceful Error Handling

Continue processing even when some requirements fail.

**Benefits:**
- Partial results instead of complete failure
- Detailed error logging for failed requirements
- Raises error only when all requirements fail

**Example:**
```python
try:
    artifacts = await generator.generate(requirements=requirements)
    print(f"Generated {len(artifacts)} test cases")
except LLMError as e:
    print(f"All requirements failed: {e}")
```

### 4. Batch Generation

Process large requirement sets in manageable batches.

**Benefits:**
- Better memory management
- Checkpoint/resume capabilities
- Rate limiting for external APIs

**Example:**
```python
def batch_callback(completed_batches, total_batches):
    print(f"Batch {completed_batches}/{total_batches} complete")

artifacts = await generator.generate_batch(
    requirements=requirements,
    batch_size=10,
    progress_callback=batch_callback,
)
```

## API Reference

### ManualTestGenerator.__init__

```python
def __init__(self, llm_client: LLMClient, max_concurrent: int = 5)
```

**Parameters:**
- `llm_client`: LLM client for generating test cases
- `max_concurrent`: Maximum number of concurrent LLM requests (default: 5)

**Example:**
```python
# Default concurrency (5)
generator = ManualTestGenerator(llm_client)

# Custom concurrency
generator = ManualTestGenerator(llm_client, max_concurrent=10)
```

### ManualTestGenerator.generate

```python
async def generate(
    self,
    requirements: List[Requirement],
    include_positive: bool = True,
    include_negative: bool = True,
    include_edge_cases: bool = True,
    progress_callback: Optional[Callable[[int, int, str], None]] = None,
) -> List[TestArtifact]
```

**Parameters:**
- `requirements`: List of requirements to generate tests for
- `include_positive`: Whether to generate positive test scenarios (default: True)
- `include_negative`: Whether to generate negative test scenarios (default: True)
- `include_edge_cases`: Whether to generate edge case scenarios (default: True)
- `progress_callback`: Optional callback function(completed, total, requirement_id)

**Returns:**
- List of generated test artifacts

**Raises:**
- `LLMError`: If test generation fails for all requirements

**Example:**
```python
artifacts = await generator.generate(
    requirements=requirements,
    include_positive=True,
    include_negative=True,
    include_edge_cases=True,
    progress_callback=lambda c, t, r: print(f"{c}/{t}: {r}"),
)
```

### ManualTestGenerator.generate_batch

```python
async def generate_batch(
    self,
    requirements: List[Requirement],
    batch_size: int = 10,
    include_positive: bool = True,
    include_negative: bool = True,
    include_edge_cases: bool = True,
    progress_callback: Optional[Callable[[int, int], None]] = None,
) -> List[TestArtifact]
```

**Parameters:**
- `requirements`: List of requirements to generate tests for
- `batch_size`: Number of requirements to process per batch (default: 10)
- `include_positive`: Whether to generate positive test scenarios (default: True)
- `include_negative`: Whether to generate negative test scenarios (default: True)
- `include_edge_cases`: Whether to generate edge case scenarios (default: True)
- `progress_callback`: Optional callback function(completed_batches, total_batches)

**Returns:**
- List of generated test artifacts

**Raises:**
- `LLMError`: If test generation fails for all requirements

**Example:**
```python
artifacts = await generator.generate_batch(
    requirements=requirements,
    batch_size=5,
    progress_callback=lambda c, t: print(f"Batch {c}/{t}"),
)
```

## Best Practices

### 1. Choosing Concurrency Level

**Considerations:**
- API rate limits (e.g., OpenAI has rate limits per minute)
- Available memory
- Network bandwidth
- Cost considerations (parallel requests = faster but same cost)

**Recommendations:**
```python
# For OpenAI free tier
generator = ManualTestGenerator(llm_client, max_concurrent=3)

# For OpenAI paid tier
generator = ManualTestGenerator(llm_client, max_concurrent=10)

# For local LLM (no rate limits)
generator = ManualTestGenerator(llm_client, max_concurrent=20)
```

### 2. Choosing Batch Size

**Considerations:**
- Total number of requirements
- Memory constraints
- Checkpoint frequency needs

**Recommendations:**
```python
# Small sets (< 50 requirements)
# Use generate() directly, no batching needed

# Medium sets (50-200 requirements)
artifacts = await generator.generate_batch(
    requirements=requirements,
    batch_size=25,
)

# Large sets (> 200 requirements)
artifacts = await generator.generate_batch(
    requirements=requirements,
    batch_size=50,
)
```

### 3. Progress Tracking

**Simple Progress Bar:**
```python
def progress_callback(completed, total, req_id):
    bar_length = 40
    filled = int(bar_length * completed / total)
    bar = '█' * filled + '░' * (bar_length - filled)
    print(f'\r[{bar}] {completed}/{total} {req_id}', end='', flush=True)

artifacts = await generator.generate(
    requirements=requirements,
    progress_callback=progress_callback,
)
print()  # New line after completion
```

**Rich Progress Display:**
```python
from rich.progress import Progress

with Progress() as progress:
    task = progress.add_task("[cyan]Generating tests...", total=len(requirements))
    
    def progress_callback(completed, total, req_id):
        progress.update(task, completed=completed, description=f"[cyan]{req_id}")
    
    artifacts = await generator.generate(
        requirements=requirements,
        progress_callback=progress_callback,
    )
```

### 4. Error Handling

**Partial Failure Handling:**
```python
import logging

logger = logging.getLogger(__name__)

try:
    artifacts = await generator.generate(requirements=requirements)
    
    success_rate = len(artifacts) / (len(requirements) * 3)  # 3 test types
    
    if success_rate < 0.8:
        logger.warning(f"Low success rate: {success_rate:.1%}")
    
    logger.info(f"Generated {len(artifacts)} test cases")
    
except LLMError as e:
    logger.error(f"Complete failure: {e}")
    # Implement retry logic or fallback
```

**Retry Logic:**
```python
async def generate_with_retry(generator, requirements, max_retries=3):
    for attempt in range(max_retries):
        try:
            return await generator.generate(requirements=requirements)
        except LLMError as e:
            if attempt == max_retries - 1:
                raise
            logger.warning(f"Attempt {attempt + 1} failed, retrying...")
            await asyncio.sleep(2 ** attempt)  # Exponential backoff
```

## Performance Optimization

### 1. Optimal Concurrency

Test different concurrency levels to find the optimal setting:

```python
import time

async def benchmark_concurrency(requirements, concurrency_levels):
    results = {}
    
    for max_concurrent in concurrency_levels:
        generator = ManualTestGenerator(llm_client, max_concurrent=max_concurrent)
        
        start = time.time()
        artifacts = await generator.generate(requirements=requirements)
        duration = time.time() - start
        
        results[max_concurrent] = {
            'duration': duration,
            'throughput': len(artifacts) / duration,
        }
    
    return results

# Test with different levels
results = await benchmark_concurrency(
    requirements=requirements[:10],
    concurrency_levels=[1, 3, 5, 10],
)

# Find optimal
optimal = max(results.items(), key=lambda x: x[1]['throughput'])
print(f"Optimal concurrency: {optimal[0]} ({optimal[1]['throughput']:.2f} tests/sec)")
```

### 2. Memory Management

For very large requirement sets, use batch generation:

```python
# Process 1000 requirements in batches of 50
artifacts = await generator.generate_batch(
    requirements=large_requirements,
    batch_size=50,
)

# This prevents memory issues and allows for checkpointing
```

### 3. Caching

Implement caching to avoid regenerating tests:

```python
import hashlib
import json
from pathlib import Path

def get_cache_key(requirement: Requirement) -> str:
    """Generate cache key for requirement."""
    content = json.dumps({
        'id': requirement.id,
        'content': requirement.content,
        'type': requirement.type.value,
    }, sort_keys=True)
    return hashlib.sha256(content.encode()).hexdigest()

async def generate_with_cache(generator, requirements, cache_dir='./cache'):
    cache_path = Path(cache_dir)
    cache_path.mkdir(exist_ok=True)
    
    all_artifacts = []
    uncached_requirements = []
    
    # Check cache
    for req in requirements:
        cache_key = get_cache_key(req)
        cache_file = cache_path / f"{cache_key}.json"
        
        if cache_file.exists():
            # Load from cache
            with open(cache_file) as f:
                cached_data = json.load(f)
                # Convert back to TestArtifact objects
                all_artifacts.extend(cached_data)
        else:
            uncached_requirements.append(req)
    
    # Generate for uncached requirements
    if uncached_requirements:
        new_artifacts = await generator.generate(requirements=uncached_requirements)
        
        # Save to cache
        for artifact in new_artifacts:
            req_id = artifact.requirement_ids[0]
            req = next(r for r in uncached_requirements if r.id == req_id)
            cache_key = get_cache_key(req)
            cache_file = cache_path / f"{cache_key}.json"
            
            with open(cache_file, 'w') as f:
                json.dump([artifact.dict()], f)
        
        all_artifacts.extend(new_artifacts)
    
    return all_artifacts
```

## Troubleshooting

### Issue: Rate Limit Errors

**Symptom:** Frequent API rate limit errors

**Solution:**
```python
# Reduce concurrency
generator = ManualTestGenerator(llm_client, max_concurrent=2)

# Or use batch generation with delays
async def generate_with_delays(generator, requirements, batch_size=5, delay=1.0):
    all_artifacts = []
    
    for i in range(0, len(requirements), batch_size):
        batch = requirements[i:i + batch_size]
        artifacts = await generator.generate(requirements=batch)
        all_artifacts.extend(artifacts)
        
        if i + batch_size < len(requirements):
            await asyncio.sleep(delay)
    
    return all_artifacts
```

### Issue: Memory Issues

**Symptom:** Out of memory errors with large requirement sets

**Solution:**
```python
# Use batch generation
artifacts = await generator.generate_batch(
    requirements=requirements,
    batch_size=20,  # Smaller batches
)

# Or process in chunks and save incrementally
async def generate_and_save(generator, requirements, output_dir, chunk_size=50):
    output_path = Path(output_dir)
    output_path.mkdir(exist_ok=True)
    
    for i in range(0, len(requirements), chunk_size):
        chunk = requirements[i:i + chunk_size]
        artifacts = await generator.generate(requirements=chunk)
        
        # Save chunk
        chunk_file = output_path / f"chunk_{i // chunk_size}.json"
        with open(chunk_file, 'w') as f:
            json.dump([a.dict() for a in artifacts], f)
```

### Issue: Slow Generation

**Symptom:** Generation takes too long

**Solution:**
```python
# Increase concurrency (if rate limits allow)
generator = ManualTestGenerator(llm_client, max_concurrent=10)

# Reduce test types
artifacts = await generator.generate(
    requirements=requirements,
    include_positive=True,
    include_negative=False,  # Skip negative tests
    include_edge_cases=False,  # Skip edge cases
)

# Use faster model
ai_config = AIConfig(
    provider="openai",
    model="gpt-3.5-turbo",  # Faster than gpt-4
    temperature=0.7,
)
```

## Examples

See `examples/batch_generation_example.py` for complete working examples demonstrating:
- Parallel generation with progress tracking
- Batch generation for large requirement sets
- Graceful handling of partial failures
- Custom concurrency configuration

## Migration Guide

### From Sequential to Parallel

**Before:**
```python
generator = ManualTestGenerator(llm_client)
artifacts = await generator.generate(requirements=requirements)
```

**After:**
```python
# Same API, now parallel by default!
generator = ManualTestGenerator(llm_client, max_concurrent=5)
artifacts = await generator.generate(requirements=requirements)
```

### Adding Progress Tracking

**Before:**
```python
artifacts = await generator.generate(requirements=requirements)
```

**After:**
```python
def progress_callback(completed, total, req_id):
    print(f"Progress: {completed}/{total}")

artifacts = await generator.generate(
    requirements=requirements,
    progress_callback=progress_callback,
)
```

### Using Batch Generation

**Before:**
```python
# Process all at once
artifacts = await generator.generate(requirements=large_requirements)
```

**After:**
```python
# Process in batches
artifacts = await generator.generate_batch(
    requirements=large_requirements,
    batch_size=25,
)
```

## Summary

The batch generation feature provides:
- **Parallel processing** for faster generation
- **Progress tracking** for visibility
- **Graceful error handling** for reliability
- **Batch processing** for scalability

These features make the `ManualTestGenerator` production-ready for large-scale test generation workflows.
