import socket
import sys

if len(sys.argv) not in (3, 4):
    print("用法：python webget.py host path [port]")
    sys.exit(1)

host = sys.argv[1]
path = sys.argv[2]
port = 80

if len(sys.argv) == 4:
    try:
        port = int(sys.argv[3])
    except ValueError:
        sys.exit("端口必须是整数")

if not 1 <= port <= 65535:
    sys.exit("端口必须在 1 到 65535 之间")
if not path.startswith("/"):
    sys.exit("path 要以 / 开头")

host_header = host if port == 80 else f"{host}:{port}"
request = (
    f"GET {path} HTTP/1.1\r\n"
    f"Host: {host_header}\r\n"
    "Connection: close\r\n"
    "\r\n"
)

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.settimeout(10)
s.connect((host, port))
s.sendall(request.encode("ascii"))

data = b""
recv_count = 0
header_end = -1
content_length = None

while True:
    chunk = s.recv(4096)
    recv_count += 1
    print(f"第 {recv_count} 次 recv 收到 {len(chunk)} 字节")

    if chunk == b"":
        if header_end == -1 or content_length is not None:
            s.close()
            raise EOFError("对端关闭时，响应还没收完整")
        # 没有 Content-Length 时，读到对端关闭就结束。
        break

    data += chunk

    if header_end == -1:
        # 空行可能跨两次 recv，所以在累计数据中查找。
        header_end = data.find(b"\r\n\r\n")
        if header_end == -1:
            continue

        for line in data[:header_end].split(b"\r\n"):
            if line.lower().startswith(b"content-length:"):
                content_length = int(line.split(b":", 1)[1])
                break

    if content_length is not None:
        # 跳过空行分隔符的 4 个字节，只数正文长度。
        body_start = header_end + 4
        if len(data) - body_start >= content_length:
            data = data[:body_start + content_length]
            break

s.close()
print(f"recv 总调用次数 {recv_count}")

header = data[:header_end].decode("latin-1")
body = data[header_end + 4:]
lines = header.split("\r\n")

status_line = lines[0]
status_code = status_line.split()[1]
print("状态行", status_line)
print("状态码", status_code)
print("全部响应头")
for line in lines[1:]:
    print(line)

with open("response_body.html", "wb") as file:
    file.write(body)

print(f"已保存 response_body.html，共 {len(body)} 字节")