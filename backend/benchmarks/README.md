# Performance Benchmarking Suite

This directory contains performance benchmarking scripts for the Logistics AI Chatbot system.

## Available Benchmarks

### Comprehensive Performance Test (`performance_test.py`)
Tests API endpoints, Kafka throughput, and overall system performance in a single unified test.

**Metrics:**
- **API Performance:**
  - Requests per second (RPS)
  - Response time (avg, median, min, max, P95, P99)
  - Error rate
  - Status code distribution
- **Kafka Performance:**
  - Messages per second
  - Produce latency
  - Message size statistics
  - Error rate
- **Overall System:**
  - Combined throughput (API + Kafka operations per second)
  - Total test duration

**Usage:**
```bash
cd backend

# Run single test with default settings
python benchmarks/performance_test.py --concurrency 10 --requests 100 --kafka-messages 100

# Run full benchmark suite (multiple scenarios)
python benchmarks/performance_test.py --suite

# Skip Kafka tests (API only)
python benchmarks/performance_test.py --concurrency 10 --requests 100 --no-kafka

# Custom API URL and more Kafka messages
python benchmarks/performance_test.py --url http://localhost:8000 --concurrency 20 --requests 200 --kafka-messages 200
```

## Prerequisites

1. **Run from Backend Directory**: All benchmark scripts must be run from the `backend` directory:
   ```bash
   cd backend
   python benchmarks/performance_test.py
   ```

2. **API Server Running**: The FastAPI server must be running on `http://localhost:8000`

3. **Dependencies**: Install additional dependencies:
   ```bash
   pip install aiohttp
   ```

4. **Kafka**: Kafka must be running and accessible (optional - use `--no-kafka` to skip Kafka tests)

## Example Output

### Comprehensive Performance Test
```
================================================================================
📊 COMPREHENSIVE PERFORMANCE BENCHMARK RESULTS
================================================================================

📡 API PERFORMANCE:
   Total Requests:      100
   Successful:          100
   Failed:              0
   Requests/Second:     1.71
   Error Rate:          0.00%

   Response Times (seconds):
      Average:          5.351s
      Median:           5.229s
      Min:              0.919s
      Max:              9.484s
      P95:               6.559s
      P99:               9.484s

   Status Code Distribution:
      200: 100 (100.0%)

📤 KAFKA PERFORMANCE:
   Total Operations:     100
   Successful:          100
   Failed:              0
   Operations/Second:   1.71
   Error Rate:          0.00%

   Latency (seconds):
      Average:          0.004s
      Median:           0.000s
      Min:              0.000s
      Max:              0.342s
      P95:               0.000s
      P99:               0.342s

   Message Statistics:
      Avg Message Size: 183 bytes
      Total Bytes:      18,310 bytes

🚀 OVERALL SYSTEM PERFORMANCE:
   Total Test Duration:  58.31s
   Overall Throughput:   3.43 ops/sec
   (Combined API + Kafka operations per second)
================================================================================

```

## Benchmark Scenarios

### Light Load
- Concurrency: 5
- Total Requests: 50
- Use case: Baseline performance

### Medium Load
- Concurrency: 10
- Total Requests: 100
- Use case: Normal operation

### High Load
- Concurrency: 20
- Total Requests: 200
- Use case: Peak traffic

### Very High Load
- Concurrency: 50
- Total Requests: 500
- Use case: Stress testing

## Results Storage

All benchmarks save results to JSON files:
- `benchmark_results_YYYYMMDD_HHMMSS.json` - Comprehensive performance results (API + Kafka)
- `benchmark_summary_YYYYMMDD_HHMMSS.json` - Summary report (when running suite)

## Interpreting Results

### Good Performance Indicators
- **API Response Time**: < 1s
- **Kafka Latency**: < 100ms
- **Error Rate**: < 1% for both API and Kafka
- **API Throughput**: > 10 RPS
- **Kafka Throughput**: > 50 messages/sec
- **Overall Throughput**: > 20 ops/sec
- **P95 Latency**: < 2x average latency

### Performance Bottlenecks
- **High P99 latency**: Indicates occasional slow requests
- **High error rate**: System may be overloaded
- **Low throughput**: May need scaling
- **Database slow queries**: May need indexing

## Tips for Accurate Benchmarks

1. **Warm-up**: Run a few requests before benchmarking to warm up connections
2. **Isolated Environment**: Run on dedicated hardware/containers
3. **Consistent Load**: Use same concurrency levels for comparison
4. **Multiple Runs**: Run benchmarks multiple times and average results
5. **Monitor Resources**: Watch CPU, memory, and network during tests

## Troubleshooting

### API Timeout Errors
- Increase timeout in `performance_test.py`
- Check if API server is running
- Verify network connectivity

### Kafka Connection Errors
- Verify Kafka is running
- Check SSL certificates
- Verify bootstrap servers configuration


