"""
Comprehensive performance benchmarking script for the Logistics AI Chatbot.
Tests API endpoints, Kafka throughput, and overall system performance.
"""
import sys
from pathlib import Path

# Add parent directory to path to allow imports
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

import asyncio
import aiohttp
import time
import statistics
from typing import List, Dict, Any, Optional
from datetime import datetime
import json
import argparse
from dataclasses import dataclass, asdict
from collections import defaultdict
import uuid

from src.kafka_utils.producer import KafkaProducer
from src.kafka_utils.config import TOPICS


@dataclass
class RequestMetrics:
    """Metrics for a single API request."""
    request_id: int
    question: str
    start_time: float
    end_time: float
    response_time: float
    status_code: int
    success: bool
    error: str = ""
    response_length: int = 0


@dataclass
class KafkaMetrics:
    """Metrics for a single Kafka operation."""
    operation_id: int
    operation_type: str  # "produce"
    start_time: float
    end_time: float
    latency: float
    success: bool
    message_size: int
    error: str = ""


@dataclass
class SystemBenchmarkResults:
    """Comprehensive system benchmark results."""
    # API Metrics
    api_total_requests: int
    api_successful_requests: int
    api_failed_requests: int
    api_requests_per_second: float
    api_avg_response_time: float
    api_min_response_time: float
    api_max_response_time: float
    api_median_response_time: float
    api_p95_response_time: float
    api_p99_response_time: float
    api_error_rate: float
    
    # Kafka Metrics
    kafka_total_operations: int
    kafka_successful_operations: int
    kafka_failed_operations: int
    kafka_operations_per_second: float
    kafka_avg_latency: float
    kafka_min_latency: float
    kafka_max_latency: float
    kafka_median_latency: float
    kafka_p95_latency: float
    kafka_p99_latency: float
    kafka_error_rate: float
    kafka_avg_message_size: int
    kafka_total_bytes: int
    
    # Overall Metrics
    total_test_duration: float
    overall_throughput: float  # Combined operations per second
    api_status_code_distribution: Dict[int, int]


class ComprehensivePerformanceBenchmark:
    """Comprehensive performance testing framework."""
    
    def __init__(self, api_url: str = "http://localhost:8000"):
        self.api_url = api_url
        self.api_metrics: List[RequestMetrics] = []
        self.kafka_metrics: List[KafkaMetrics] = []
        self.session: Optional[aiohttp.ClientSession] = None
        self.kafka_producer: Optional[KafkaProducer] = None
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
        if self.kafka_producer:
            self.kafka_producer.close()
    
    def setup_kafka(self):
        """Set up Kafka producer connection."""
        print("🔌 Connecting to Kafka...")
        self.kafka_producer = KafkaProducer()
        if not self.kafka_producer.connect():
            raise RuntimeError("Failed to connect Kafka producer")
        print("✅ Kafka producer connected")
    
    async def send_api_request(self, request_id: int, question: str) -> RequestMetrics:
        """Send a single API request and measure metrics."""
        start_time = time.time()
        metrics = RequestMetrics(
            request_id=request_id,
            question=question,
            start_time=start_time,
            end_time=0,
            response_time=0,
            status_code=0,
            success=False
        )
        
        try:
            async with self.session.post(
                f"{self.api_url}/ask",
                json={"question": question},
                timeout=aiohttp.ClientTimeout(total=60)
            ) as response:
                end_time = time.time()
                response_time = end_time - start_time
                
                metrics.end_time = end_time
                metrics.response_time = response_time
                metrics.status_code = response.status
                metrics.success = response.status == 200
                
                if metrics.success:
                    data = await response.json()
                    metrics.response_length = len(data.get("answer", ""))
                else:
                    try:
                        error_data = await response.json()
                        metrics.error = error_data.get("detail", "Unknown error")
                    except:
                        metrics.error = f"HTTP {response.status}"
                        
        except asyncio.TimeoutError:
            metrics.end_time = time.time()
            metrics.response_time = metrics.end_time - metrics.start_time
            metrics.status_code = 504
            metrics.error = "Request timeout"
        except Exception as e:
            metrics.end_time = time.time()
            metrics.response_time = metrics.end_time - metrics.start_time
            metrics.status_code = 0
            metrics.error = str(e)
        
        self.api_metrics.append(metrics)
        return metrics
    
    def send_kafka_message(self, operation_id: int, message: Dict[str, Any], topic: str) -> KafkaMetrics:
        """Send a single Kafka message and measure metrics."""
        start_time = time.time()
        message_size = len(json.dumps(message))
        
        metrics = KafkaMetrics(
            operation_id=operation_id,
            operation_type="produce",
            start_time=start_time,
            end_time=0,
            latency=0,
            success=False,
            message_size=message_size
        )
        
        try:
            message_id = str(uuid.uuid4())
            success = self.kafka_producer.produce(
                topic=topic,
                message=message,
                key=message_id
            )
            
            end_time = time.time()
            metrics.end_time = end_time
            metrics.latency = end_time - start_time
            metrics.success = success
            
            if success:
                self.kafka_producer.flush(timeout=0.1)  # Quick flush
            
        except Exception as e:
            metrics.end_time = time.time()
            metrics.latency = metrics.end_time - metrics.start_time
            metrics.error = str(e)
        
        self.kafka_metrics.append(metrics)
        return metrics
    
    async def run_comprehensive_test(
        self,
        questions: List[str],
        concurrency: int = 10,
        total_requests: int = 100,
        kafka_messages: int = 100,
        test_kafka: bool = True
    ) -> SystemBenchmarkResults:
        """
        Run comprehensive performance test including API and Kafka.
        
        Args:
            questions: List of questions to use for API tests
            concurrency: Number of concurrent API requests
            total_requests: Total number of API requests to send
            kafka_messages: Number of Kafka messages to produce
            test_kafka: Whether to test Kafka performance
            
        Returns:
            SystemBenchmarkResults with aggregated metrics
        """
        print("\n" + "=" * 80)
        print("🚀 COMPREHENSIVE PERFORMANCE BENCHMARK")
        print("=" * 80)
        print(f"\n📊 Test Configuration:")
        print(f"   API URL:              {self.api_url}")
        print(f"   API Requests:         {total_requests} (concurrency: {concurrency})")
        if test_kafka:
            print(f"   Kafka Messages:       {kafka_messages}")
        print(f"   Questions pool:       {len(questions)} questions\n")
        
        self.api_metrics = []
        self.kafka_metrics = []
        overall_start = time.time()
        
        # Setup Kafka if needed
        if test_kafka:
            try:
                self.setup_kafka()
            except Exception as e:
                print(f"⚠️  Kafka setup failed: {e}. Continuing with API tests only.")
                test_kafka = False
        
        # Run API tests
        print("\n📡 Running API Performance Test...")
        api_start = time.time()
        
        semaphore = asyncio.Semaphore(concurrency)
        
        async def bounded_api_request(request_id: int, question: str):
            async with semaphore:
                await self.send_api_request(request_id, question)
                if request_id % 10 == 0:
                    print(f"   API: Completed {request_id}/{total_requests} requests...", end='\r')
        
        api_tasks = []
        for i in range(total_requests):
            question = questions[i % len(questions)]
            task = bounded_api_request(i + 1, question)
            api_tasks.append(task)
        
        await asyncio.gather(*api_tasks)
        api_time = time.time() - api_start
        print(f"\n✅ API test complete: {total_requests} requests in {api_time:.2f}s")
        
        # Run Kafka tests
        if test_kafka and self.kafka_producer:
            print("\n📤 Running Kafka Performance Test...")
            kafka_start = time.time()
            
            for i in range(kafka_messages):
                message = {
                    "message_id": str(uuid.uuid4()),
                    "tool_name": "get_order_details_tool",
                    "message": f"What are the details of order {i % 10 + 1}?",
                    "timestamp": datetime.utcnow().isoformat()
                }
                self.send_kafka_message(i + 1, message, TOPICS["commands"])
                if (i + 1) % 10 == 0:
                    print(f"   Kafka: Produced {i + 1}/{kafka_messages} messages...", end='\r')
            
            kafka_time = time.time() - kafka_start
            print(f"\n✅ Kafka test complete: {kafka_messages} messages in {kafka_time:.2f}s")
        
        overall_time = time.time() - overall_start
        print(f"\n⏱️  Total test duration: {overall_time:.2f}s\n")
        
        return self._calculate_results(overall_time)
    
    def _calculate_results(self, total_time: float) -> SystemBenchmarkResults:
        """Calculate comprehensive metrics from collected data."""
        # Calculate API metrics
        api_successful = [m for m in self.api_metrics if m.success]
        api_failed = [m for m in self.api_metrics if not m.success]
        api_response_times = [m.response_time for m in self.api_metrics]
        
        api_status_codes = defaultdict(int)
        for m in self.api_metrics:
            api_status_codes[m.status_code] += 1
        
        if api_response_times:
            sorted_times = sorted(api_response_times)
            api_p95_index = int(len(sorted_times) * 0.95)
            api_p99_index = int(len(sorted_times) * 0.99)
            api_p95 = sorted_times[api_p95_index] if api_p95_index < len(sorted_times) else sorted_times[-1]
            api_p99 = sorted_times[api_p99_index] if api_p99_index < len(sorted_times) else sorted_times[-1]
        else:
            api_p95 = 0
            api_p99 = 0
        
        # Calculate Kafka metrics
        kafka_successful = [m for m in self.kafka_metrics if m.success]
        kafka_failed = [m for m in self.kafka_metrics if not m.success]
        kafka_latencies = [m.latency for m in self.kafka_metrics]
        
        if kafka_latencies:
            sorted_latencies = sorted(kafka_latencies)
            kafka_p95_index = int(len(sorted_latencies) * 0.95)
            kafka_p99_index = int(len(sorted_latencies) * 0.99)
            kafka_p95 = sorted_latencies[kafka_p95_index] if kafka_p95_index < len(sorted_latencies) else sorted_latencies[-1]
            kafka_p99 = sorted_latencies[kafka_p99_index] if kafka_p99_index < len(sorted_latencies) else sorted_latencies[-1]
        else:
            kafka_p95 = 0
            kafka_p99 = 0
        
        kafka_total_bytes = sum(m.message_size for m in self.kafka_metrics)
        
        # Calculate overall throughput
        total_operations = len(self.api_metrics) + len(self.kafka_metrics)
        overall_throughput = total_operations / total_time if total_time > 0 else 0
        
        return SystemBenchmarkResults(
            # API Metrics
            api_total_requests=len(self.api_metrics),
            api_successful_requests=len(api_successful),
            api_failed_requests=len(api_failed),
            api_requests_per_second=len(self.api_metrics) / total_time if total_time > 0 else 0,
            api_avg_response_time=statistics.mean(api_response_times) if api_response_times else 0,
            api_min_response_time=min(api_response_times) if api_response_times else 0,
            api_max_response_time=max(api_response_times) if api_response_times else 0,
            api_median_response_time=statistics.median(api_response_times) if api_response_times else 0,
            api_p95_response_time=api_p95,
            api_p99_response_time=api_p99,
            api_error_rate=(len(api_failed) / len(self.api_metrics) * 100) if self.api_metrics else 0,
            
            # Kafka Metrics
            kafka_total_operations=len(self.kafka_metrics),
            kafka_successful_operations=len(kafka_successful),
            kafka_failed_operations=len(kafka_failed),
            kafka_operations_per_second=len(self.kafka_metrics) / total_time if total_time > 0 and self.kafka_metrics else 0,
            kafka_avg_latency=statistics.mean(kafka_latencies) if kafka_latencies else 0,
            kafka_min_latency=min(kafka_latencies) if kafka_latencies else 0,
            kafka_max_latency=max(kafka_latencies) if kafka_latencies else 0,
            kafka_median_latency=statistics.median(kafka_latencies) if kafka_latencies else 0,
            kafka_p95_latency=kafka_p95,
            kafka_p99_latency=kafka_p99,
            kafka_error_rate=(len(kafka_failed) / len(self.kafka_metrics) * 100) if self.kafka_metrics else 0,
            kafka_avg_message_size=int(statistics.mean([m.message_size for m in self.kafka_metrics])) if self.kafka_metrics else 0,
            kafka_total_bytes=kafka_total_bytes,
            
            # Overall Metrics
            total_test_duration=total_time,
            overall_throughput=overall_throughput,
            api_status_code_distribution=dict(api_status_codes)
        )
    
    def print_results(self, results: SystemBenchmarkResults):
        """Print formatted comprehensive benchmark results."""
        print("=" * 80)
        print("📊 COMPREHENSIVE PERFORMANCE BENCHMARK RESULTS")
        print("=" * 80)
        
        # API Results
        print(f"\n📡 API PERFORMANCE:")
        print(f"   Total Requests:      {results.api_total_requests}")
        print(f"   Successful:          {results.api_successful_requests}")
        print(f"   Failed:              {results.api_failed_requests}")
        print(f"   Requests/Second:     {results.api_requests_per_second:.2f}")
        print(f"   Error Rate:          {results.api_error_rate:.2f}%")
        print(f"\n   Response Times (seconds):")
        print(f"      Average:          {results.api_avg_response_time:.3f}s")
        print(f"      Median:           {results.api_median_response_time:.3f}s")
        print(f"      Min:              {results.api_min_response_time:.3f}s")
        print(f"      Max:              {results.api_max_response_time:.3f}s")
        print(f"      P95:               {results.api_p95_response_time:.3f}s")
        print(f"      P99:               {results.api_p99_response_time:.3f}s")
        
        if results.api_status_code_distribution:
            print(f"\n   Status Code Distribution:")
            for code, count in sorted(results.api_status_code_distribution.items()):
                percentage = (count / results.api_total_requests * 100) if results.api_total_requests > 0 else 0
                print(f"      {code}: {count} ({percentage:.1f}%)")
        
        # Kafka Results
        if results.kafka_total_operations > 0:
            print(f"\n📤 KAFKA PERFORMANCE:")
            print(f"   Total Operations:     {results.kafka_total_operations}")
            print(f"   Successful:          {results.kafka_successful_operations}")
            print(f"   Failed:              {results.kafka_failed_operations}")
            print(f"   Operations/Second:   {results.kafka_operations_per_second:.2f}")
            print(f"   Error Rate:          {results.kafka_error_rate:.2f}%")
            print(f"\n   Latency (seconds):")
            print(f"      Average:          {results.kafka_avg_latency:.3f}s")
            print(f"      Median:           {results.kafka_median_latency:.3f}s")
            print(f"      Min:              {results.kafka_min_latency:.3f}s")
            print(f"      Max:              {results.kafka_max_latency:.3f}s")
            print(f"      P95:               {results.kafka_p95_latency:.3f}s")
            print(f"      P99:               {results.kafka_p99_latency:.3f}s")
            print(f"\n   Message Statistics:")
            print(f"      Avg Message Size: {results.kafka_avg_message_size} bytes")
            print(f"      Total Bytes:      {results.kafka_total_bytes:,} bytes")
        else:
            print(f"\n📤 KAFKA PERFORMANCE: Not tested")
        
        # Overall Results
        print(f"\n🚀 OVERALL SYSTEM PERFORMANCE:")
        print(f"   Total Test Duration:  {results.total_test_duration:.2f}s")
        print(f"   Overall Throughput:   {results.overall_throughput:.2f} ops/sec")
        print(f"   (Combined API + Kafka operations per second)")
        print("=" * 80)
    
    def save_results(self, results: SystemBenchmarkResults, filename: str = None):
        """Save results to JSON file."""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"benchmark_results_{timestamp}.json"
        
        data = {
            "timestamp": datetime.now().isoformat(),
            "results": asdict(results),
            "api_metrics": [asdict(m) for m in self.api_metrics],
            "kafka_metrics": [asdict(m) for m in self.kafka_metrics]
        }
        
        with open(filename, 'w') as f:
            json.dump(data, f, indent=2)
        
        print(f"\n💾 Results saved to: {filename}")


# Sample questions for testing
SAMPLE_QUESTIONS = [
    "What are the details of order 1?",
    "What are the details of order 2?",
    "What are the details of order 3?",
    "How many orders do we have?",
    "What is the status of order 1?",
    "What is the status of order 2?",
    "Hello, how are you?",
    "Thank you for your help",
    "What are the details of order 4?",
    "What are the details of order 5?",
]


async def run_benchmark_suite(api_url: str = "http://localhost:8000", test_kafka: bool = True):
    """Run a comprehensive benchmark suite."""
    print("\n" + "=" * 80)
    print("🚀 LOGISTICS AI CHATBOT - COMPREHENSIVE PERFORMANCE BENCHMARK SUITE")
    print("=" * 80)
    
    async with ComprehensivePerformanceBenchmark(api_url) as benchmark:
        all_results = []
        
        # Test 1: Low concurrency (baseline)
        print("\n📊 Test 1: Baseline (5 concurrent, 50 requests)")
        results1 = await benchmark.run_comprehensive_test(
            questions=SAMPLE_QUESTIONS,
            concurrency=5,
            total_requests=50,
            kafka_messages=50,
            test_kafka=test_kafka
        )
        benchmark.print_results(results1)
        all_results.append(("Baseline (5 concurrent)", results1))
        
        # Test 2: Medium concurrency
        print("\n📊 Test 2: Medium Load (10 concurrent, 100 requests)")
        results2 = await benchmark.run_comprehensive_test(
            questions=SAMPLE_QUESTIONS,
            concurrency=10,
            total_requests=100,
            kafka_messages=100,
            test_kafka=test_kafka
        )
        benchmark.print_results(results2)
        all_results.append(("Medium Load (10 concurrent)", results2))
        
        # Test 3: High concurrency
        print("\n📊 Test 3: High Load (20 concurrent, 200 requests)")
        results3 = await benchmark.run_comprehensive_test(
            questions=SAMPLE_QUESTIONS,
            concurrency=20,
            total_requests=200,
            kafka_messages=200,
            test_kafka=test_kafka
        )
        benchmark.print_results(results3)
        all_results.append(("High Load (20 concurrent)", results3))
        
        # Summary
        print("\n" + "=" * 80)
        print("📊 BENCHMARK SUMMARY")
        print("=" * 80)
        print(f"\n{'Test':<30} {'API RPS':<10} {'API Avg (s)':<12} {'Kafka OPS':<12} {'Overall OPS':<12} {'Error %':<10}")
        print("-" * 100)
        for name, result in all_results:
            kafka_ops = f"{result.kafka_operations_per_second:.2f}" if result.kafka_total_operations > 0 else "N/A"
            print(f"{name:<30} {result.api_requests_per_second:<10.2f} {result.api_avg_response_time:<12.3f} "
                  f"{kafka_ops:<12} {result.overall_throughput:<12.2f} {result.api_error_rate:<10.2f}")
        
        # Save all results
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        summary_file = f"benchmark_summary_{timestamp}.json"
        summary_data = {
            "timestamp": datetime.now().isoformat(),
            "api_url": api_url,
            "test_kafka": test_kafka,
            "tests": [
                {
                    "name": name,
                    "results": asdict(result)
                }
                for name, result in all_results
            ]
        }
        with open(summary_file, 'w') as f:
            json.dump(summary_data, f, indent=2)
        print(f"\n💾 Summary saved to: {summary_file}")


async def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Comprehensive performance benchmark for Logistics AI Chatbot")
    parser.add_argument(
        "--url",
        default="http://localhost:8000",
        help="API URL (default: http://localhost:8000)"
    )
    parser.add_argument(
        "--concurrency",
        type=int,
        help="Number of concurrent API requests (overrides suite)"
    )
    parser.add_argument(
        "--requests",
        type=int,
        default=100,
        help="Total number of API requests (default: 100)"
    )
    parser.add_argument(
        "--kafka-messages",
        type=int,
        default=100,
        help="Number of Kafka messages to produce (default: 100)"
    )
    parser.add_argument(
        "--no-kafka",
        action="store_true",
        help="Skip Kafka performance tests"
    )
    parser.add_argument(
        "--suite",
        action="store_true",
        help="Run full benchmark suite"
    )
    
    args = parser.parse_args()
    
    if args.suite:
        await run_benchmark_suite(args.url, test_kafka=not args.no_kafka)
    else:
        concurrency = args.concurrency or 10
        async with ComprehensivePerformanceBenchmark(args.url) as benchmark:
            results = await benchmark.run_comprehensive_test(
                questions=SAMPLE_QUESTIONS,
                concurrency=concurrency,
                total_requests=args.requests,
                kafka_messages=args.kafka_messages,
                test_kafka=not args.no_kafka
            )
            benchmark.print_results(results)
            benchmark.save_results(results)


if __name__ == "__main__":
    asyncio.run(main())
