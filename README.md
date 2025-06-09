# 🚀 API Monitoring Tool

![Python](https://img.shields.io/badge/Python-3.8%2B-blue)
![License](https://img.shields.io/badge/License-MIT-green)
[![GitHub Issues](https://img.shields.io/github/issues/Orshacaal/api-monitor-tool)](https://github.com/Orshacaal/api-monitor-tool/issues)

Ferramenta completa para deploy e monitoramento de APIs com dashboard em tempo real.

![Dashboard Preview](https://via.placeholder.com/800x400?text=Screenshot+do+Dashboard) <!-- Adicione um screenshot real aqui -->

## ✨ Recursos

- **Deploy automatizado** de APIs
- **Monitoramento em tempo real** de recursos do sistema (CPU, memória, disco, rede)
- **Dashboard web** integrado
- **Health checks** automatizados para APIs
- **Auto-restart** de APIs que falham
- Interface de linha de comando (CLI) amigável

## ⚙️ Instalação

### Pré-requisitos
- Python 3.8+
- Git (opcional)

### Passo a Passo

1. Clone o repositório:
```bash
git clone https://github.com/Orshacaal/api-monitor-tool.git
cd api-monitor-tool
Instale as dependências:

bash
pip install -r requirements.txt
🚦 Como Usar
Adicionar uma API para monitoramento
bash
python api_monitoring_tool.py add MinhaAPI /caminho/da/api 5000 "python app.py" --health-url http://localhost:5000/health
Parâmetros:

MinhaAPI: Nome amigável da API

/caminho/da/api: Caminho absoluto para o diretório da API

5000: Porta em que a API roda

"python app.py": Comando para iniciar a API

--health-url: URL para health check (opcional)

Iniciar o monitoramento
bash
python api_monitoring_tool.py monitor
Acesse o dashboard em: http://localhost:8080

Comandos disponíveis
Comando	Descrição	Exemplo
add	Adicionar nova API	add MinhaAPI ./api 8000 "npm start"
list	Listar APIs registradas	list
monitor	Iniciar dashboard de monitoramento	monitor --web-port 8080
📊 Funcionalidades do Dashboard
Visualização em tempo real de:

Utilização de CPU

Uso de memória

Uso de disco

Tráfego de rede

Status de todas as APIs:

Running/Stopped

Healthy/Unhealthy

Controle manual de APIs:

▶️ Iniciar

⏹️ Parar

🔄 Reiniciar

🛠️ Estrutura do Projeto
text
api-monitor-tool/
├── api_monitoring_tool.py  # Código principal
├── requirements.txt        # Dependências
├── .gitignore
├── README.md               # Este arquivo
└── requirements_and_examples.txt  # Exemplos de uso
🤝 Como Contribuir
Faça um fork do projeto

Crie sua branch (git checkout -b feature/sua-feature)

Faça commit das alterações (git commit -m 'Adiciona nova feature')

Faça push para a branch (git push origin feature/sua-feature)

Abra um Pull Request

📄 Licença
Este projeto está sob a licença MIT. Veja o arquivo LICENSE para mais detalhes.

Nota: Este projeto está em desenvolvimento ativo. Reporte issues e sugestões na página do GitHub!

text

### Para implementar no seu repositório:

1. Crie o arquivo `README.md` na raiz do projeto
2. Copie e cole o conteúdo acima
3. Personalize com:
   - Um screenshot real do dashboard (substitua o placeholder)
   - Informações específicas do seu projeto
   - Links corretos para issues

### Arquivo LICENSE recomendado (crie como `LICENSE`):

```text
MIT License

Copyright (c) 2023 Orshacaal

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
Comandos para adicionar ao repositório:
bash
# Adicione os arquivos
git add README.md LICENSE

# Commit
git commit -m "Adiciona README e LICENSE"

# Envie para o GitHub
git push origin main
