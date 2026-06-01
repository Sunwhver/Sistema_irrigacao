const LATITUDE = "-26.22";
const LONGITUDE = "-52.67";

function formatarData() {
    const hoje = new Date();
    const opcoes = { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' };
    document.getElementById('data-atual').innerText = hoje.toLocaleDateString('pt-BR', opcoes).toUpperCase();
}

async function buscarClimaCompleto() {
    const urlClima = `https://api.open-meteo.com/v1/forecast?latitude=${LATITUDE}&longitude=${LONGITUDE}&current=temperature_2m,relative_humidity_2m,apparent_temperature&hourly=temperature_2m,precipitation_probability&daily=precipitation_probability_max&timezone=America%2FSao_Paulo`;
    
    try {
        const resposta = await fetch(urlClima);
        const dados = await resposta.json();
        
        document.getElementById('temp-atual').innerText = `${dados.current.temperature_2m}°C`;
        document.getElementById('sensacao-atual').innerText = `${dados.current.apparent_temperature}°C`;
        document.getElementById('umidade-atual').innerText = `${dados.current.relative_humidity_2m}%`;
        
        document.getElementById('prob-chuva').innerText = `${dados.daily.precipitation_probability_max[0]}%`;

        const horaAtual = new Date().getHours();
        const containerHoras = document.getElementById('previsao-horaria');
        containerHoras.innerHTML = '';

        for (let i = horaAtual; i < horaAtual + 6; i++) {
            const horaFormatada = dados.hourly.time[i].split("T")[1];
            const temp = dados.hourly.temperature_2m[i];
            const prob = dados.hourly.precipitation_probability[i];

            const div = document.createElement('div');
            div.className = 'hourly-item';
            div.innerHTML = `
                <strong>${horaFormatada}</strong>
                <span>${temp}°C</span>
                <span style="color: #64b5f6; font-size: 12px;">${prob}% chuva</span>
            `;
            containerHoras.appendChild(div);
        }

    } catch (erro) {
        console.error("Erro ao buscar clima da API externa:", erro);
    }
}

async function buscarHistoricoBackend() {
    const urlBackend = "http://127.0.0.1:8000/api/historico";
    
    try {
        const resposta = await fetch(urlBackend);
        const dados = await resposta.json();
        
        const historico = dados.historico;
        
        if (historico && historico.length > 0) {
            const registroAtual = historico[0];
            
            const badgeStatus = document.getElementById('status-irrigacao');
            if (registroAtual.decisao_irrigar === 1 || registroAtual.decisao_irrigar === true) {
                badgeStatus.innerText = "Irrigação LIGADA";
                badgeStatus.className = "value status-badge status-ativo";
            } else {
                badgeStatus.innerText = "Irrigação DESLIGADA";
                badgeStatus.className = "value status-badge status-inativo";
            }
            
            document.getElementById('alerta-sistema').innerText = registroAtual.alerta_emitido || "";

            const tbody = document.querySelector('#tabela-historico tbody');
            tbody.innerHTML = '';
            
            historico.forEach(linha => {
                const tr = document.createElement('tr');
                const soloStatus = linha.solo_seco ? "Seco" : "Úmido";
                const acaoStatus = linha.decisao_irrigar ? "Ligou" : "Não Ligou";
                
                tr.innerHTML = `
                    <td>${linha.id}</td>
                    <td>${soloStatus}</td>
                    <td>${acaoStatus}</td>
                `;
                tbody.appendChild(tr);
            });
        }

    } catch (erro) {
        console.error("Erro ao conectar com o Backend FastAPI:", erro);
        document.getElementById('status-irrigacao').innerText = "Aguardando NodeMCU...";
    }
}

formatarData();
buscarClimaCompleto();
buscarHistoricoBackend();