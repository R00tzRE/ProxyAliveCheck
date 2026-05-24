import requests
import time
import asyncio
import aiohttp
from aiohttp_socks import ProxyConnector
from typing import List, Dict, Optional


class ProxyChecker:
    def __init__(self, timeout: int = 10, test_url: str = "https://www.baidu.com", 
                 verify_count: int = 1, max_response_time: float = 30.0, 
                 verify_content: bool = False):
        self.timeout = timeout
        self.test_url = test_url
        self.verify_count = verify_count
        self.max_response_time = max_response_time
        self.verify_content = verify_content

    def _parse_proxy(self, proxy: str) -> tuple:
        proxy = proxy.strip()
        
        if proxy.startswith('socks4://'):
            protocol = 'socks4'
            proxy_addr = proxy[len('socks4://'):]
        elif proxy.startswith('socks5://'):
            protocol = 'socks5'
            proxy_addr = proxy[len('socks5://'):]
        elif proxy.startswith('http://'):
            protocol = 'http'
            proxy_addr = proxy[len('http://'):]
        else:
            protocol = 'http'
            proxy_addr = proxy
        
        return protocol, proxy_addr

    def _verify_response(self, response, response_time: float) -> tuple[bool, str]:
        """Verify if response is valid"""
        if response.status_code not in [200, 201, 202, 203, 204, 206, 301, 302, 304]:
            return False, f"Invalid status code: {response.status_code}"
        
        if response_time > self.max_response_time:
            return False, f"Response time too long: {response_time}s > {self.max_response_time}s"
        
        if self.verify_content:
            content_length = len(response.content)
            if content_length < 100:
                return False, f"Response content too short: {content_length} bytes"
        
        return True, "Verification passed"

    def check_proxy(self, proxy: str) -> Dict:
        protocol, proxy_addr = self._parse_proxy(proxy)
        
        if protocol in ['socks4', 'socks5']:
            proxy_dict = {
                "http": f"{protocol}://{proxy_addr}",
                "https": f"{protocol}://{proxy_addr}"
            }
        else:
            proxy_dict = {
                "http": f"http://{proxy_addr}",
                "https": f"http://{proxy_addr}"
            }
        
        success_count = 0
        total_response_time = 0.0
        last_error = None
        last_status_code = None
        
        for attempt in range(self.verify_count):
            try:
                start_time = time.time()
                response = requests.get(
                    self.test_url,
                    proxies=proxy_dict,
                    timeout=self.timeout,
                    allow_redirects=True
                )
                end_time = time.time()
                response_time = round(end_time - start_time, 2)
                
                is_valid, reason = self._verify_response(response, response_time)
                
                if is_valid:
                    success_count += 1
                    total_response_time += response_time
                    last_status_code = response.status_code
                else:
                    last_error = reason
                    
            except Exception as e:
                last_error = str(e)
        
        is_alive = success_count >= self.verify_count
        
        if is_alive:
            avg_response_time = round(total_response_time / success_count, 2)
            return {
                "proxy": proxy,
                "protocol": protocol,
                "alive": True,
                "status_code": last_status_code,
                "response_time": avg_response_time,
                "verify_count": self.verify_count,
                "success_count": success_count
            }
        else:
            return {
                "proxy": proxy,
                "protocol": protocol,
                "alive": False,
                "error": last_error or "Verification failed",
                "verify_count": self.verify_count,
                "success_count": success_count
            }

    def check_proxies_sync(self, proxies: List[str]) -> List[Dict]:
        results = []
        for proxy in proxies:
            results.append(self.check_proxy(proxy))
        return results

    async def _verify_response_async(self, response, response_time: float) -> tuple[bool, str]:
        """Async verify if response is valid"""
        if response.status not in [200, 201, 202, 203, 204, 206, 301, 302, 304]:
            return False, f"Invalid status code: {response.status}"
        
        if response_time > self.max_response_time:
            return False, f"Response time too long: {response_time}s > {self.max_response_time}s"
        
        if self.verify_content:
            content = await response.read()
            content_length = len(content)
            if content_length < 100:
                return False, f"Response content too short: {content_length} bytes"
        
        return True, "Verification passed"

    async def check_proxy_async(self, proxy: str) -> Dict:
        protocol, proxy_addr = self._parse_proxy(proxy)
        
        success_count = 0
        total_response_time = 0.0
        last_error = None
        last_status_code = None
        
        for attempt in range(self.verify_count):
            try:
                start_time = time.time()
                
                if protocol in ['socks4', 'socks5']:
                    connector = ProxyConnector.from_url(f"{protocol}://{proxy_addr}")
                    async with aiohttp.ClientSession(connector=connector) as session:
                        async with session.get(
                            self.test_url,
                            timeout=aiohttp.ClientTimeout(total=self.timeout),
                            allow_redirects=True
                        ) as response:
                            end_time = time.time()
                            response_time = round(end_time - start_time, 2)
                            
                            is_valid, reason = await self._verify_response_async(response, response_time)
                            if is_valid:
                                success_count += 1
                                total_response_time += response_time
                                last_status_code = response.status
                            else:
                                last_error = reason
                else:
                    proxy_url = f"http://{proxy_addr}"
                    async with aiohttp.ClientSession() as session:
                        async with session.get(
                            self.test_url,
                            proxy=proxy_url,
                            timeout=aiohttp.ClientTimeout(total=self.timeout),
                            allow_redirects=True
                        ) as response:
                            end_time = time.time()
                            response_time = round(end_time - start_time, 2)
                            
                            is_valid, reason = await self._verify_response_async(response, response_time)
                            if is_valid:
                                success_count += 1
                                total_response_time += response_time
                                last_status_code = response.status
                            else:
                                last_error = reason
                                
            except Exception as e:
                last_error = str(e)
        
        is_alive = success_count >= self.verify_count
        
        if is_alive:
            avg_response_time = round(total_response_time / success_count, 2)
            return {
                "proxy": proxy,
                "protocol": protocol,
                "alive": True,
                "status_code": last_status_code,
                "response_time": avg_response_time,
                "verify_count": self.verify_count,
                "success_count": success_count
            }
        else:
            return {
                "proxy": proxy,
                "protocol": protocol,
                "alive": False,
                "error": last_error or "Verification failed",
                "verify_count": self.verify_count,
                "success_count": success_count
            }

    async def check_proxies_async(self, proxies: List[str]) -> List[Dict]:
        tasks = [self.check_proxy_async(proxy) for proxy in proxies]
        results = await asyncio.gather(*tasks)
        return results

    def get_alive_proxies(self, proxies: List[str], async_mode: bool = True) -> List[Dict]:
        if async_mode:
            results = asyncio.run(self.check_proxies_async(proxies))
        else:
            results = self.check_proxies_sync(proxies)
        
        return [r for r in results if r["alive"]]
