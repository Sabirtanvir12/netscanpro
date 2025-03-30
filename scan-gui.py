import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import socket
import concurrent.futures
import json
from datetime import datetime
import threading
import re
import struct

# Dark Theme Colors
BG_COLOR = "#121212"
FG_COLOR = "#e0e0e0"
ACCENT_COLOR = "#4a90e2"
BUTTON_COLOR = "#333333"
TEXTBOX_COLOR = "#252525"
OPEN_PORT_COLOR = "#2ecc71"  # Green
SERVICE_COLOR = "#3498db"    # Blue
VERSION_COLOR = "#9b59b6"    # Purple

class StealthScanGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("🔥Ultimate Network Scanner🔍-By SABIR")
        self.root.geometry("1100x800")
        self.root.configure(bg=BG_COLOR)
        
        # Make window resizable
        self.root.minsize(900, 700)
        
        # Scan control variables
        self.scanning = False
        self.stop_event = threading.Event()
        self.executor = None
        
        # Improved Style Configuration
        self.style = ttk.Style()
        self.style.theme_use('clam')
        self.style.configure('.', background=BG_COLOR, foreground=FG_COLOR)
        self.style.configure('TFrame', background=BG_COLOR)
        self.style.configure('TLabel', background=BG_COLOR, foreground=FG_COLOR)
        self.style.configure('TButton', background=BUTTON_COLOR, foreground=FG_COLOR)
        self.style.configure('TEntry', fieldbackground=TEXTBOX_COLOR, foreground=FG_COLOR)
        self.style.configure('TCombobox', fieldbackground=TEXTBOX_COLOR, foreground=FG_COLOR)
        self.style.map('TButton', background=[('active', ACCENT_COLOR)])
        
        # Configure Treeview Colors
        self.style.configure("Treeview", 
                            background=TEXTBOX_COLOR,
                            foreground=FG_COLOR,
                            fieldbackground=TEXTBOX_COLOR,
                            rowheight=25)
        self.style.map('Treeview', background=[('selected', ACCENT_COLOR)])
        
        # Main Frame
        self.main_frame = ttk.Frame(root, padding="15")
        self.main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Target Input Section
        input_frame = ttk.Frame(self.main_frame)
        input_frame.grid(row=0, column=0, sticky="ew", pady=10)
        
        ttk.Label(input_frame, text="Target:", font=('Helvetica', 10, 'bold')).grid(row=0, column=0, sticky=tk.W)
        self.target_entry = ttk.Entry(input_frame, width=40, font=('Helvetica', 10))
        self.target_entry.grid(row=1, column=0, padx=5, sticky=tk.W)
        
        ttk.Label(input_frame, text="Port Range:", font=('Helvetica', 10, 'bold')).grid(row=0, column=1, sticky=tk.W, padx=10)
        self.port_entry = ttk.Entry(input_frame, width=25, font=('Helvetica', 10))
        self.port_entry.insert(0, "1-1000")  # Default to top ports
        self.port_entry.grid(row=1, column=1, padx=5, sticky=tk.W)
        
        # Scan Options Section
        options_frame = ttk.Frame(self.main_frame)
        options_frame.grid(row=1, column=0, sticky="ew", pady=10)
        
        ttk.Label(options_frame, text="Scan Type:", font=('Helvetica', 10, 'bold')).grid(row=0, column=0, sticky=tk.W)
        self.scan_type = ttk.Combobox(options_frame, values=["Quick Scan (Top 1000)", "Full Scan (All Ports)", "Stealth Scan", "Custom"], width=20)
        self.scan_type.current(0)
        self.scan_type.grid(row=1, column=0, padx=5, sticky=tk.W)
        self.scan_type.bind("<<ComboboxSelected>>", self.update_port_range)
        
        self.service_var = tk.IntVar(value=1)
        self.service_cb = ttk.Checkbutton(options_frame, text="Service Detection", variable=self.service_var)
        self.service_cb.grid(row=0, column=1, padx=20, sticky=tk.W)
        
        self.version_var = tk.IntVar(value=1)
        self.version_cb = ttk.Checkbutton(options_frame, text="Version Detection", variable=self.version_var)
        self.version_cb.grid(row=1, column=1, padx=20, sticky=tk.W)
        
        ttk.Label(options_frame, text="Threads:", font=('Helvetica', 10, 'bold')).grid(row=0, column=2, sticky=tk.W, padx=10)
        self.threads_slider = ttk.Scale(options_frame, from_=50, to=1000, orient=tk.HORIZONTAL, length=150)
        self.threads_slider.set(300)  # Higher default threads
        self.threads_slider.grid(row=1, column=2, padx=5, sticky=tk.W)
        
        self.threads_label = ttk.Label(options_frame, text="300", width=4)
        self.threads_label.grid(row=1, column=3, padx=5, sticky=tk.W)
        self.threads_slider.configure(command=lambda e: self.threads_label.config(text=str(int(self.threads_slider.get()))))
        
        # Action Buttons
        button_frame = ttk.Frame(self.main_frame)
        button_frame.grid(row=2, column=0, sticky="ew", pady=10)
        
        self.scan_btn = ttk.Button(button_frame, text="Start Scan", command=self.start_scan)
        self.scan_btn.pack(side=tk.LEFT, padx=5)
        
        self.stop_btn = ttk.Button(button_frame, text="Stop Scan", command=self.stop_scan, state=tk.DISABLED)
        self.stop_btn.pack(side=tk.LEFT, padx=5)
        
        self.export_btn = ttk.Button(button_frame, text="Export Results", command=self.export_results, state=tk.DISABLED)
        self.export_btn.pack(side=tk.LEFT, padx=5)
        
        # Progress Bar
        self.progress = ttk.Progressbar(self.main_frame, orient=tk.HORIZONTAL, mode='determinate')
        self.progress.grid(row=3, column=0, sticky="ew", pady=5)
        
        # Results Frame
        self.results_frame = ttk.LabelFrame(self.main_frame, text="Scan Results", padding="10")
        self.results_frame.grid(row=4, column=0, sticky=tk.NSEW, pady=10)
        self.main_frame.rowconfigure(4, weight=1)
        self.main_frame.columnconfigure(0, weight=1)
        
        # Results Treeview with Colors
        self.results_tree = ttk.Treeview(
            self.results_frame, 
            columns=("Port", "State", "Service", "Version"), 
            show="headings",
            selectmode="extended"
        )
        
        # Configure Treeview Columns
        self.results_tree.heading("Port", text="Port", anchor=tk.W, command=lambda: self.sort_results("Port", False))
        self.results_tree.heading("State", text="State", anchor=tk.W)
        self.results_tree.heading("Service", text="Service", anchor=tk.W, command=lambda: self.sort_results("Service", False))
        self.results_tree.heading("Version", text="Version", anchor=tk.W, command=lambda: self.sort_results("Version", False))
        
        self.results_tree.column("Port", width=80, anchor=tk.W)
        self.results_tree.column("State", width=100, anchor=tk.W)
        self.results_tree.column("Service", width=250, anchor=tk.W)
        self.results_tree.column("Version", width=450, anchor=tk.W)
        
        # Custom Tags for Coloring
        self.results_tree.tag_configure('open', foreground=OPEN_PORT_COLOR)
        self.results_tree.tag_configure('service', foreground=SERVICE_COLOR)
        self.results_tree.tag_configure('version', foreground=VERSION_COLOR)
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(self.results_frame, orient=tk.VERTICAL, command=self.results_tree.yview)
        self.results_tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.results_tree.pack(fill=tk.BOTH, expand=True)
        
        # Status Bar
        self.status_var = tk.StringVar()
        self.status_var.set("Ready to scan")
        self.status_bar = ttk.Label(
            self.main_frame, 
            textvariable=self.status_var, 
            relief=tk.SUNKEN,
            padding=(10, 5),
            font=('Helvetica', 9)
        )
        self.status_bar.grid(row=5, column=0, sticky=tk.EW, pady=(5, 0))
        
        # Initialize variables
        self.results = []
        self.scanned_ports = 0
        self.total_ports = 0
    
    def update_port_range(self, event=None):
        """Update port range based on scan type selection"""
        scan_type = self.scan_type.get()
        if scan_type == "Quick Scan (Top 1000)":
            self.port_entry.delete(0, tk.END)
            self.port_entry.insert(0, "1-1000")
        elif scan_type == "Full Scan (All Ports)":
            self.port_entry.delete(0, tk.END)
            self.port_entry.insert(0, "1-65535")
    
    def parse_ports(self, port_str):
        """Convert port range string to list of ports"""
        port_str = port_str.strip()
        
        # Handle top ports
        if port_str.lower().startswith("top"):
            num = int(port_str[3:])
            # Common ports list
            common_ports = [
                21, 22, 23, 25, 53, 80, 110, 111, 135, 139, 143, 443, 
                445, 993, 995, 1723, 3306, 3389, 5900, 8080, 8443
            ]
            return common_ports[:num]
        
        # Handle ranges and lists
        if "-" in port_str:
            start, end = map(int, port_str.split("-"))
            return list(range(start, end + 1))
        elif "," in port_str:
            return list(map(int, port_str.split(",")))
        else:
            return [int(port_str)]
    
    def get_service_version(self, port):
        """Nmap-style accurate version detection with improved probes"""
        try:
            service = "unknown"
            version = ""
            banner = ""
            
            if self.version_var.get():
                try:
                    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                        s.settimeout(2)
                        s.connect((self.target, port))
                        
                        # HTTP/HTTPS (Ports 80, 443, 8080, 8443)
                        if port in [80, 443, 8080, 8443]:
                            probes = [
                                b"GET / HTTP/1.0\r\n\r\n",
                                b"GET / HTTP/1.1\r\nHost: %b\r\n\r\n" % self.target.encode(),
                                b"HEAD / HTTP/1.0\r\n\r\n"
                            ]
                            
                            for probe in probes:
                                try:
                                    s.send(probe)
                                    response = s.recv(4096).decode('latin-1', errors='ignore')
                                    
                                    # Server header detection
                                    server_match = re.search(r'Server:\s*([^\r\n]+)', response, re.IGNORECASE)
                                    powered_by = re.search(r'X-Powered-By:\s*([^\r\n]+)', response, re.IGNORECASE)
                                    via_match = re.search(r'Via:\s*([^\r\n]+)', response, re.IGNORECASE)
                                    
                                    if server_match:
                                        version = server_match.group(1).strip()
                                        service = "http"
                                        break
                                    elif "Apache" in response:
                                        version = self._detect_apache_version(response)
                                        service = "httpd"
                                        break
                                    elif "nginx" in response:
                                        version = self._detect_nginx_version(response)
                                        service = "nginx"
                                        break
                                    elif "Microsoft-IIS" in response:
                                        version = self._detect_iis_version(response)
                                        service = "microsoft-httpd"
                                        break
                                    elif powered_by:
                                        version = powered_by.group(1).strip()
                                        service = "http"
                                        break
                                    elif via_match:
                                        version = via_match.group(1).strip()
                                        service = "http-proxy"
                                        break
                                except:
                                    continue
                            
                            # Fallback to generic HTTP if no specific version found
                            if service == "unknown" and any(x in response.lower() for x in ['http/1.', '<html', '<!doctype']):
                                service = "http"
                                version = "HTTP Service"
                        
                        # SSH (Port 22)
                        elif port == 22:
                            try:
                                banner = s.recv(1024).decode('latin-1', errors='ignore')
                                ssh_match = re.match(r'SSH-(\d\.\d)-(.*)', banner)
                                if ssh_match:
                                    service = "ssh"
                                    proto_version = ssh_match.group(1)
                                    software = ssh_match.group(2).strip()
                                    
                                    # Common SSH software detection
                                    if "OpenSSH" in software:
                                        version = self._detect_openssh_version(software)
                                    elif "dropbear" in software.lower():
                                        version = self._detect_dropbear_version(software)
                                    else:
                                        version = f"{software} (Protocol {proto_version})"
                                else:
                                    service = "ssh"
                                    version = banner.split('\n')[0].strip()
                            except:
                                service = "ssh"
                                version = "SSH Service"
                        
                        # FTP (Port 21)
                        elif port == 21:
                            try:
                                banner = s.recv(1024).decode('latin-1', errors='ignore')
                                s.send(b"SYST\r\n")
                                syst_response = s.recv(1024).decode('latin-1', errors='ignore')
                                
                                service = "ftp"
                                version = banner.split('\n')[0].replace('220 ', '').strip()
                                
                                # Detect common FTP servers
                                if "vsFTPd" in version:
                                    version = self._detect_vsftpd_version(version)
                                elif "ProFTPD" in version:
                                    version = self._detect_proftpd_version(version)
                                elif "Pure-FTPd" in version:
                                    version = self._detect_pureftpd_version(version)
                                
                                # Add system type if available
                                if "215 UNIX Type: L8" in syst_response:
                                    version += " (Unix)"
                                elif "215 Windows_NT" in syst_response:
                                    version += " (Windows)"
                            except:
                                service = "ftp"
                                version = "FTP Service"
                        
                        # SMTP (Port 25, 587, 465)
                        elif port in [25, 587, 465]:
                            try:
                                banner = s.recv(1024).decode('latin-1', errors='ignore')
                                s.send(b"EHLO example.com\r\n")
                                ehlo_response = s.recv(2048).decode('latin-1', errors='ignore')
                                
                                service = "smtp"
                                version = banner.split('\n')[0].replace('220 ', '').strip()
                                
                                # Detect common SMTP servers
                                if "Postfix" in version:
                                    version = self._detect_postfix_version(version)
                                elif "Sendmail" in version:
                                    version = self._detect_sendmail_version(version, ehlo_response)
                                elif "Exim" in version:
                                    version = self._detect_exim_version(version, ehlo_response)
                                elif "Microsoft ESMTP" in version:
                                    version = self._detect_exchange_version(version, ehlo_response)
                            except:
                                service = "smtp"
                                version = "SMTP Service"
                        
                        # DNS (Port 53)
                        elif port == 53:
                            try:
                                # DNS version.bind query
                                query = b"\x00\x00\x01\x00\x00\x01\x00\x00\x00\x00\x00\x00\x07version\x04bind\x00\x00\x10\x00\x03"
                                s.send(query)
                                response = s.recv(1024)
                                
                                if len(response) > 0:
                                    service = "domain"
                                    # Parse DNS response to extract version.bind info
                                    try:
                                        if len(response) > 12:
                                            answer = response[12:]
                                            version_start = answer.find(b"version.bind") + 12
                                            version_end = answer.find(b"\x00", version_start)
                                            version_text = answer[version_start:version_end].decode('ascii', errors='ignore')
                                            version = f"BIND {version_text}"
                                        else:
                                            version = "DNS Service"
                                    except:
                                        version = "DNS Service"
                                else:
                                    service = "domain"
                                    version = "DNS Service"
                            except:
                                service = "domain"
                                version = "DNS Service"
                        
                        # MySQL (Port 3306)
                        elif port == 3306:
                            try:
                                # MySQL protocol handshake
                                banner = s.recv(1024)
                                if len(banner) > 4:
                                    protocol_version = banner[4]
                                    if protocol_version == 10:  # MySQL protocol
                                        server_version_end = banner.find(b'\x00', 5)
                                        server_version = banner[5:server_version_end].decode('latin-1')
                                        service = "mysql"
                                        version = server_version
                                    else:
                                        service = "mysql"
                                        version = "MySQL Service"
                                else:
                                    service = "mysql"
                                    version = "MySQL Service"
                            except:
                                service = "mysql"
                                version = "MySQL Service"
                        
                        # PostgreSQL (Port 5432)
                        elif port == 5432:
                            try:
                                # PostgreSQL protocol
                                s.send(struct.pack('!i', 8) + b'\x00\x03\x00\x00' + b'user\x00postgres\x00\x00')
                                response = s.recv(1024)
                                
                                if response and response[0] == ord('R'):
                                    # Error response contains version info
                                    version_start = response.find(b'PostgreSQL') + 10
                                    version_end = response.find(b' ', version_start)
                                    pg_version = response[version_start:version_end].decode('latin-1')
                                    service = "postgresql"
                                    version = f"PostgreSQL {pg_version}"
                                else:
                                    service = "postgresql"
                                    version = "PostgreSQL Service"
                            except:
                                service = "postgresql"
                                version = "PostgreSQL Service"
                        
                        # Redis (Port 6379)
                        elif port == 6379:
                            try:
                                s.send(b"INFO\r\n")
                                response = s.recv(1024).decode('latin-1', errors='ignore')
                                if "redis_version" in response:
                                    redis_match = re.search(r'redis_version:([^\r\n]+)', response)
                                    service = "redis"
                                    version = f"Redis {redis_match.group(1).strip()}"
                                else:
                                    service = "redis"
                                    version = "Redis Service"
                            except:
                                service = "redis"
                                version = "Redis Service"
                        
                        # MongoDB (Port 27017)
                        elif port == 27017:
                            try:
                                # MongoDB wire protocol
                                msg = struct.pack('<i', 16) + b'\x00\x00\x00\x00' + b'\x00\x00\x00\x00' + b'\x00\x00\x00\x00'
                                s.send(msg)
                                response = s.recv(1024)
                                if len(response) > 20:
                                    version_bytes = response[8:12]
                                    version_num = struct.unpack('<i', version_bytes)[0]
                                    major = version_num >> 16
                                    minor = (version_num >> 8) & 0xff
                                    patch = version_num & 0xff
                                    service = "mongodb"
                                    version = f"MongoDB {major}.{minor}.{patch}"
                                else:
                                    service = "mongodb"
                                    version = "MongoDB Service"
                            except:
                                service = "mongodb"
                                version = "MongoDB Service"
                        
                        # Generic protocol detection for other ports
                        else:
                            probes = [
                                (b"HELP\r\n", 1024),      # Common in text protocols
                                (b"INFO\r\n", 1024),       # Redis-style
                                (b"VERSION\r\n", 1024),    # Generic version request
                                (b"\x00\x00\x00\x00", 32), # Binary protocols
                                (b"GET / HTTP/1.0\r\n\r\n", 1024), # HTTP fallback
                                (b"\x16\x03\x01", 1024),   # SSL/TLS
                            ]
                            
                            best_response = ""
                            for probe, recv_size in probes:
                                try:
                                    s.send(probe)
                                    response = s.recv(recv_size)
                                    if len(response) > len(best_response):
                                        best_response = response
                                except:
                                    continue
                            
                            # Try to decode as text
                            try:
                                banner = best_response.decode('latin-1', errors='ignore')
                            except:
                                banner = str(best_response)
                            
                            # Match against common service patterns
                            patterns = [
                                (r'(?i)ssh[-_](\d+\.\d+)', 'ssh', 'OpenSSH {}'),
                                (r'(?i)apache[/\s](\d+\.\d+\.\d+)', 'httpd', 'Apache {}'),
                                (r'(?i)nginx[/\s](\d+\.\d+\.\d+)', 'nginx', 'nginx {}'),
                                (r'(?i)iis[/\s](\d+\.\d+)', 'microsoft-httpd', 'IIS {}'),
                                (r'(?i)postfix', 'smtp', 'Postfix'),
                                (r'(?i)exim', 'smtp', 'Exim'),
                                (r'(?i)sendmail', 'smtp', 'Sendmail'),
                                (r'(?i)proftpd', 'ftp', 'ProFTPD'),
                                (r'(?i)pure-ftpd', 'ftp', 'Pure-FTPd'),
                                (r'(?i)vsftpd', 'ftp', 'vsFTPd {}'),
                                (r'(?i)mysql', 'mysql', 'MySQL'),
                                (r'(?i)postgresql', 'postgresql', 'PostgreSQL'),
                                (r'(?i)redis', 'redis', 'Redis'),
                                (r'(?i)memcached', 'memcache', 'Memcached'),
                                (r'(?i)mongodb', 'mongodb', 'MongoDB'),
                            ]
                            
                            for pattern, svc, ver_pattern in patterns:
                                match = re.search(pattern, banner)
                                if match:
                                    service = svc
                                    try:
                                        version = ver_pattern.format(*match.groups())
                                    except:
                                        version = ver_pattern
                                    break
                            
                            # Fallback to system service names
                            if service == "unknown":
                                try:
                                    service = socket.getservbyport(port, "tcp")
                                except:
                                    pass
                            
                            version = banner.split('\n')[0].strip()[:100] if version == "" else version
                
                except Exception as e:
                    pass
            
            # Fallback to system service names
            if service == "unknown":
                try:
                    service = socket.getservbyport(port, "tcp")
                except:
                    pass
                    
            return service, version
            
        except Exception as e:
            return "unknown", ""
    
    # Version detection helper methods
    def _detect_apache_version(self, response):
        """Detect Apache HTTP Server version"""
        version_match = re.search(r'Apache[/\s](\d+\.\d+\.\d+)', response, re.IGNORECASE)
        if version_match:
            return f"Apache/{version_match.group(1)}"
        return "Apache"
    
    def _detect_nginx_version(self, response):
        """Detect nginx version"""
        version_match = re.search(r'nginx[/\s](\d+\.\d+\.\d+)', response, re.IGNORECASE)
        if version_match:
            return f"nginx/{version_match.group(1)}"
        return "nginx"
    
    def _detect_iis_version(self, response):
        """Detect Microsoft IIS version"""
        version_match = re.search(r'Microsoft-IIS/(\d+\.\d+)', response, re.IGNORECASE)
        if version_match:
            return f"IIS/{version_match.group(1)}"
        return "Microsoft-IIS"
    
    def _detect_openssh_version(self, banner):
        """Detect OpenSSH version"""
        version_match = re.search(r'OpenSSH[_]?(\d+\.\d+(?:p\d+)?)', banner, re.IGNORECASE)
        if version_match:
            return f"OpenSSH {version_match.group(1)}"
        return "OpenSSH"
    
    def _detect_dropbear_version(self, banner):
        """Detect Dropbear SSH version"""
        version_match = re.search(r'dropbear[_]?(\d+\.\d+)', banner, re.IGNORECASE)
        if version_match:
            return f"Dropbear SSH {version_match.group(1)}"
        return "Dropbear SSH"
    
    def _detect_vsftpd_version(self, banner):
        """Detect vsFTPd version"""
        version_match = re.search(r'vsFTPd (\d+\.\d+\.\d+)', banner)
        if version_match:
            return f"vsFTPd {version_match.group(1)}"
        return "vsFTPd"
    
    def _detect_proftpd_version(self, banner):
        """Detect ProFTPD version"""
        version_match = re.search(r'ProFTPD (\d+\.\d+\.\d+)', banner)
        if version_match:
            return f"ProFTPD {version_match.group(1)}"
        return "ProFTPD"
    
    def _detect_pureftpd_version(self, banner):
        """Detect Pure-FTPd version"""
        version_match = re.search(r'Pure-FTPd (\d+\.\d+)', banner)
        if version_match:
            return f"Pure-FTPd {version_match.group(1)}"
        return "Pure-FTPd"
    
    def _detect_postfix_version(self, banner):
        """Detect Postfix version"""
        version_match = re.search(r'Postfix (\d+\.\d+\.\d+)', banner)
        if version_match:
            return f"Postfix {version_match.group(1)}"
        return "Postfix"
    
    def _detect_sendmail_version(self, banner, ehlo_response):
        """Detect Sendmail version"""
        version_match = re.search(r'Sendmail(?:[/\s](\d+\.\d+\.\d+))?', banner, re.IGNORECASE)
        if version_match and version_match.group(1):
            return f"Sendmail {version_match.group(1)}"
        
        # Try to get version from EHLO response
        if "sendmail" in ehlo_response.lower():
            return "Sendmail"
        return "Sendmail"
    
    def _detect_exim_version(self, banner, ehlo_response):
        """Detect Exim version"""
        version_match = re.search(r'Exim (\d+\.\d+)', banner)
        if version_match:
            return f"Exim {version_match.group(1)}"
        return "Exim"
    
    def _detect_exchange_version(self, banner, ehlo_response):
        """Detect Microsoft Exchange version"""
        if "Microsoft ESMTP MAIL" in banner:
            return "Microsoft Exchange"
        return "Microsoft Exchange"
    
    def scan_port(self, port):
        """Scan a single port with service/version detection"""
        if self.stop_event.is_set():
            return port, False, "", ""
        
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.settimeout(1)
                result = sock.connect_ex((self.target, port))
                
                if result == 0:
                    service, version = "", ""
                    if self.service_var.get() or self.version_var.get():
                        service, version = self.get_service_version(port)
                    return port, True, service, version
                return port, False, "", ""
        except:
            return port, False, "", ""
    
    def update_results(self, port, is_open, service, version):
        """Update GUI with scan results (thread-safe)"""
        self.scanned_ports += 1
        self.progress['value'] = (self.scanned_ports / self.total_ports) * 100
        
        if is_open:
            # Insert with colored tags
            item_id = self.results_tree.insert(
                "", 
                tk.END, 
                values=(port, "OPEN", service, version),
                tags=('open')
            )
            
            # Apply different colors to different columns
            self.results_tree.set(item_id, "Service", service)
            self.results_tree.item(item_id, tags=('service'))
            self.results_tree.set(item_id, "Version", version)
            self.results_tree.item(item_id, tags=('version'))
            
            self.results.append({
                "port": port,
                "state": "OPEN",
                "service": service,
                "version": version
            })
    
    def sort_results(self, col, reverse):
        """Sort treeview by column"""
        data = [(self.results_tree.set(child, col), child) 
                for child in self.results_tree.get_children('')]
        
        # Try to convert to integer if it's the port column
        if col == "Port":
            data.sort(key=lambda x: int(x[0]), reverse=reverse)
        else:
            data.sort(reverse=reverse)
        
        for index, (val, child) in enumerate(data):
            self.results_tree.move(child, '', index)
        
        self.results_tree.heading(col, command=lambda: self.sort_results(col, not reverse))
    
    def start_scan(self):
        """Start the scanning process"""
        if self.scanning:
            return
        
        # Get input values
        target = self.target_entry.get().strip()
        if not target:
            messagebox.showerror("Error", "Please enter a target")
            return
        
        try:
            self.target = socket.gethostbyname(target)
        except socket.gaierror:
            messagebox.showerror("Error", "Invalid target")
            return
        
        try:
            ports = self.parse_ports(self.port_entry.get())
        except ValueError:
            messagebox.showerror("Error", "Invalid port range")
            return
        
        # Update UI
        self.scanning = True
        self.stop_event.clear()
        self.scan_btn.config(state=tk.DISABLED)
        self.stop_btn.config(state=tk.NORMAL)
        self.export_btn.config(state=tk.DISABLED)
        self.status_var.set(f"Scanning {target} ({len(ports)} ports)...")
        self.progress['value'] = 0
        self.results_tree.delete(*self.results_tree.get_children())
        self.results = []
        self.scanned_ports = 0
        self.total_ports = len(ports)
        
        # Start scan in background
        scan_thread = threading.Thread(target=self.run_scan, args=(ports,), daemon=True)
        scan_thread.start()
    
    def run_scan(self, ports):
        """Run the scan with threading"""
        threads = int(self.threads_slider.get())
        self.executor = concurrent.futures.ThreadPoolExecutor(max_workers=threads)
        
        try:
            futures = {self.executor.submit(self.scan_port, port): port for port in ports}
            for future in concurrent.futures.as_completed(futures):
                if self.stop_event.is_set():
                    break
                
                port, is_open, service, version = future.result()
                if is_open:
                    self.root.after(0, self.update_results, port, is_open, service, version)
        finally:
            self.scan_complete()
    
    def stop_scan(self):
        """Stop the ongoing scan"""
        if self.scanning:
            self.stop_event.set()
            if self.executor:
                self.executor.shutdown(wait=False)
            self.status_var.set(f"Scan stopped. Found {len(self.results)} open ports.")
    
    def scan_complete(self):
        """Clean up after scan completes"""
        self.scanning = False
        self.root.after(0, lambda: self.scan_btn.config(state=tk.NORMAL))
        self.root.after(0, lambda: self.stop_btn.config(state=tk.DISABLED))
        self.root.after(0, lambda: self.export_btn.config(state=tk.NORMAL))
        
        if not self.stop_event.is_set():
            self.root.after(0, lambda: self.status_var.set(
                f"Scan completed. Found {len(self.results)} open ports."))
            self.root.after(0, lambda: self.progress.config(value=100))
    
    def export_results(self):
        """Export results to file"""
        if not self.results:
            messagebox.showerror("Error", "No results to export")
            return
        
        file_path = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[
                ("JSON Files", "*.json"), 
                ("CSV Files", "*.csv"),
                ("HTML Files", "*.html"),
                ("All Files", "*.*")
            ],
            title="Save Scan Results"
        )
        
        if not file_path:
            return
        
        try:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            if file_path.endswith(".json"):
                with open(file_path, "w") as f:
                    json.dump({
                        "target": self.target,
                        "timestamp": timestamp,
                        "scan_type": self.scan_type.get(),
                        "results": self.results
                    }, f, indent=2)
            elif file_path.endswith(".csv"):
                with open(file_path, "w") as f:
                    f.write("Port,State,Service,Version\n")
                    for row in self.results:
                        f.write(f"{row['port']},{row['state']},\"{row['service']}\",\"{row['version']}\"\n")
            
            messagebox.showinfo("Success", f"Results successfully exported to:\n{file_path}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to export: {str(e)}")

# Run the application
if __name__ == "__main__":
    root = tk.Tk()
    
    # Set window icon (replace with actual icon path)
    try:
        root.iconbitmap("scan_icon.ico")
    except:
        pass
    
    app = StealthScanGUI(root)
    root.mainloop()
