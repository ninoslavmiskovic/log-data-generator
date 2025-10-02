import json
import random
import datetime
import uuid
from faker import Faker
import ipaddress

fake = Faker()

class DataTypeGenerator:
    """Base class for all data type generators"""
    
    def __init__(self):
        self.start_date = datetime.datetime.now() - datetime.timedelta(days=365)
        self.end_date = datetime.datetime.now()
    
    def random_timestamp(self, start=None, end=None):
        start = start or self.start_date
        end = end or self.end_date
        return start + datetime.timedelta(seconds=random.randint(0, int((end - start).total_seconds())))

class UnstructuredLogsGenerator(DataTypeGenerator):
    """Original unstructured logs generator"""
    
    def __init__(self):
        super().__init__()
        self.log_levels = ["INFO", "WARN", "ERROR", "DEBUG"]
        self.sources = ["AuthService", "PaymentService", "DatabaseService", "NotificationService", "CacheService"]
        self.messages = {
            "AuthService": {
                "INFO": [
                    "User '{user}' logged in successfully from IP address {ip_address}",
                    "Password reset initiated for user '{user}'; verification email sent"
                ],
                "WARN": [
                    "Multiple failed login attempts detected for user '{user}'; account locked for 30 minutes"
                ],
                "ERROR": [
                    "Critical security vulnerability detected: unauthorized access attempt to admin panel from IP '{ip_address}'",
                    "Authentication service failed to validate token for user '{user}'"
                ],
                "DEBUG": [
                    "Generated authentication token for session '{session_id}'",
                    "Password hash generated using SHA-256 algorithm for user '{user}'"
                ]
            },
            "PaymentService": {
                "INFO": [
                    "Payment completed successfully for transaction ID '{transaction_id}'",
                    "Refund processed for order ID '{order_id}'; amount refunded: ${amount}"
                ],
                "WARN": [
                    "Payment processing delayed due to network latency exceeding {latency}ms threshold",
                    "Suspicious transaction pattern detected for user '{user}'"
                ],
                "ERROR": [
                    "Transaction ID '{transaction_id}' declined due to insufficient funds",
                    "Payment gateway error: {gateway_response}"
                ],
                "DEBUG": [
                    "Debugging payment flow for transaction ID '{transaction_id}'",
                    "Payment gateway response: {gateway_response}"
                ]
            }
        }
    
    def generate_entry(self):
        if random.random() < 0.10:
            timestamp = random.choice([self.start_date + datetime.timedelta(days=30 * i) for i in range(1, 13)]) + datetime.timedelta(seconds=random.randint(0, 3600))
            level = "ERROR"
        else:
            timestamp = self.random_timestamp()
            level = random.choices(self.log_levels, weights=[0.7, 0.1, 0.1, 0.1])[0]
        
        source = random.choice(self.sources)
        tmpl_list = self.messages.get(source, {}).get(level, ["Generic log message"])
        tmpl = random.choice(tmpl_list)
        
        msg_data = {
            "user": fake.user_name(),
            "ip_address": fake.ipv4(),
            "session_id": fake.uuid4(),
            "transaction_id": fake.uuid4(),
            "order_id": fake.random_int(min=100000, max=999999),
            "amount": fake.random_int(min=10, max=5000),
            "latency": fake.random_int(min=100, max=2000),
            "gateway_response": random.choice(["SUCCESS", "TIMEOUT", "INVALID_CARD", "NETWORK_ERROR"])
        }
        
        try:
            message = tmpl.format(**msg_data)
        except KeyError:
            message = "Incomplete log message."
        
        return {
            "@timestamp": timestamp.isoformat() + "Z",
            "log.level": level,
            "source": source,
            "message": message
        }

class StructuredLogsGenerator(DataTypeGenerator):
    """JSON structured logs with consistent fields"""
    
    def __init__(self):
        super().__init__()
        self.services = ["user-api", "order-service", "inventory-service", "notification-service", "analytics-service"]
        self.environments = ["production", "staging", "development"]
        self.log_levels = ["INFO", "WARN", "ERROR", "DEBUG"]
    
    def generate_entry(self):
        service = random.choice(self.services)
        timestamp = self.random_timestamp()
        level = random.choices(self.log_levels, weights=[0.6, 0.2, 0.1, 0.1])[0]
        
        base_entry = {
            "@timestamp": timestamp.isoformat() + "Z",
            "service.name": service,
            "service.version": f"{fake.random_int(1, 5)}.{fake.random_int(0, 9)}.{fake.random_int(0, 9)}",
            "log.level": level,
            "environment": random.choice(self.environments),
            "host.name": fake.hostname(),
            "process.pid": fake.random_int(1000, 99999),
            "trace.id": fake.uuid4(),
            "span.id": fake.uuid4()[:16],
            "user.id": fake.uuid4(),
            "request.id": fake.uuid4(),
            "http.method": random.choice(["GET", "POST", "PUT", "DELETE", "PATCH"]),
            "http.status_code": random.choices([200, 201, 400, 401, 403, 404, 500, 502, 503], 
                                             weights=[40, 10, 8, 5, 3, 8, 10, 5, 5])[0],
            "http.response_time_ms": fake.random_int(10, 2000),
            "message": self._generate_message(service, level)
        }
        
        return base_entry
    
    def _generate_message(self, service, level):
        messages = {
            "user-api": {
                "INFO": ["User profile updated successfully", "User authentication completed", "Password reset email sent"],
                "WARN": ["Rate limit approaching for user", "Deprecated API endpoint used"],
                "ERROR": ["User authentication failed", "Database connection timeout", "Invalid user credentials"],
                "DEBUG": ["JWT token validated", "Database query executed", "Cache miss for user profile"]
            },
            "order-service": {
                "INFO": ["Order created successfully", "Payment processed", "Order shipped"],
                "WARN": ["Inventory low for product", "Payment gateway slow response"],
                "ERROR": ["Payment failed", "Order processing error", "Inventory service unavailable"],
                "DEBUG": ["Order validation completed", "Inventory check performed", "Payment gateway called"]
            }
        }
        
        service_messages = messages.get(service, {"INFO": ["Generic info message"], "WARN": ["Generic warning"], "ERROR": ["Generic error"], "DEBUG": ["Generic debug"]})
        return random.choice(service_messages.get(level, ["Generic message"]))

class DistributedTracesGenerator(DataTypeGenerator):
    """OpenTelemetry-style distributed tracing data"""
    
    def __init__(self):
        super().__init__()
        self.services = ["frontend", "user-service", "order-service", "payment-service", "inventory-service", "notification-service"]
        self.operations = {
            "frontend": ["page_load", "user_click", "form_submit", "api_call"],
            "user-service": ["authenticate", "get_profile", "update_profile", "validate_token"],
            "order-service": ["create_order", "get_order", "update_order", "cancel_order"],
            "payment-service": ["process_payment", "refund", "validate_card", "charge"],
            "inventory-service": ["check_stock", "reserve_items", "update_inventory", "release_reservation"],
            "notification-service": ["send_email", "send_sms", "send_push", "log_notification"]
        }
    
    def generate_entry(self):
        trace_id = fake.uuid4()
        root_span = self._generate_span(trace_id, None, "frontend", "page_load", is_root=True)
        
        # Generate child spans
        spans = [root_span]
        for _ in range(random.randint(2, 8)):
            parent_span = random.choice(spans)
            service = random.choice(self.services[1:])  # Skip frontend for child spans
            operation = random.choice(self.operations[service])
            child_span = self._generate_span(trace_id, parent_span["span.id"], service, operation)
            spans.append(child_span)
        
        return random.choice(spans)  # Return one span from the trace
    
    def _generate_span(self, trace_id, parent_span_id, service, operation, is_root=False):
        start_time = self.random_timestamp()
        duration_ms = fake.random_int(1, 1000) if not is_root else fake.random_int(100, 5000)
        end_time = start_time + datetime.timedelta(milliseconds=duration_ms)
        
        span = {
            "@timestamp": start_time.isoformat() + "Z",
            "trace.id": trace_id,
            "span.id": fake.uuid4()[:16],
            "span.name": f"{service}.{operation}",
            "service.name": service,
            "operation.name": operation,
            "span.kind": "server" if is_root else random.choice(["client", "server", "internal"]),
            "span.status": random.choices(["OK", "ERROR", "TIMEOUT"], weights=[85, 10, 5])[0],
            "duration.ms": duration_ms,
            "span.start_time": start_time.isoformat() + "Z",
            "span.end_time": end_time.isoformat() + "Z",
            "resource.attributes": {
                "service.version": f"{fake.random_int(1, 3)}.{fake.random_int(0, 9)}.{fake.random_int(0, 9)}",
                "deployment.environment": random.choice(["production", "staging", "development"]),
                "host.name": fake.hostname()
            }
        }
        
        if parent_span_id:
            span["span.parent_id"] = parent_span_id
        
        # Add operation-specific attributes
        if "payment" in operation:
            span["payment.amount"] = fake.random_int(10, 1000)
            span["payment.currency"] = random.choice(["USD", "EUR", "GBP"])
        elif "order" in operation:
            span["order.id"] = fake.uuid4()
            span["order.total"] = fake.random_int(50, 500)
        elif "user" in operation:
            span["user.id"] = fake.uuid4()
            span["user.email"] = fake.email()
        
        return span

class MetricsGenerator(DataTypeGenerator):
    """Time series metrics data"""
    
    def __init__(self):
        super().__init__()
        self.metric_types = ["counter", "gauge", "histogram", "summary"]
        self.services = ["frontend", "api-gateway", "user-service", "order-service", "database"]
        
    def generate_entry(self):
        service = random.choice(self.services)
        metric_type = random.choice(self.metric_types)
        timestamp = self.random_timestamp()
        
        base_metric = {
            "@timestamp": timestamp.isoformat() + "Z",
            "metric.type": metric_type,
            "service.name": service,
            "host.name": fake.hostname(),
            "environment": random.choice(["production", "staging", "development"])
        }
        
        if metric_type == "counter":
            base_metric.update(self._generate_counter_metric(service))
        elif metric_type == "gauge":
            base_metric.update(self._generate_gauge_metric(service))
        elif metric_type == "histogram":
            base_metric.update(self._generate_histogram_metric(service))
        else:  # summary
            base_metric.update(self._generate_summary_metric(service))
        
        return base_metric
    
    def _generate_counter_metric(self, service):
        counters = {
            "frontend": ["page_views_total", "button_clicks_total", "form_submissions_total"],
            "api-gateway": ["requests_total", "errors_total", "rate_limit_hits_total"],
            "user-service": ["logins_total", "registrations_total", "password_resets_total"],
            "order-service": ["orders_created_total", "orders_completed_total", "orders_cancelled_total"],
            "database": ["queries_total", "connections_total", "deadlocks_total"]
        }
        
        metric_name = random.choice(counters[service])
        return {
            "metric.name": metric_name,
            "metric.value": fake.random_int(1, 1000),
            "labels": {
                "method": random.choice(["GET", "POST", "PUT", "DELETE"]) if "requests" in metric_name else None,
                "status": random.choice(["success", "error"]) if "total" in metric_name else None
            }
        }
    
    def _generate_gauge_metric(self, service):
        gauges = {
            "frontend": ["active_users", "page_load_time_seconds"],
            "api-gateway": ["active_connections", "queue_size"],
            "user-service": ["active_sessions", "cache_hit_ratio"],
            "order-service": ["pending_orders", "processing_time_seconds"],
            "database": ["active_connections", "cpu_usage_percent", "memory_usage_bytes"]
        }
        
        metric_name = random.choice(gauges[service])
        if "percent" in metric_name:
            value = fake.random_int(0, 100)
        elif "bytes" in metric_name:
            value = fake.random_int(1000000, 8000000000)  # 1MB to 8GB
        elif "seconds" in metric_name:
            value = round(random.uniform(0.1, 10.0), 3)
        else:
            value = fake.random_int(0, 1000)
        
        return {
            "metric.name": metric_name,
            "metric.value": value
        }
    
    def _generate_histogram_metric(self, service):
        return {
            "metric.name": "response_time_histogram",
            "metric.buckets": {
                "0.1": fake.random_int(0, 100),
                "0.5": fake.random_int(100, 500),
                "1.0": fake.random_int(500, 800),
                "5.0": fake.random_int(800, 950),
                "10.0": fake.random_int(950, 1000)
            },
            "metric.count": fake.random_int(1000, 10000),
            "metric.sum": fake.random_int(5000, 50000)
        }
    
    def _generate_summary_metric(self, service):
        return {
            "metric.name": "request_duration_summary",
            "metric.quantiles": {
                "0.5": round(random.uniform(0.1, 2.0), 3),
                "0.9": round(random.uniform(2.0, 5.0), 3),
                "0.95": round(random.uniform(5.0, 8.0), 3),
                "0.99": round(random.uniform(8.0, 15.0), 3)
            },
            "metric.count": fake.random_int(1000, 10000),
            "metric.sum": fake.random_int(5000, 50000)
        }

class SecurityEventsGenerator(DataTypeGenerator):
    """SIEM-style security events"""
    
    def __init__(self):
        super().__init__()
        self.event_types = ["authentication", "authorization", "network", "malware", "data_access", "system"]
        self.severities = ["low", "medium", "high", "critical"]
        self.attack_types = ["brute_force", "sql_injection", "xss", "csrf", "malware", "phishing", "ddos"]
    
    def generate_entry(self):
        event_type = random.choice(self.event_types)
        timestamp = self.random_timestamp()
        
        base_event = {
            "@timestamp": timestamp.isoformat() + "Z",
            "event.type": event_type,  
            "event.id": fake.uuid4(),
            "event.severity": random.choices(self.severities, weights=[40, 35, 20, 5])[0],
            "source.ip": fake.ipv4(),
            "destination.ip": fake.ipv4(),
            "user.name": fake.user_name(),
            "host.name": fake.hostname(),
            "agent.name": "security-agent",
            "agent.version": f"{fake.random_int(1, 3)}.{fake.random_int(0, 9)}.{fake.random_int(0, 9)}"
        }
        
        if event_type == "authentication":
            base_event.update(self._generate_auth_event())
        elif event_type == "network":
            base_event.update(self._generate_network_event())
        elif event_type == "malware":
            base_event.update(self._generate_malware_event())
        else:
            base_event.update(self._generate_generic_security_event(event_type))
        
        return base_event
    
    def _generate_auth_event(self):
        success = random.choices([True, False], weights=[70, 30])[0]
        return {
            "event.action": "login_attempt",
            "event.outcome": "success" if success else "failure",
            "authentication.method": random.choice(["password", "mfa", "sso", "api_key"]),
            "source.port": fake.random_int(1024, 65535),
            "user.agent": fake.user_agent(),
            "geo.country": fake.country_code(),
            "geo.city": fake.city(),
            "message": f"{'Successful' if success else 'Failed'} login attempt for user"
        }
    
    def _generate_network_event(self):
        is_malicious = random.choices([True, False], weights=[20, 80])[0]
        return {
            "event.action": "network_connection",
            "network.protocol": random.choice(["tcp", "udp", "icmp"]),
            "source.port": fake.random_int(1024, 65535),
            "destination.port": random.choice([80, 443, 22, 3389, 1433, 3306]),
            "network.bytes": fake.random_int(100, 1000000),
            "threat.indicator": random.choice(self.attack_types) if is_malicious else None,
            "event.severity": "high" if is_malicious else "low",
            "message": f"Network connection {'blocked - malicious' if is_malicious else 'allowed'}"
        }
    
    def _generate_malware_event(self):
        return {
            "event.action": "malware_detection",
            "file.name": fake.file_name(),
            "file.path": fake.file_path(),
            "file.hash.sha256": fake.sha256(),
            "malware.name": f"{random.choice(['Trojan', 'Virus', 'Worm', 'Ransomware'])}.{fake.word().title()}",
            "event.severity": "critical",
            "event.outcome": random.choice(["quarantined", "deleted", "blocked"]),
            "message": "Malware detected and quarantined"
        }
    
    def _generate_generic_security_event(self, event_type):
        return {
            "event.action": f"{event_type}_event",
            "message": f"Security event of type {event_type} detected"
        }

class AlertsGenerator(DataTypeGenerator):
    """Alert manager style alerts"""
    
    def __init__(self):
        super().__init__()
        self.alert_names = [
            "HighCPUUsage", "HighMemoryUsage", "DiskSpaceLow", "ServiceDown",
            "HighErrorRate", "SlowResponseTime", "DatabaseConnectionFailed",
            "SecurityBreach", "UnauthorizedAccess", "PaymentFailure"
        ]
        self.severities = ["warning", "critical"]
        self.states = ["firing", "resolved"]
    
    def generate_entry(self):
        alert_name = random.choice(self.alert_names)
        state = random.choices(self.states, weights=[30, 70])[0]  # More resolved than firing
        timestamp = self.random_timestamp()
        
        alert = {
            "@timestamp": timestamp.isoformat() + "Z",
            "alert.name": alert_name,
            "alert.state": state,
            "alert.severity": random.choice(self.severities),
            "alert.id": fake.uuid4(),
            "labels": {
                "service": random.choice(["frontend", "backend", "database", "cache", "queue"]),
                "environment": random.choice(["production", "staging", "development"]),
                "team": random.choice(["platform", "backend", "frontend", "devops", "security"]),
                "instance": fake.hostname()
            },
            "annotations": {
                "summary": self._generate_summary(alert_name, state),
                "description": self._generate_description(alert_name),
                "runbook_url": f"https://runbooks.company.com/{alert_name.lower()}"
            }
        }
        
        if state == "firing":
            alert["alert.started_at"] = (timestamp - datetime.timedelta(minutes=fake.random_int(1, 60))).isoformat() + "Z"
        else:
            alert["alert.started_at"] = (timestamp - datetime.timedelta(minutes=fake.random_int(5, 120))).isoformat() + "Z"
            alert["alert.resolved_at"] = timestamp.isoformat() + "Z"
        
        # Add metric-specific values
        if "CPU" in alert_name:
            alert["metric.value"] = fake.random_int(80, 100)
            alert["metric.threshold"] = 85
        elif "Memory" in alert_name:
            alert["metric.value"] = fake.random_int(85, 98)
            alert["metric.threshold"] = 90
        elif "Disk" in alert_name:
            alert["metric.value"] = fake.random_int(90, 98)
            alert["metric.threshold"] = 95
        elif "ErrorRate" in alert_name:
            alert["metric.value"] = fake.random_int(5, 25)
            alert["metric.threshold"] = 5
        
        return alert
    
    def _generate_summary(self, alert_name, state):
        summaries = {
            "HighCPUUsage": f"CPU usage is {'above' if state == 'firing' else 'below'} threshold",
            "HighMemoryUsage": f"Memory usage is {'above' if state == 'firing' else 'below'} threshold",
            "ServiceDown": f"Service is {'down' if state == 'firing' else 'up'}",
            "HighErrorRate": f"Error rate is {'above' if state == 'firing' else 'below'} threshold"
        }
        return summaries.get(alert_name, f"{alert_name} alert is {state}")
    
    def _generate_description(self, alert_name):
        descriptions = {
            "HighCPUUsage": "CPU usage has exceeded the configured threshold",
            "HighMemoryUsage": "Memory usage has exceeded the configured threshold", 
            "ServiceDown": "Service health check is failing",
            "HighErrorRate": "Application error rate has exceeded acceptable levels"
        }
        return descriptions.get(alert_name, f"Alert for {alert_name}")

class NetworkTrafficGenerator(DataTypeGenerator):
    """Network flow and traffic data"""
    
    def __init__(self):
        super().__init__()
        self.protocols = ["TCP", "UDP", "ICMP"]
        self.common_ports = [80, 443, 22, 21, 25, 53, 110, 143, 993, 995, 3389, 1433, 3306, 5432, 6379]
    
    def generate_entry(self):
        timestamp = self.random_timestamp()
        protocol = random.choice(self.protocols)
        
        # Generate realistic internal/external IPs
        source_ip = self._generate_ip()
        dest_ip = self._generate_ip()
        
        flow = {
            "@timestamp": timestamp.isoformat() + "Z",
            "flow.id": fake.uuid4(),
            "network.protocol": protocol.lower(),
            "source.ip": source_ip,
            "destination.ip": dest_ip,
            "source.port": fake.random_int(1024, 65535),
            "destination.port": random.choice(self.common_ports + [fake.random_int(1024, 65535)]),
            "network.bytes": fake.random_int(64, 1000000),
            "network.packets": fake.random_int(1, 1000),
            "flow.duration_ms": fake.random_int(100, 30000),
            "network.direction": random.choice(["inbound", "outbound", "internal"]),
            "event.action": random.choice(["allowed", "blocked", "monitored"]),
            "geo.source.country": fake.country_code(),
            "geo.destination.country": fake.country_code(),
            "network.transport": protocol.lower()
        }
        
        # Add application layer info for HTTP/HTTPS
        if flow["destination.port"] in [80, 443]:
            flow["http.method"] = random.choice(["GET", "POST", "PUT", "DELETE"])
            flow["http.status_code"] = random.choices([200, 404, 500, 403], weights=[70, 15, 10, 5])[0]
            flow["user.agent"] = fake.user_agent()
            flow["url.domain"] = fake.domain_name()
        
        return flow
    
    def _generate_ip(self):
        # Mix of internal and external IPs
        if random.random() < 0.4:  # 40% internal IPs
            return random.choice([
                f"10.{fake.random_int(0, 255)}.{fake.random_int(0, 255)}.{fake.random_int(1, 254)}",
                f"192.168.{fake.random_int(0, 255)}.{fake.random_int(1, 254)}",
                f"172.{fake.random_int(16, 31)}.{fake.random_int(0, 255)}.{fake.random_int(1, 254)}"
            ])
        else:  # 60% external IPs
            return fake.ipv4()

class APMDataGenerator(DataTypeGenerator):
    """Application Performance Monitoring data"""
    
    def __init__(self):
        super().__init__()
        self.transaction_types = ["request", "task", "background_job", "database_query"]
        self.services = ["web-app", "api-service", "worker", "database"]
    
    def generate_entry(self):
        transaction_type = random.choice(self.transaction_types)
        service = random.choice(self.services)
        timestamp = self.random_timestamp()
        
        duration_ms = fake.random_int(10, 5000)
        success = random.choices([True, False], weights=[85, 15])[0]
        
        apm_data = {
            "@timestamp": timestamp.isoformat() + "Z",
            "transaction.id": fake.uuid4(),
            "transaction.type": transaction_type,
            "transaction.name": self._generate_transaction_name(transaction_type),
            "service.name": service,
            "service.version": f"{fake.random_int(1, 3)}.{fake.random_int(0, 9)}.{fake.random_int(0, 9)}",
            "transaction.duration.ms": duration_ms,
            "transaction.result": "success" if success else "error",
            "user.id": fake.uuid4(),
            "trace.id": fake.uuid4(),
            "span.id": fake.uuid4()[:16],
            "host.name": fake.hostname(),
            "container.id": fake.uuid4()[:12],
            "kubernetes.pod.name": f"{service}-{fake.uuid4()[:8]}",
            "kubernetes.namespace": random.choice(["production", "staging", "development"])
        }
        
        # Add transaction-specific data
        if transaction_type == "request":
            apm_data.update({
                "http.method": random.choice(["GET", "POST", "PUT", "DELETE"]),
                "http.status_code": 500 if not success else random.choices([200, 201, 204], weights=[80, 15, 5])[0],
                "http.url": f"https://api.company.com/{fake.uri_path()}",
                "user.agent": fake.user_agent()
            })
        elif transaction_type == "database_query":
            apm_data.update({
                "db.type": random.choice(["postgresql", "mysql", "mongodb", "redis"]),
                "db.statement": self._generate_db_statement(),
                "db.rows_affected": fake.random_int(0, 1000) if success else 0
            })
        
        # Add error details if transaction failed
        if not success:
            apm_data.update({
                "error.type": random.choice(["DatabaseError", "TimeoutError", "ValidationError", "AuthenticationError"]),
                "error.message": fake.sentence(),
                "error.stack_trace": self._generate_stack_trace()
            })
        
        return apm_data
    
    def _generate_transaction_name(self, transaction_type):
        names = {
            "request": [f"{method} /api/{endpoint}" for method in ["GET", "POST", "PUT", "DELETE"] 
                       for endpoint in ["users", "orders", "products", "payments"]],
            "task": ["send_email", "process_payment", "generate_report", "cleanup_temp_files"],
            "background_job": ["data_sync", "cache_refresh", "log_rotation", "backup_database"],
            "database_query": ["SELECT users", "UPDATE orders", "INSERT products", "DELETE sessions"]
        }
        return random.choice(names[transaction_type])
    
    def _generate_db_statement(self):
        statements = [
            "SELECT * FROM users WHERE id = $1",
            "UPDATE orders SET status = 'completed' WHERE id = $1",
            "INSERT INTO products (name, price) VALUES ($1, $2)",
            "DELETE FROM sessions WHERE expires_at < NOW()"
        ]
        return random.choice(statements)
    
    def _generate_stack_trace(self):
        return "\n".join([
            f"  at {fake.word()}.{fake.word()}({fake.file_name()}:{fake.random_int(1, 100)})",
            f"  at {fake.word()}.{fake.word()}({fake.file_name()}:{fake.random_int(1, 100)})",
            f"  at {fake.word()}.{fake.word()}({fake.file_name()}:{fake.random_int(1, 100)})"
        ])

# Registry of all available data generators
DATA_GENERATORS = {
    "unstructured_logs": {
        "name": "Unstructured Logs",
        "description": "Traditional log files with free-form text messages",
        "generator": UnstructuredLogsGenerator,
        "icon": "fas fa-file-alt",
        "index_pattern": "logs-unstructured"
    },
    "structured_logs": {
        "name": "Structured Logs", 
        "description": "JSON-formatted logs with consistent fields and metadata",
        "generator": StructuredLogsGenerator,
        "icon": "fas fa-code",
        "index_pattern": "logs-structured"
    },
    "distributed_traces": {
        "name": "Distributed Traces",
        "description": "OpenTelemetry-style tracing data showing request flows across services", 
        "generator": DistributedTracesGenerator,
        "icon": "fas fa-project-diagram",
        "index_pattern": "traces"
    },
    "metrics": {
        "name": "Metrics & Time Series",
        "description": "Counter, gauge, histogram and summary metrics from applications and infrastructure",
        "generator": MetricsGenerator,
        "icon": "fas fa-chart-line",
        "index_pattern": "metrics"
    },
    "security_events": {
        "name": "Security Events", 
        "description": "SIEM-style security events including authentication, network, and threat data",
        "generator": SecurityEventsGenerator,
        "icon": "fas fa-shield-alt",
        "index_pattern": "security-events"
    },
    "alerts": {
        "name": "Alerts & Notifications",
        "description": "Alert manager style alerts with firing and resolved states",
        "generator": AlertsGenerator,
        "icon": "fas fa-bell",
        "index_pattern": "alerts"
    },
    "network_traffic": {
        "name": "Network Traffic",
        "description": "Network flow logs with connection details, protocols, and traffic analysis",
        "generator": NetworkTrafficGenerator,
        "icon": "fas fa-network-wired",
        "index_pattern": "network-traffic"
    },
    "apm_data": {
        "name": "APM Data",
        "description": "Application Performance Monitoring data with transactions, errors, and traces",
        "generator": APMDataGenerator,
        "icon": "fas fa-tachometer-alt",
        "index_pattern": "apm"
    }
}
