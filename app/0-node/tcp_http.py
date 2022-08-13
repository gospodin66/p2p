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
def craft_http_response(tcp_packet_data: str) -> None:
    
    http_version = "HTTP/1.1"
    http_response_code  = [
        "200 OK",
        "400 Bad Request",
        "404 Not Found",
        "500 Internal Server Error"
    ]
    encoding = 'utf-8'
    cookie_expiry = "Thu, 2 Oct 2025 00:00:00 GMT"

    try:        
        cookies = set_cookies(tcp_packet_data)
        payload = 200

        headers_arr = set_http_headers()
        headers_str = "\r\n".join(str(header) for header in headers_arr)

        http_payload = "<!DOCTYPE html>" \
                        "<html>" \
                            f"<body>{payload}</body>" \
                        "</html>"

        return  f"{http_version} {http_response_code[0]}\r\n" \
                f"{headers_str}\r\n" \
                +(f"{cookies}\r\n\r\n" if cookies != "" else "\r\n")+ \
                f"{http_payload}\r\n"

    except Exception as e:
        print(f"[!] SERVER ERROR: {e.args[::-1]}")
        payload = 500

        http_payload = "<!DOCTYPE html>" \
                        "<html>" \
                            f"<body>{payload}</body>" \
                        "</html>"

        return  f"{http_version} {http_response_code[3]}\r\n" \
                f"{headers_str}\r\n" \
                +(f"{cookies}\r\n\r\n" if cookies != "" else "\r\n")+ \
                f"{http_payload}\r\n"