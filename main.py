# main.py
import subprocess
import sys
import time
import getpass
import httpx
import json
import base64
import urllib.request
import urllib.parse
from pathlib import Path

from pydantic_settings import BaseSettings

from utils import colors as c
from utils import marks as m
from utils import printc
class Settings(BaseSettings):
    model_config = {
        "env_file": ".env"
    }

    github_user: str

settings = Settings()

GITHUB_USER = settings.github_user

GITHUB_URL = f"https://github.com/{GITHUB_USER}/"
GITHUB_SSH = f"git@github.com:{GITHUB_USER}/"
CLOUDFLARED_URL = "https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-{arch}.deb"
CERT_PATH = Path.cwd().parent / ".cloudflared" / "cert.pem"
CONFIG_PATH = Path.cwd().parent / ".cloudflared" / "config.yml"
CLONE_PATH = Path.cwd().parent
BORDER_SIZE = 85

def print_border() -> None:
    for _ in range(BORDER_SIZE):
        printc(color=c.YEL, out='-', end='')
    print()

def print_title(title: str) -> None:
    title_length = len(title)
    left_dashes = int((BORDER_SIZE - title_length)/2)
    right_dashes = int((BORDER_SIZE - title_length)/2)
    if BORDER_SIZE > title_length + left_dashes + right_dashes:
        right_dashes += 1
    for _ in range(left_dashes - 1):
        printc(color=c.YEL, out="-", end="")
    printc(color=c.YEL, out=" "+title, end=" ")
    for _ in range(right_dashes - 1):
        printc(color=c.YEL, out="-", end="")
    print("\n")

def print_info():
    pass

def get_repo_name() -> str:
    repo_name =  input("Github repository name:\n>  ")
    print()
    return repo_name


def get_sudo_password() -> str:
    username = getpass.getuser()
    sudo_password = getpass.getpass(prompt=f"[sudo] password for {username}:\n>  ")
    print()
    return sudo_password

def get_tunnel_name() -> str:
    tunnel_name = input("Enter new tunnel name:\n>  ")
    print()
    return tunnel_name

def get_port_number() -> str:
    port_number = input("Enter port number (Blank for 8443):\n>  ")
    if port_number == "":
        port_number = "8443"
    print()
    return port_number

# def get_domain_name() -> str:
#     domain_name = input("Enter domain name:\n>  ")
#     print()
#     return domain_name

def get_sub_domain() -> str:
    sub_domain = input("Enter subdomain (Blank for root domain):\n>  ")
    print()
    if sub_domain == "":
        return "www"
    return sub_domain

def get_domain_name() -> str:
    cert_path = str(Path.cwd().parent / ".cloudflared" / "cert.pem")

    with open(cert_path, "r") as f:
        content = f.read()

    lines = content.strip().split("\n")
    # Skip first and last line (markers)
    token_b64 = "".join(lines[1:-1])

    token_json = json.loads(base64.b64decode(token_b64))
    zone_id = token_json["zoneID"]
    api_token = token_json["apiToken"]

    res = httpx.get(
        url=f"https://api.cloudflare.com/client/v4/zones/{zone_id}",
        headers={"Authorization": f"Bearer {api_token}", "Content-Type": "application/json"}
    )
    return (res.json()['result']['name'])

def pwd() -> str:
    try:
        result = subprocess.run(["pwd"], check=True, capture_output=True, text=True)
        return result.stdout.strip()
    except subprocess.CalledProcessError as exc:
        printc(color=c.RED, out=f"Error: {exc.stderr}")
        sys.exit(1)

# def is_cloned(repo_name: str) -> bool:
#     time.sleep(0.25)
#     target_dir = str(Path.cwd().parent)
#     try:
#         result = subprocess.run(["ls", "-la", target_dir], check=True, capture_output=True, text=True)
#         lines = result.stdout.split("\n")
#         for line in lines:
#             if len(line) > 0 and line[0] == "d" and repo_name in line:
#                 return True
#         return False
#     except subprocess.CalledProcessError as exc:
#         printc(color=c.RED, out=f"{exc.stderr}")
#         sys.exit(1)

# def clone_repo(repo_name: str) -> None:
#     printc(color=c.YEL, out=f"{m.ARROW}  Cloning {repo_name} into parent directory")
#     time.sleep(0.25)
#     target_dir = str(Path.cwd().parent / repo_name)
#     if is_cloned(repo_name=repo_name):
#         printc(color=c.RED, out=f"{m.X_BLD}  Directory named {repo_name} already exists in parent directory", end='  ')
#         printc(color=c.GRN, out=f"{m.ARROW}  Attempting Cloudflare Setup")
#         print()
#         return
#     try:
#         subprocess.run(["git", "clone", GITHUB_URL+repo_name, target_dir], check=True, capture_output=True, text=True)
#         if is_cloned(repo_name=repo_name):
#             printc(color=c.GRN, out=f"{m.CHK_BLD}  Success Cloning {repo_name}")
#             print()
#             return
#         else:
#             printc(color=c.RED, out=f"Error Cloning {repo_name} into parent directory")
#             print()
#             return
#     except subprocess.CalledProcessError as exc:
#         print(f"Error: {exc.stderr}")
#         sys.exit(1)

def system_arch() -> str:
    time.sleep(0.25)
    try:
        result = subprocess.run(["dpkg", "--print-architecture"], check=True, capture_output=True, text=True)
        return result.stdout.strip()
    except subprocess.CalledProcessError as exc:
        printc(color=c.RED, out=f"{m.X}  {exc.stderr}")
        sys.exit(1)

def download_cloudflared():
    arch=system_arch()
    printc(color=c.YEL, out=f"{m.ARROW}  Downloading cloudflared-linux-{arch}")
    url = "https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-{arch}.deb".format(arch=arch)
    command = ["curl", "-L", "-o", "cloudflared.deb", url]
    time.sleep(0.25)
    try:
        subprocess.run(command, check=True, capture_output=True, text=True)
        download_check = subprocess.run(["ls", "-la"], check=True, capture_output=True, text=True)
        for line in download_check.stdout.strip().split("\n"):
            if "cloudflared.deb" in line:
                printc(c.GRN, out=f"{m.CHK_BLD}  Successfulled downloaded cloudflared.deb")
                print()
                return
        printc(color=c.RED, out=f"{m.X_BLD}  Failed to download cloudflared.deb")
        sys.exit(1)
    except subprocess.CalledProcessError as exc:
        printc(color=c.RED, out=f"{m.X}  {exc.stderr}")
        sys.exit(1)

def install_cloudflared(password):
    time.sleep(0.25)
    printc(color=c.YEL, out=f"{m.ARROW}  Installing cloudflared.deb")
    try:
        subprocess.run(["sudo", "-S", "dpkg", "-i", "cloudflared.deb"],
                       input=password+"\n", check=True, capture_output=True, text=True)
        install_check = subprocess.run(["which", "cloudflared"], check=True, capture_output=True, text=True)
        if install_check.stdout.strip().endswith("cloudflared"):
            printc(color=c.GRN, out=f"{m.CHK_BLD}  Successfully installed cloudflared.deb")
            print()
            return
        printc(color=c.RED, out=f"{m.X_BLD}  Failed to to install cloudflared.deb")
    except subprocess.CalledProcessError as exc:
        printc(color=c.RED, out=f"{m.X}  {exc.stderr}")
        sys.exit(1)

def shorten_url(long_url: str) -> str:
    """Shorten URL using is.gd"""
    try:
        api_url = f"https://is.gd/create.php?format=simple&url={urllib.parse.quote(long_url)}"
        req = urllib.request.Request(
            api_url,
            headers={"User-Agent": "Mozilla/5.0"}
        )
        with urllib.request.urlopen(req, timeout=5) as response:
            return response.read().decode('utf-8')
    except Exception as exc:
        print(f"URL shortening failed: {exc}")
        return long_url

def cloudflared_login():
    time.sleep(0.25)
    def delete_existing_cert() -> bool:
        time.sleep(0.25)
        target_dir = str(Path.cwd().parent)
        file = str(Path.cwd().parent / ".cloudflared")
        try:
            subprocess.run(["rm", "-rf", file])
            result = subprocess.run(["ls", "-la", target_dir], check=True, capture_output=True, text=True)
            lines = result.stdout.split("\n")
            for line in lines:
                if len(line) > 0 and line[0] == "d" and ".cloudflared" in line:
                    printc(c.RED, f"{m.X_BLD}  Error deleting existing cert.pem")
                    return
            printc(c.GRN, f"{m.CHK_BLD}  Existing cert.pem successfully deleted")
            print()
        except subprocess.CalledProcessError as exc:
            printc(c.RED, f"{m.X_BLD}  {exc.stderr}")
            sys.exit(1)

    def try_login() -> str:
        try:
            process = subprocess.Popen(
                ["cloudflared", "tunnel", "login"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            printc(c.YEL, "-  INSTRUCTIONS: During cloudflare login you may or may not be automatically")
            printc(c.YEL, "-  redericted to the \"Authorize Cloudflare Tunnel\" page. If you are not redirected,")
            printc(c.YEL, "-  you will need to click the shortened url a second time after logging in. Then,")
            printc(c.YEL, "-  just click the link and the script will create the configuration files, and put the")
            printc(c.YEL, "-  cert.pem file where it needs to go.\n")
            for line in process.stderr:
                line = line.strip()
                if not line:
                    continue
                if line.startswith("https://"):
                    link = shorten_url(long_url=line)
                    printc(c.YEL, f"{m.ARROW}  Login to cloudflare: ", end="  ")
                    print(link)
                elif "ERR You have an existing certificate at " in line:
                    printc(c.RED, f"{m.X_BLD}  You have an existing certificate in", end=" ")
                    print(f"{c.BOLD}{c.BLU} ~/.cloudflared/cert.pem", end=f"  {c.NC}")
                    printc(c.GRN, f"{m.ARROW}  Deleting existing ")
                    delete_existing_cert()
                    return "retry"
                elif "You have successfully logged in".lower() in line.lower():
                    printc(c.GRN, f"{m.CHK_BLD}  Successfully logged in to cloudflare")
                    print()
                    return "success"
                elif "Please open the following URL" in line:
                    pass
                else:
                    printc(c.GRY, f"   {line}")
        except subprocess.CalledProcessError as exc:
            printc(c.RED, f"{m.X_BLD}  {exc.stderr}")
            sys.exit(1)

    login_attempt = try_login()
    if login_attempt == "retry":
        try_login()

def create_tunnel(tunnel_name: str):
    # cloudflared tunnel create portfoliosite
    printc(c.YEL, f"{m.ARROW}  Creating cloudflare tunnel")
    time.sleep(0.25)
    try:
        process = subprocess.Popen(
            ["cloudflared", "tunnel", "create", tunnel_name],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )

        for line in process.stdout:
            line = line.strip()
            if "Created tunnel" in line and "with id" in line:
                elements = line.split()
                tunnel_id = elements[len(elements)-1]
                printc(c.GRN, f"{m.CHK_BLD}  Successfully created tunnel with id: {tunnel_id}")
                print()
                return tunnel_id

        for line in process.stderr:
            line = line.strip()
            if "tunnel with name already exists" in line:
                printc(c.RED, f"{m.X_BLD}  Failed to create tunnel - tunnel with name: {c.GRY}{c.BOLD}{tunnel_name}{c.RED} already exists")
                print()
                sys.exit(1)

        for line in process.stderr:
            line = line.strip()
            if "tunnel with name already exists" in line:
                printc(c.GRY, f"   Unexpected Error creating tunnel - {line}")
                sys.exit(1)

    except subprocess.CalledProcessError as exc:
        printc(c.RED, f"{m.X_BLD}  {exc.stderr}")
        sys.exit(1)

def tunnel_config(tunnel_id: str, domain: str, port: str = 8443):
    with open(f"{Path.home()}/.cloudflared/config.yml", "w") as f:
        cred_file = f"/home/{getpass.getuser()}/.cloudflared/{tunnel_id}.json"
        domain = domain
        service = f"http://127.0.0.1:{port}"
        lines = [
            f"tunnel: {tunnel_id}",
            f"credentials-file: {cred_file}",
            "",
            "ingress:",
            f"  - hostname: {domain}",
            f"    service: {service}",
            "  - service: http_status:404",
        ]
        f.write("\n".join(lines))

def route_dns(tunnel_name: str, tunnel_id: str, domain: str | None = None) -> str:
    printc(c.YEL, f"{m.ARROW}  Creating CNAME record for {tunnel_name}")
    time.sleep(0.25)
    try:
        # For root domains, don't pass domain as second argument to avoid CNAME flattening
        if domain is None:
            command = ["cloudflared", "tunnel", "route", "dns", tunnel_name]
        else:
            command = ["cloudflared", "tunnel", "route", "dns", tunnel_name, domain]

        process = subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )

        for line in process.stdout:
            line.strip()
            printc(c.GRY, f"   stdout:   {line}")
            print()

        for line in process.stderr:
            line.strip()
            if f"Added CNAME {domain}" in line and tunnel_id in line:
                elements = line.split(" ")
                for element in elements:
                    if domain in element:
                        printc(c.GRN, f"{m.CHK_BLD}  {element} will route to this tunnel: {c.NC}{tunnel_id}")
                        print()
            else:
                printc(c.GRY, f"   stderr:   {line}")

    except subprocess.CalledProcessError as exc:
        printc(c.RED, f"{m.X_BLD}  {exc.stderr}")

def cleanup() -> None:
    time.sleep(0.25)
    try:
        subprocess.run(["rm", "cloudflared.deb"])
    except subprocess.CalledProcessError as exc:
        printc(color=c.RED, out=f"{m.X}  {exc.stderr}")
        sys.exit(1)

def cloudflare_setup():
    print_border()
    print_title(title= "Cloudflare Tunnel Install and setup")
    # repo_name = get_repo_name()
    sudo_password = get_sudo_password()
    sub_domain = get_sub_domain()
    port = get_port_number()
    # clone_repo(repo_name=repo_name)
    download_cloudflared()
    install_cloudflared(password=sudo_password)
    cloudflared_login()
    domain = get_domain_name()
    if sub_domain == "www":
        tunnel_name = domain
    else:
        tunnel_name = ".".join([sub_domain, domain])
    tunnel_id = create_tunnel(tunnel_name=tunnel_name)
    tunnel_config(tunnel_id=tunnel_id, domain=domain, port=port)
    # cloudflared tunnel route dns portfoliosite yourdomain.com
    route_dns(tunnel_name=tunnel_name, tunnel_id=tunnel_id)
    if sub_domain == "www":
        route_dns(tunnel_name=f"www.{tunnel_name}", tunnel_id=tunnel_id, domain=f"www.{domain}")
    cleanup()

if __name__ == "__main__":
    cloudflare_setup()

# TODO: Handle incorrect password.
# TODO: delete and reclone if exists
# TODO: handle tunnel with name already exists
# TODO: handle CNAME records already exists