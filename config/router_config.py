#KONEKTIFITAS ROUTER
DEFAULT_CONFIG = {
    "host" :"",
    "port" :"",
    "username" :"",
    "password" :"",
    "use_ssl" :"false",
    "ssl_verify" :"",
    "timeout" :10
}
#INTERFACE TARGET AI
INTERFACES = {
    "primary" : "ether1",
    "secondary" : "ether2"
}

#BASE MODEL TARGET
PING_TARGETS = [
    "8.8.8.8",    # Google DNS
    "1.1.1.1"     # Cloudflare DNS
]

#FAILOVER 
THRESHOLDS = {
    "latency_max": 100,        # Maximum acceptable latency in ms
    "packet_loss_max": 5,      # Maximum acceptable packet loss in %
    "check_interval": 30,      # Check interval in seconds
    "failover_timeout": 60,    # Time before considering switching back
    "consecutive_failures": 3  # Number of consecutive failures before failover
}