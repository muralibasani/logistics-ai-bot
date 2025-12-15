# Quick Start Guide for Performance Benchmarks

## Installation

1. Install the required dependency:
```bash
cd backend
pip install aiohttp
# or
uv pip install aiohttp
```

## Running Benchmarks

**Important:** All benchmark scripts should be run from the `backend` directory:

```bash
cd backend
python benchmarks/performance_test.py --concurrency 10 --requests 50
```

### Comprehensive Performance Test

Test API endpoints, Kafka throughput, and overall system performance:

```bash
cd backend

# Quick test: 10 concurrent API requests, 50 Kafka messages
python benchmarks/performance_test.py --concurrency 10 --requests 50 --kafka-messages 50

# Full benchmark suite (multiple scenarios)
python benchmarks/performance_test.py --suite

# API only (skip Kafka)
python benchmarks/performance_test.py --concurrency 10 --requests 100 --no-kafka
```

**What it measures:**
- **API Performance:**
  - Requests per second (RPS)
  - Response time (avg, median, P95, P99)
  - Error rate
- **Kafka Performance:**
  - Messages per second
  - Produce latency
  - Message size statistics
- **Overall System:**
  - Combined throughput (API + Kafka operations per second)

## Prerequisites

Before running benchmarks, ensure:

1. **API Server is Running:**
   ```bash
   cd backend
   uvicorn api:app --reload
   ```

2. **Kafka is Running** (optional - use `--no-kafka` to skip Kafka tests)

## Example Output

```
🚀 COMPREHENSIVE PERFORMANCE BENCHMARK
================================================================================

📊 Test Configuration:
   API URL:              http://localhost:8000
   API Requests:         100 (concurrency: 10)
   Kafka Messages:       100
   Questions pool:       10 questions

📡 Running API Performance Test...
   API: Completed 100/100 requests...
✅ API test complete: 100 requests in 8.50s

📤 Running Kafka Performance Test...
   Kafka: Produced 100/100 messages...
✅ Kafka test complete: 100 messages in 2.00s

⏱️  Total test duration: 10.50s

================================================================================
📊 COMPREHENSIVE PERFORMANCE BENCHMARK RESULTS
================================================================================

📡 API PERFORMANCE:
   Total Requests:      100
   Successful:          14
   Failed:              86
   Requests/Second:     11.91
   Error Rate:          86.00%

   Response Times (seconds):
      Average:          0.507s
      Median:           0.002s
      Min:              0.001s
      Max:              5.028s
      P95:               2.834s
      P99:               5.028s

   Status Code Distribution:
      0: 86 (86.0%)
      200: 14 (14.0%)

📤 KAFKA PERFORMANCE:
   Total Operations:     100
   Successful:          100
   Failed:              0
   Operations/Second:   11.91
   Error Rate:          0.00%

   Latency (seconds):
      Average:          0.003s
      Median:           0.000s
      Min:              0.000s
      Max:              0.304s
      P95:               0.000s
      P99:               0.304s

   Message Statistics:
      Avg Message Size: 183 bytes
      Total Bytes:      18,310 bytes

🚀 OVERALL SYSTEM PERFORMANCE:
   Total Test Duration:  8.40s
   Overall Throughput:   23.82 ops/sec
   (Combined API + Kafka operations per second)
================================================================================
```

## Interpreting Results

- **Good Performance:**
  - Response time < 1s
  - Error rate < 1%
  - RPS > 10

- **Needs Attention:**
  - Response time > 2s
  - Error rate > 5%
  - P99 latency > 3x average

## Tips

1. **Warm-up**: Run a few requests before benchmarking
2. **Multiple Runs**: Run 3-5 times and average results
3. **Isolated Environment**: Run on dedicated hardware
4. **Monitor Resources**: Watch CPU/memory during tests

