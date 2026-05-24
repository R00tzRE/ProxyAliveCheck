from proxy_checker import ProxyChecker
import asyncio

checker = ProxyChecker(timeout=10, test_url="https://www.baidu.com")

proxies = [
    "127.0.0.1:8080",
    "http://127.0.0.1:8080",
    "socks4://127.0.0.1:1080",
    "socks5://127.0.0.1:1080"
]

print("Synchronous check:")
results_sync = checker.check_proxies_sync(proxies)
for result in results_sync:
    if result['alive']:
        print(f"✓ {result['proxy']} - Response time: {result['response_time']}s")
    else:
        print(f"✗ {result['proxy']} - Failed: {result['error']}")

print("\nAsynchronous check:")
results_async = asyncio.run(checker.check_proxies_async(proxies))
for result in results_async:
    if result['alive']:
        print(f"✓ {result['proxy']} - Response time: {result['response_time']}s")
    else:
        print(f"✗ {result['proxy']} - Failed: {result['error']}")

print("\nGet alive proxies:")
alive_proxies = checker.get_alive_proxies(proxies)
for proxy_info in alive_proxies:
    print(f"✓ {proxy_info['proxy']}")
