#!/usr/bin/env python3
"""
Ferramenta de Deploy e Monitoramento de APIs
Autor: Assistant
Descrição: Ferramenta completa para subir APIs e monitorar recursos da máquina
"""

import os
import sys
import json
import time
import psutil
import threading
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict
import argparse
import logging
from flask import Flask, jsonify, render_template_string, request
import requests

# Configuração do logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('api_monitor.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

@dataclass
class APIConfig:
    """Configuração de uma API"""
    name: str
    path: str
    port: int
    command: str
    auto_restart: bool = True
    health_check_url: Optional[str] = None
    env_vars: Dict[str, str] = None

@dataclass
class SystemMetrics:
    """Métricas do sistema"""
    timestamp: str
    cpu_percent: float
    memory_percent: float
    memory_used_gb: float
    memory_total_gb: float
    disk_percent: float
    disk_used_gb: float
    disk_total_gb: float
    network_sent_mb: float
    network_recv_mb: float
    active_apis: int

class APIManager:
    """Gerenciador de APIs"""
    
    def __init__(self):
        self.apis: Dict[str, APIConfig] = {}
        self.processes: Dict[str, subprocess.Popen] = {}
        self.config_file = "apis_config.json"
        self.load_config()
    
    def add_api(self, config: APIConfig):
        """Adiciona uma nova API"""
        self.apis[config.name] = config
        self.save_config()
        logger.info(f"API {config.name} adicionada")
    
    def remove_api(self, name: str):
        """Remove uma API"""
        if name in self.apis:
            self.stop_api(name)
            del self.apis[name]
            self.save_config()
            logger.info(f"API {name} removida")
    
    def start_api(self, name: str) -> bool:
        """Inicia uma API"""
        if name not in self.apis:
            logger.error(f"API {name} não encontrada")
            return False
        
        if name in self.processes and self.processes[name].poll() is None:
            logger.warning(f"API {name} já está rodando")
            return True
        
        config = self.apis[name]
        
        try:
            # Configurar variáveis de ambiente
            env = os.environ.copy()
            if config.env_vars:
                env.update(config.env_vars)
            
            # Iniciar processo
            process = subprocess.Popen(
                config.command.split(),
                cwd=config.path,
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            
            self.processes[name] = process
            logger.info(f"API {name} iniciada na porta {config.port}")
            return True
            
        except Exception as e:
            logger.error(f"Erro ao iniciar API {name}: {e}")
            return False
    
    def stop_api(self, name: str) -> bool:
        """Para uma API"""
        if name in self.processes:
            process = self.processes[name]
            if process.poll() is None:
                process.terminate()
                try:
                    process.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait()
            del self.processes[name]
            logger.info(f"API {name} parada")
            return True
        return False
    
    def restart_api(self, name: str) -> bool:
        """Reinicia uma API"""
        self.stop_api(name)
        time.sleep(2)
        return self.start_api(name)
    
    def get_api_status(self, name: str) -> Dict:
        """Obtém status de uma API"""
        if name not in self.apis:
            return {"status": "not_found"}
        
        config = self.apis[name]
        process = self.processes.get(name)
        
        if process and process.poll() is None:
            status = "running"
            pid = process.pid
            
            # Verificar health check se configurado
            health = "unknown"
            if config.health_check_url:
                try:
                    response = requests.get(config.health_check_url, timeout=5)
                    health = "healthy" if response.status_code == 200 else "unhealthy"
                except:
                    health = "unhealthy"
        else:
            status = "stopped"
            pid = None
            health = "down"
        
        return {
            "name": name,
            "status": status,
            "pid": pid,
            "port": config.port,
            "health": health,
            "auto_restart": config.auto_restart
        }
    
    def get_all_status(self) -> List[Dict]:
        """Obtém status de todas as APIs"""
        return [self.get_api_status(name) for name in self.apis.keys()]
    
    def check_and_restart_apis(self):
        """Verifica e reinicia APIs que falharam"""
        for name, config in self.apis.items():
            if config.auto_restart:
                status = self.get_api_status(name)
                if status["status"] == "stopped":
                    logger.warning(f"API {name} parou, reiniciando...")
                    self.start_api(name)
    
    def save_config(self):
        """Salva configuração das APIs"""
        config_data = {}
        for name, api_config in self.apis.items():
            config_data[name] = asdict(api_config)
        
        with open(self.config_file, 'w') as f:
            json.dump(config_data, f, indent=2)
    
    def load_config(self):
        """Carrega configuração das APIs"""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r') as f:
                    config_data = json.load(f)
                
                for name, data in config_data.items():
                    self.apis[name] = APIConfig(**data)
                
                logger.info(f"Configuração carregada: {len(self.apis)} APIs")
            except Exception as e:
                logger.error(f"Erro ao carregar configuração: {e}")

class SystemMonitor:
    """Monitor de sistema"""
    
    def __init__(self):
        self.metrics_history: List[SystemMetrics] = []
        self.max_history = 1000  # Manter últimas 1000 métricas
        self.running = False
        self.thread = None
    
    def get_current_metrics(self, active_apis: int = 0) -> SystemMetrics:
        """Obtém métricas atuais do sistema"""
        # CPU
        cpu_percent = psutil.cpu_percent(interval=1)
        
        # Memória
        memory = psutil.virtual_memory()
        memory_percent = memory.percent
        memory_used_gb = memory.used / (1024**3)
        memory_total_gb = memory.total / (1024**3)
        
        # Disco
        disk = psutil.disk_usage('/')
        disk_percent = (disk.used / disk.total) * 100
        disk_used_gb = disk.used / (1024**3)
        disk_total_gb = disk.total / (1024**3)
        
        # Rede
        net_io = psutil.net_io_counters()
        network_sent_mb = net_io.bytes_sent / (1024**2)
        network_recv_mb = net_io.bytes_recv / (1024**2)
        
        return SystemMetrics(
            timestamp=datetime.now().isoformat(),
            cpu_percent=cpu_percent,
            memory_percent=memory_percent,
            memory_used_gb=memory_used_gb,
            memory_total_gb=memory_total_gb,
            disk_percent=disk_percent,
            disk_used_gb=disk_used_gb,
            disk_total_gb=disk_total_gb,
            network_sent_mb=network_sent_mb,
            network_recv_mb=network_recv_mb,
            active_apis=active_apis
        )
    
    def start_monitoring(self, interval: int = 30):
        """Inicia monitoramento contínuo"""
        self.running = True
        self.thread = threading.Thread(target=self._monitor_loop, args=(interval,))
        self.thread.daemon = True
        self.thread.start()
        logger.info("Monitoramento iniciado")
    
    def stop_monitoring(self):
        """Para monitoramento"""
        self.running = False
        if self.thread:
            self.thread.join()
        logger.info("Monitoramento parado")
    
    def _monitor_loop(self, interval: int):
        """Loop de monitoramento"""
        while self.running:
            try:
                metrics = self.get_current_metrics()
                self.metrics_history.append(metrics)
                
                # Manter apenas últimas métricas
                if len(self.metrics_history) > self.max_history:
                    self.metrics_history = self.metrics_history[-self.max_history:]
                
                time.sleep(interval)
            except Exception as e:
                logger.error(f"Erro no monitoramento: {e}")
                time.sleep(interval)
    
    def get_metrics_summary(self) -> Dict:
        """Obtém resumo das métricas"""
        if not self.metrics_history:
            return {}
        
        latest = self.metrics_history[-1]
        return {
            "current": asdict(latest),
            "history_count": len(self.metrics_history),
            "monitoring_active": self.running
        }

class APIMonitoringTool:
    """Ferramenta principal de monitoramento"""
    
    def __init__(self):
        self.api_manager = APIManager()
        self.system_monitor = SystemMonitor()
        self.web_app = self._create_web_app()
        self.auto_check_interval = 60  # segundos
        self.auto_check_thread = None
        self.running = False
    
    def _create_web_app(self) -> Flask:
        """Cria aplicação web para dashboard"""
        app = Flask(__name__)
        
        @app.route('/')
        def dashboard():
            return render_template_string(DASHBOARD_HTML)
        
        @app.route('/api/status')
        def api_status():
            apis = self.api_manager.get_all_status()
            metrics = self.system_monitor.get_metrics_summary()
            return jsonify({
                "apis": apis,
                "system_metrics": metrics,
                "timestamp": datetime.now().isoformat()
            })
        
        @app.route('/api/start/<name>', methods=['POST'])
        def start_api(name):
            success = self.api_manager.start_api(name)
            return jsonify({"success": success})
        
        @app.route('/api/stop/<name>', methods=['POST'])
        def stop_api(name):
            success = self.api_manager.stop_api(name)
            return jsonify({"success": success})
        
        @app.route('/api/restart/<name>', methods=['POST'])
        def restart_api(name):
            success = self.api_manager.restart_api(name)
            return jsonify({"success": success})
        
        return app
    
    def add_api(self, name: str, path: str, port: int, command: str, 
                auto_restart: bool = True, health_check_url: str = None):
        """Adiciona uma nova API"""
        config = APIConfig(
            name=name,
            path=path,
            port=port,
            command=command,
            auto_restart=auto_restart,
            health_check_url=health_check_url
        )
        self.api_manager.add_api(config)
    
    def start_monitoring(self, web_port: int = 8080, monitor_interval: int = 30):
        """Inicia monitoramento completo"""
        self.running = True
        
        # Iniciar monitoramento do sistema
        self.system_monitor.start_monitoring(monitor_interval)
        
        # Iniciar verificação automática de APIs
        self.auto_check_thread = threading.Thread(target=self._auto_check_loop)
        self.auto_check_thread.daemon = True
        self.auto_check_thread.start()
        
        logger.info(f"Dashboard disponível em http://localhost:{web_port}")
        
        # Iniciar servidor web
        self.web_app.run(host='0.0.0.0', port=web_port, debug=False)
    
    def stop_monitoring(self):
        """Para monitoramento"""
        self.running = False
        self.system_monitor.stop_monitoring()
        
        # Parar todas as APIs
        for name in list(self.api_manager.apis.keys()):
            self.api_manager.stop_api(name)
    
    def _auto_check_loop(self):
        """Loop de verificação automática"""
        while self.running:
            try:
                self.api_manager.check_and_restart_apis()
                time.sleep(self.auto_check_interval)
            except Exception as e:
                logger.error(f"Erro na verificação automática: {e}")
                time.sleep(self.auto_check_interval)

# Template HTML para dashboard
DASHBOARD_HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>API Monitor Dashboard</title>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        body { font-family: Arial, sans-serif; margin: 0; padding: 20px; background: #f5f5f5; }
        .container { max-width: 1200px; margin: 0 auto; }
        .header { background: #2c3e50; color: white; padding: 20px; border-radius: 8px; margin-bottom: 20px; }
        .metrics { display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 20px; margin-bottom: 20px; }
        .metric-card { background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        .metric-value { font-size: 2em; font-weight: bold; color: #3498db; }
        .apis { background: white; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        .api-item { padding: 15px; border-bottom: 1px solid #eee; display: flex; justify-content: space-between; align-items: center; }
        .api-item:last-child { border-bottom: none; }
        .status { padding: 5px 10px; border-radius: 20px; color: white; font-size: 0.8em; }
        .status.running { background: #27ae60; }
        .status.stopped { background: #e74c3c; }
        .health { padding: 3px 8px; border-radius: 15px; font-size: 0.7em; margin-left: 10px; }
        .health.healthy { background: #d5edd8; color: #27ae60; }
        .health.unhealthy { background: #f8d7da; color: #e74c3c; }
        .health.down { background: #f8f9fa; color: #6c757d; }
        .btn { padding: 8px 15px; margin: 0 5px; border: none; border-radius: 4px; cursor: pointer; }
        .btn.start { background: #27ae60; color: white; }
        .btn.stop { background: #e74c3c; color: white; }
        .btn.restart { background: #f39c12; color: white; }
        .refresh { text-align: center; margin: 20px 0; }
        .refresh button { padding: 10px 20px; background: #3498db; color: white; border: none; border-radius: 4px; cursor: pointer; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🔧 API Monitor Dashboard</h1>
            <p>Monitoramento em tempo real de APIs e sistema</p>
        </div>
        
        <div class="metrics" id="metrics">
            <!-- Métricas serão carregadas aqui -->
        </div>
        
        <div class="refresh">
            <button onclick="loadData()">🔄 Atualizar</button>
            <span id="lastUpdate"></span>
        </div>
        
        <div class="apis">
            <h2 style="padding: 20px 20px 0;">APIs Registradas</h2>
            <div id="apiList">
                <!-- Lista de APIs será carregada aqui -->
            </div>
        </div>
    </div>

    <script>
        function loadData() {
            fetch('/api/status')
                .then(response => response.json())
                .then(data => {
                    updateMetrics(data.system_metrics);
                    updateAPIList(data.apis);
                    document.getElementById('lastUpdate').textContent = 
                        'Última atualização: ' + new Date(data.timestamp).toLocaleTimeString();
                })
                .catch(error => console.error('Erro:', error));
        }
        
        function updateMetrics(metrics) {
            if (!metrics.current) return;
            
            const metricsHTML = `
                <div class="metric-card">
                    <h3>💻 CPU</h3>
                    <div class="metric-value">${metrics.current.cpu_percent.toFixed(1)}%</div>
                </div>
                <div class="metric-card">
                    <h3>🧠 Memória</h3>
                    <div class="metric-value">${metrics.current.memory_percent.toFixed(1)}%</div>
                    <small>${metrics.current.memory_used_gb.toFixed(1)}GB / ${metrics.current.memory_total_gb.toFixed(1)}GB</small>
                </div>
                <div class="metric-card">
                    <h3>💾 Disco</h3>
                    <div class="metric-value">${metrics.current.disk_percent.toFixed(1)}%</div>
                    <small>${metrics.current.disk_used_gb.toFixed(1)}GB / ${metrics.current.disk_total_gb.toFixed(1)}GB</small>
                </div>
                <div class="metric-card">
                    <h3>🌐 Rede</h3>
                    <div style="font-size: 1.2em;">
                        ↑ ${metrics.current.network_sent_mb.toFixed(1)}MB<br>
                        ↓ ${metrics.current.network_recv_mb.toFixed(1)}MB
                    </div>
                </div>
            `;
            document.getElementById('metrics').innerHTML = metricsHTML;
        }
        
        function updateAPIList(apis) {
            if (!apis.length) {
                document.getElementById('apiList').innerHTML = 
                    '<div style="padding: 20px; text-align: center; color: #666;">Nenhuma API registrada</div>';
                return;
            }
            
            const apiHTML = apis.map(api => `
                <div class="api-item">
                    <div>
                        <strong>${api.name}</strong> (Porta: ${api.port})
                        <span class="status ${api.status}">${api.status.toUpperCase()}</span>
                        <span class="health ${api.health}">${api.health.toUpperCase()}</span>
                    </div>
                    <div>
                        <button class="btn start" onclick="controlAPI('${api.name}', 'start')">▶️ Iniciar</button>
                        <button class="btn stop" onclick="controlAPI('${api.name}', 'stop')">⏹️ Parar</button>
                        <button class="btn restart" onclick="controlAPI('${api.name}', 'restart')">🔄 Reiniciar</button>
                    </div>
                </div>
            `).join('');
            
            document.getElementById('apiList').innerHTML = apiHTML;
        }
        
        function controlAPI(name, action) {
            fetch(`/api/${action}/${name}`, { method: 'POST' })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        setTimeout(loadData, 2000); // Recarregar após 2 segundos
                    } else {
                        alert('Erro ao executar ação');
                    }
                })
                .catch(error => console.error('Erro:', error));
        }
        
        // Carregar dados iniciais e configurar auto-refresh
        loadData();
        setInterval(loadData, 30000); // Atualizar a cada 30 segundos
    </script>
</body>
</html>
"""

def main():
    """Função principal CLI"""
    parser = argparse.ArgumentParser(description='Ferramenta de Deploy e Monitoramento de APIs')
    parser.add_argument('--web-port', type=int, default=8080, help='Porta do dashboard web')
    parser.add_argument('--monitor-interval', type=int, default=30, help='Intervalo de monitoramento (segundos)')
    
    subparsers = parser.add_subparsers(dest='command', help='Comandos disponíveis')
    
    # Comando para adicionar API
    add_parser = subparsers.add_parser('add', help='Adicionar nova API')
    add_parser.add_argument('name', help='Nome da API')
    add_parser.add_argument('path', help='Caminho da API')
    add_parser.add_argument('port', type=int, help='Porta da API')
    add_parser.add_argument('command', help='Comando para iniciar a API')
    add_parser.add_argument('--health-url', help='URL para health check')
    add_parser.add_argument('--no-auto-restart', action='store_true', help='Desabilitar auto-restart')
    
    # Comando para listar APIs
    subparsers.add_parser('list', help='Listar APIs')
    
    # Comando para iniciar monitoramento
    subparsers.add_parser('monitor', help='Iniciar monitoramento')
    
    args = parser.parse_args()
    
    tool = APIMonitoringTool()
    
    if args.command == 'add':
        tool.add_api(
            name=args.name,
            path=args.path,
            port=args.port,
            command=args.command,
            auto_restart=not args.no_auto_restart,
            health_check_url=args.health_url
        )
        print(f"✅ API '{args.name}' adicionada com sucesso!")
    
    elif args.command == 'list':
        apis = tool.api_manager.get_all_status()
        if not apis:
            print("Nenhuma API registrada.")
        else:
            print("\n📋 APIs Registradas:")
            for api in apis:
                print(f"  • {api['name']} (Porta: {api['port']}) - Status: {api['status']}")
    
    elif args.command == 'monitor' or args.command is None:
        try:
            print("🚀 Iniciando monitoramento...")
            print(f"📊 Dashboard: http://localhost:{args.web_port}")
            print("⏹️  Pressione Ctrl+C para parar")
            tool.start_monitoring(args.web_port, args.monitor_interval)
        except KeyboardInterrupt:
            print("\n🛑 Parando monitoramento...")
            tool.stop_monitoring()
            print("✅ Monitoramento parado!")

if __name__ == "__main__":
    main()