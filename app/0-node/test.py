ip_port = b''
ips_path = './ips.txt'
try:
    with open(ips_path, "r") as f:
        while (ip_port := f.readline().rstrip()):

            ip = ip_port[:ip_port.find(':')]
            port = int(ip_port[(ip_port.find(':') + 1):]) \
                    if ip_port[(ip_port.find(':') + 1):].isnumeric() \
                    else 0 

            if port == 0:
                print(f"[!] skipping invalid peer ip_port: {ip_port}..")
                continue


            print(f"[!] connecting to peer {ip}:{port}")
            print(ip,port)
            
except Exception as e:
    print(f"unexpected error on file.read() in conn_from_list(): {e.args[::-1]}")