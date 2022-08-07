import random
import os
import uuid


#
#
#
def get_http_version() -> str:
    return "HTTP/1.1"

#
#
#
def get_http_response_code() -> str:
    return [
        "200 OK",
        "400 Bad Request",
        "404 Not Found",
        "500 Internal Server Error"
    ]


#
#
#
def get_encoding() -> str:
    return 'utf-8'


#
#
#
def get_cookie_expiry() -> str:
    return "Thu, 2 Oct 2025 00:00:00 GMT"


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

    pp = "accelerometer=()," \
         "autoplay=()," \
         "camera=()," \
         "display-capture=()," \
         "document-domain=()," \
         "encrypted-media=()," \
         "fullscreen=()," \
         "geolocation=()," \
         "gyroscope=()," \
         "magnetometer=()," \
         "microphone=()," \
         "midi=()," \
         "payment=()," \
         "picture-in-picture=()," \
         "publickey-credentials-get=()," \
         "screen-wake-lock=()," \
         "sync-xhr=(self),usb=()," \
         "web-share=()," \
         "xr-spatial-tracking=()"

    hsts = "max-age=31536000; includeSubDomains"

    return [
        "Server: Custom",
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
        f"Strict-Transport-Security: {hsts}"
        f"Permissions-Policy: {pp}",
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
