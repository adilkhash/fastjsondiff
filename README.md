# fastjsondiff

A high-performance Python library for comparing JSON payloads, powered by a Zig core for maximum speed.

## Features

- **Fast**: Zig-powered core delivers sub-millisecond comparisons for typical payloads
- **Complete**: Detects added, removed, and changed values with full path reporting
- **Deep**: Handles arbitrarily nested structures (objects and arrays)
- **Scalable**: Efficiently processes multi-megabyte JSON files
- **Pythonic**: Clean API with iteration, filtering, and serialization support

## Installation

```bash
pip install fastjsondiff-zig
```

Or using [uv](https://docs.astral.sh/uv/):

```bash
uv add fastjsondiff-zig
```

### Development Installation

```bash
# Clone the repository
git clone https://github.com/adilkhash/fastjsondiff.git
cd fastjsondiff

# Build the Zig core
cd fastjsondiff/_zig
zig build
cd ../..

# Install in development mode
pip install -e .

# Or using uv
uv pip install -e .
```

## Quick Start

```python
import fastjsondiff

# Compare two JSON strings
result = fastjsondiff.compare(
    '{"name": "Alice", "age": 30}',
    '{"name": "Bob", "age": 30, "city": "NYC"}'
)

# Check if there are differences
if result:
    print(f"Found {len(result)} differences")

# Iterate over differences
for diff in result:
    print(f"{diff.type.value}: {diff.path}")
    print(f"  old: {diff.old_value}")
    print(f"  new: {diff.new_value}")
```

Output:
```
Found 2 differences
changed: root.name
  old: "Alice"
  new: "Bob"
added: root.city
  old: None
  new: "NYC"
```

## API Reference

### `compare(a, b, *, array_match="index")`

Compare two JSON payloads and return their differences.

**Parameters:**
- `a`: First JSON input (string or bytes)
- `b`: Second JSON input (string or bytes)
- `array_match`: Array comparison strategy (`"index"` for position-based comparison)

**Returns:** `DiffResult` containing all differences found

**Raises:**
- `InvalidJsonError`: If either input is not valid JSON
- `TypeError`: If inputs are not string or bytes

```python
result = fastjsondiff.compare('{"a": 1}', '{"a": 2}')
```

### `compare_files(path_a, path_b, *, array_match="index", encoding="utf-8")`

Compare two JSON files.

**Parameters:**
- `path_a`: Path to first JSON file
- `path_b`: Path to second JSON file
- `array_match`: Array comparison strategy
- `encoding`: File encoding (default: utf-8)

**Returns:** `DiffResult` containing all differences found

```python
result = fastjsondiff.compare_files("old.json", "new.json")
```

### `DiffResult`

Container for comparison results.

```python
result = fastjsondiff.compare(json_a, json_b)

# Length and boolean
len(result)      # Number of differences
bool(result)     # True if any differences exist

# Iteration
for diff in result:
    print(diff.path)

# Index access
first_diff = result[0]

# Filtering
added = result.filter(DiffType.ADDED)
removed = result.filter(DiffType.REMOVED)
changed = result.filter(DiffType.CHANGED)

# Summary
result.summary.added      # Count of added items
result.summary.removed    # Count of removed items
result.summary.changed    # Count of changed items
result.summary.total      # Total differences

# Metadata
result.metadata.paths_compared  # Number of paths visited
result.metadata.max_depth       # Maximum nesting depth
result.metadata.duration_ms     # Comparison time in milliseconds

# Serialization
result.to_dict()          # Convert to dictionary
result.to_json()          # Convert to JSON string
result.to_json(indent=2)  # Pretty-printed JSON
```

### `Difference`

Represents a single difference.

```python
diff.type       # DiffType.ADDED, DiffType.REMOVED, or DiffType.CHANGED
diff.path       # JSON path (e.g., "root.users[0].name")
diff.old_value  # Previous value (None for ADDED)
diff.new_value  # New value (None for REMOVED)
diff.to_dict()  # Serialize to dictionary
```

### `DiffType`

Enum of difference types:

```python
from fastjsondiff import DiffType

DiffType.ADDED    # Key/element exists in second input only
DiffType.REMOVED  # Key/element exists in first input only
DiffType.CHANGED  # Value differs between inputs
```

## Path Format

Paths use dot notation for object keys and bracket notation for array indices:

- `root.name` - Object key
- `root.users[0]` - Array element
- `root.users[0].email` - Nested path

## Performance

Benchmarks on typical hardware:

| Payload Size | Keys | Time |
|-------------|------|------|
| 2 KB | 100 | 0.2 ms |
| 23 KB | 1,000 | 2.4 ms |
| 252 KB | 10,000 | 24 ms |
| 1.3 MB | 50,000 | 122 ms |

## Examples

### Detecting Configuration Changes

```python
import fastjsondiff

old_config = '{"debug": false, "port": 8080}'
new_config = '{"debug": true, "port": 8080, "host": "0.0.0.0"}'

result = fastjsondiff.compare(old_config, new_config)

for diff in result:
    if diff.type == fastjsondiff.DiffType.CHANGED:
        print(f"Modified: {diff.path}")
    elif diff.type == fastjsondiff.DiffType.ADDED:
        print(f"New setting: {diff.path}")
```

### Comparing API Responses

```python
import fastjsondiff
import json

response_v1 = '{"users": [{"id": 1, "name": "Alice"}]}'
response_v2 = '{"users": [{"id": 1, "name": "Alice", "email": "alice@example.com"}]}'

result = fastjsondiff.compare(response_v1, response_v2)

if result:
    print("API response changed:")
    print(result.to_json(indent=2))
```

### Filtering by Change Type

```python
import fastjsondiff
from fastjsondiff import DiffType

result = fastjsondiff.compare(old_json, new_json)

# Get only added fields
new_fields = result.filter(DiffType.ADDED)
print(f"{len(new_fields)} new fields added")

# Get only removed fields
removed_fields = result.filter(DiffType.REMOVED)
print(f"{len(removed_fields)} fields removed")
```

## Requirements

- Python 3.10+
- Zig 0.15.2 (for building from source)

## License

MIT

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Run tests (`pytest tests/`)
4. Commit your changes (`git commit -m 'Add amazing feature'`)
5. Push to the branch (`git push origin feature/amazing-feature`)
6. Open a Pull Request
