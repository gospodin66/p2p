import subprocess
from pathlib import Path

def scan_networks(ips_list: list, output_path: Path=Path('ips.txt')) -> list:
    try:
        pre_args = "-n -sn"
        post_args = "-oG -"
        subprocess.run(
            ["sh", 
             "-c", 
             "nmap "+pre_args+" "+' '.join(ips_list)+" "+post_args+" | awk '/Up$/{print $2}' | sort -V | tee "+str(output_path)
            ],
            capture_output=True,
            timeout=300,
            check=True
        )
    except FileNotFoundError as exc:
        print(f"Process failed because the executable could not be found.\n{exc}")
        return 1
    except subprocess.CalledProcessError as exc:
        print(
            f"Process failed because did not return a successful return code. "
            f"Returned {exc.returncode}\n{exc}"
        )
        return 1
    except subprocess.TimeoutExpired as exc:
        print(f"Process timed out.\n{exc}")
        return 1

    nodes = []
    with open(output_path, 'r') as f:
        nodes = f.read().split()

    return nodes

if __name__ == '__main__':

    ips_list = [
        '10.244.0.10-255',
        '192.168.1.0/24'
    ]
    output_path=Path('ips.txt')

    print(scan_networks(ips_list, output_path))
