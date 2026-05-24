# Proxy Checker Tool

A powerful proxy IP health checker tool supporting both synchronous and asynchronous detection modes, with support for HTTP, SOCKS4, and SOCKS5 protocols.

## New Feature: Anti-False-Positive

To address false positive issues, the following features have been added:
- **Multiple Verification**: Multiple checks can be performed on the same proxy, all must succeed to be considered alive
- **Response Time Threshold**: Proxies exceeding the set time are marked as invalid
- **Content Verification**: Verify response content length to avoid false responses

## Installation

```bash
pip install -r requirements.txt
```

## Supported Protocols

- **HTTP** - Format: `ip:port` or `http://ip:port`
- **SOCKS4** - Format: `socks4://ip:port`
- **SOCKS5** - Format: `socks5://ip:port`

## Usage

### Command Line Usage

#### Check Single Proxy
```bash
python main.py -p 127.0.0.1:8080
python main.py -p socks4://127.0.0.1:1080
python main.py -p socks5://127.0.0.1:1080
```

#### Batch Check from File
```bash
python main.py -f proxies.txt
```

#### Load and Check from URL
```bash
# Load HTTP type proxies (default)
python main.py -l https://example.com/proxies.txt

# Load SOCKS4 type proxies
python main.py -l https://example.com/proxies.txt --type socks4

# Load SOCKS5 type proxies
python main.py -l https://example.com/proxies.txt --type socks5
```

#### Save Alive Proxies to File
```bash
python main.py -f proxies.txt -o alive.txt
python main.py -l https://example.com/proxies.txt --type socks5 -o alive.txt
```

#### Custom Parameters
```bash
python main.py -f proxies.txt -t 5 --test-url https://www.google.com
```

#### Anti-False-Positive Configuration
```bash
# Verify 2 times (all must succeed to be considered alive)
python main.py -f proxies.txt --verify-count 2

# Set max response time to 10 seconds
python main.py -f proxies.txt --max-response-time 10

# Enable content verification
python main.py -f proxies.txt --verify-content

# Combined usage (recommended)
python main.py -f proxies.txt --verify-count 2 --max-response-time 10 --verify-content
```

#### Use Synchronous Mode
```bash
python main.py -f proxies.txt --sync
```

### Argument Reference

- `-f, --file`: Proxy IP file path, one proxy per line
- `-p, --proxy`: Single proxy IP
- `-l, --url`: Load proxy list from URL
- `--type`: Proxy type (http/socks4/socks5), only used with -l/--url (default: http)
- `-o, --output`: Output file path for alive proxies
- `-t, --timeout`: Timeout in seconds (default: 10)
- `-u, --test-url`: Test URL (default: https://www.baidu.com)
- `--sync`: Use synchronous mode (default: async)
- `--verify-count`: Number of verifications (increases accuracy but slower, default: 1)
- `--max-response-time`: Max response time threshold in seconds (default: 30)
- `--verify-content`: Verify response content length (reduces false positives, default: off)

### Module Usage

```python
from proxy_checker import ProxyChecker

checker = ProxyChecker(timeout=10, test_url="https://www.baidu.com")

proxies = [
    "127.0.0.1:8080",           # HTTP (default)
    "http://127.0.0.1:8080",    # HTTP
    "socks4://127.0.0.1:1080",  # SOCKS4
    "socks5://127.0.0.1:1080"   # SOCKS5
]

# Synchronous check
results = checker.check_proxies_sync(proxies)

# Asynchronous check
import asyncio
results = asyncio.run(checker.check_proxies_async(proxies))

# Get alive proxies
alive = checker.get_alive_proxies(proxies)
```

## File Description

- `proxy_checker.py`: Core checking module
- `main.py`: Command line interface
- `example.py`: Usage examples
- `proxies_example.txt`: Proxy file examples
