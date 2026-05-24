#!/usr/bin/env python3
import argparse
import sys
import asyncio
import requests
import re
from proxy_checker import ProxyChecker


def load_proxies_from_file(file_path: str) -> list:
    proxies = []
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line:
                    proxies.append(line)
        return proxies
    except Exception as e:
        print(f"Failed to read file: {e}")
        sys.exit(1)


def load_proxies_from_url(url: str, proxy_type: str) -> list:
    """Load proxy list from URL and add protocol prefix"""
    try:
        print(f"Fetching proxies from {url}...")
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        
        proxy_pattern = r'\b(?:\d{1,3}\.){3}\d{1,3}:\d+\b'
        raw_proxies = re.findall(proxy_pattern, response.text)
        
        proxies = []
        protocol_prefix = {
            'http': 'http://',
            'socks4': 'socks4://',
            'socks5': 'socks5://'
        }
        
        prefix = protocol_prefix.get(proxy_type.lower(), '')
        for proxy in raw_proxies:
            if prefix and not proxy.startswith(('http://', 'socks4://', 'socks5://')):
                proxies.append(f"{prefix}{proxy}")
            else:
                proxies.append(proxy)
        
        print(f"Successfully loaded {len(proxies)} proxies (type: {proxy_type.upper()})")
        return proxies
    except Exception as e:
        print(f"Failed to load proxies from URL: {e}")
        sys.exit(1)


def save_alive_proxies(results: list, output_file: str = None):
    alive_proxies = [r['proxy'] for r in results if r['alive']]
    
    if output_file:
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                for proxy in alive_proxies:
                    f.write(f"{proxy}\n")
            print(f"\nAlive proxies saved to: {output_file}")
        except Exception as e:
            print(f"\nFailed to save file: {e}")
    else:
        print("\nAlive proxies:")
        for proxy in alive_proxies:
            print(proxy)


def print_progress(current: int, total: int, alive: int, result: dict = None):
    progress_line = f"\r[{current}/{total}] Alive: {alive}"
    if result:
        if result['alive']:
            progress_line += f" - ✓ {result['proxy']} [{result['protocol'].upper()}]"
        else:
            progress_line += f" - ✗ {result['proxy']} [{result['protocol'].upper()}]"
    sys.stdout.write(progress_line.ljust(100))
    sys.stdout.flush()


def check_proxies_with_progress_sync(checker, proxies):
    results = []
    alive_count = 0
    total = len(proxies)
    
    for i, proxy in enumerate(proxies, 1):
        result = checker.check_proxy(proxy)
        results.append(result)
        if result['alive']:
            alive_count += 1
        print_progress(i, total, alive_count, result)
    
    print()
    return results


async def check_proxies_with_progress_async(checker, proxies):
    results = []
    alive_count = 0
    total = len(proxies)
    
    sem = asyncio.Semaphore(50)
    
    async def bounded_check(proxy):
        async with sem:
            return await checker.check_proxy_async(proxy)
    
    tasks = [bounded_check(proxy) for proxy in proxies]
    
    for i, task in enumerate(asyncio.as_completed(tasks), 1):
        result = await task
        results.append(result)
        if result['alive']:
            alive_count += 1
        print_progress(i, total, alive_count, result)
    
    print()
    return results


def main():
    parser = argparse.ArgumentParser(description='Proxy Checker Tool - Anti-False-Positive Version')
    parser.add_argument('-f', '--file', help='Path to file containing proxy IPs (format: ip:port, one per line)')
    parser.add_argument('-p', '--proxy', help='Single proxy IP (format: ip:port)')
    parser.add_argument('-l', '--url', help='Load proxy list from URL')
    parser.add_argument('--type', choices=['http', 'socks4', 'socks5'], default='http', 
                        help='Proxy type (http/socks4/socks5), only used with -l/--url (default: http)')
    parser.add_argument('-o', '--output', help='Output file path for alive proxies')
    parser.add_argument('-t', '--timeout', type=int, default=10, help='Timeout in seconds (default: 10)')
    parser.add_argument('-u', '--test-url', default='https://www.baidu.com', help='Test URL (default: https://www.baidu.com)')
    parser.add_argument('--sync', action='store_true', help='Use synchronous mode (default: async)')
    parser.add_argument('--verify-count', type=int, default=1, help='Number of verifications (increases accuracy but slower, default: 1)')
    parser.add_argument('--max-response-time', type=float, default=30.0, help='Max response time threshold in seconds (default: 30)')
    parser.add_argument('--verify-content', action='store_true', help='Verify response content length (reduces false positives, default: off)')
    args = parser.parse_args()

    if not args.file and not args.proxy and not args.url:
        parser.print_help()
        sys.exit(1)

    proxies = []
    if args.file:
        proxies = load_proxies_from_file(args.file)
    if args.proxy:
        proxies.append(args.proxy)
    if args.url:
        proxies.extend(load_proxies_from_url(args.url, args.type))

    if not proxies:
        print("No proxies loaded!")
        sys.exit(1)

    print(f"\nChecking {len(proxies)} proxies...")
    print(f"Timeout: {args.timeout} seconds")
    print(f"Test URL: {args.test_url}")
    print(f"Mode: {'Sync' if args.sync else 'Async'}")
    print(f"Verify count: {args.verify_count} times")
    print(f"Max response time: {args.max_response_time} seconds")
    print(f"Content verification: {'Enabled' if args.verify_content else 'Disabled'}")
    print("-" * 60)

    checker = ProxyChecker(
        timeout=args.timeout, 
        test_url=args.test_url,
        verify_count=args.verify_count,
        max_response_time=args.max_response_time,
        verify_content=args.verify_content
    )
    
    if args.sync:
        results = check_proxies_with_progress_sync(checker, proxies)
    else:
        results = asyncio.run(check_proxies_with_progress_async(checker, proxies))
    
    alive_count = sum(1 for r in results if r['alive'])
    print(f"\n{'=' * 60}")
    print(f"Check complete! Alive: {alive_count}/{len(proxies)}")
    
    print("\nDetailed results:")
    for result in results:
        if result['alive']:
            verify_info = f" [{result['success_count']}/{result['verify_count']}]" if result.get('verify_count', 1) > 1 else ""
            print(f"✓ {result['proxy']} [{result['protocol'].upper()}] - Response time: {result['response_time']}s - Status: {result['status_code']}{verify_info}")
        else:
            verify_info = f" [{result['success_count']}/{result['verify_count']}]" if result.get('verify_count', 1) > 1 else ""
            print(f"✗ {result['proxy']} [{result['protocol'].upper()}] - Failed: {result['error']}{verify_info}")

    save_alive_proxies(results, args.output)


if __name__ == "__main__":
    main()
