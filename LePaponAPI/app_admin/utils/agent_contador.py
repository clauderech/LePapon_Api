from datetime import date, datetime, timedelta
import re
from typing import Dict, Tuple

from models.controle_diario import ControleDiario
from models.controle_semanal import ControleSemanal


class ContadorAgent:
    """
    Agente contábil simples, baseado nas APIs existentes.

    Capacidades:
    - Resumo do dia (vendas, crediário, recebido, despesas) e caixa líquido
    - Resumo de período (início/fim) via somatórios das APIs
    - Interpretação básica de linguagem natural para datas ("hoje", "ontem", "últimos 7 dias", "este mês")
    """

    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip("/")
        self.ctrl_diario = ControleDiario(self.base_url)
        self.ctrl_sem = ControleSemanal(self.base_url)

    # -------------------- Utilidades de datas --------------------
    def _parse_periodo(self, texto: str) -> Tuple[str, str, str]:
        """
        Retorna (data_inicial_iso, data_final_iso, modo), onde modo ∈ {"dia", "periodo"}.
        Regras:
        - dois YYYY-MM-DD => período explícito
        - um YYYY-MM-DD, 'hoje', 'ontem' => dia
        - 'últimos 7 dias' => [hoje-7, ontem]
        - 'este mês'/'mês atual' => [1º dia do mês, hoje]
        Padrão: 'hoje'.
        """
        texto_low = (texto or "").lower()
        hoje = date.today()
        ontem = hoje - timedelta(days=1)

        datas = re.findall(r"\d{4}-\d{2}-\d{2}", texto_low)
        if len(datas) >= 2:
            ini = datetime.strptime(datas[0], "%Y-%m-%d").date()
            fim = datetime.strptime(datas[1], "%Y-%m-%d").date()
            if ini > fim:
                ini, fim = fim, ini
            return ini.isoformat(), fim.isoformat(), "periodo"
        if len(datas) == 1:
            d = datetime.strptime(datas[0], "%Y-%m-%d").date()
            return d.isoformat(), d.isoformat(), "dia"

        if "ontem" in texto_low:
            return ontem.isoformat(), ontem.isoformat(), "dia"
        if "hoje" in texto_low:
            return hoje.isoformat(), hoje.isoformat(), "dia"
        if "últimos 7 dias" in texto_low or "ultimos 7 dias" in texto_low or "semana" in texto_low:
            ini = ontem - timedelta(days=6)
            return ini.isoformat(), ontem.isoformat(), "periodo"
        if "este mês" in texto_low or "mes atual" in texto_low or "mês atual" in texto_low:
            ini = hoje.replace(day=1)
            return ini.isoformat(), hoje.isoformat(), "periodo"

        # Padrão
        return hoje.isoformat(), hoje.isoformat(), "dia"

    # -------------------- Cálculos --------------------
    @staticmethod
    def _caixa_liquido(totais: Dict[str, float]) -> float:
        """
        Heurística de caixa líquido do período:
        caixa = recebido + (vendas - crediario) - despesas
        Observação: ajuste se o seu modelo de dados diferir.
        """
        return (
            float(totais.get("total_recebido", 0) or 0)
            + (float(totais.get("total_vendas", 0) or 0) - float(totais.get("total_crediario", 0) or 0))
            - float(totais.get("total_despesas", 0) or 0)
        )

    @staticmethod
    def _fmt(valor: float) -> str:
        try:
            return f"R$ {float(valor):,.2f}".replace(",", "#").replace(".", ",").replace("#", ".")
        except Exception:
            return str(valor)

    def _resumo_dia(self, data_iso: str) -> Dict[str, float]:
        return self.ctrl_diario.consultar(data_iso)

    def _resumo_periodo(self, ini_iso: str, fim_iso: str) -> Dict[str, float]:
        return self.ctrl_sem.consultar_periodo(ini_iso, fim_iso)

    # -------------------- Interface principal --------------------
    def responder(self, pergunta: str) -> str:
        ini, fim, modo = self._parse_periodo(pergunta)

        if modo == "dia":
            totais = self._resumo_dia(ini)
            titulo = f"Resumo de {ini}"
        else:
            totais = self._resumo_periodo(ini, fim)
            titulo = f"Resumo do período {ini} a {fim}"

        caixa = self._caixa_liquido(totais)

        foco = ""
        low = (pergunta or "").lower()
        if any(k in low for k in ["venda", "faturamento"]):
            foco = f"\nFoco pedido: Vendas = {self._fmt(totais.get('total_vendas', 0))}"
        elif "credi" in low:
            foco = f"\nFoco pedido: Crediário = {self._fmt(totais.get('total_crediario', 0))}"
        elif "receb" in low:
            foco = f"\nFoco pedido: Recebido = {self._fmt(totais.get('total_recebido', 0))}"
        elif "despes" in low:
            foco = f"\nFoco pedido: Despesas = {self._fmt(totais.get('total_despesas', 0))}"
        elif any(k in low for k in ["lucro", "caixa", "saldo"]):
            foco = f"\nFoco pedido: Caixa líquido = {self._fmt(caixa)}"

        texto = (
            f"{titulo}\n"
            f"- Vendas: {self._fmt(totais.get('total_vendas', 0))}\n"
            f"- Crediário: {self._fmt(totais.get('total_crediario', 0))}\n"
            f"- Recebido: {self._fmt(totais.get('total_recebido', 0))}\n"
            f"- Despesas: {self._fmt(totais.get('total_despesas', 0))}\n"
            f"- Caixa líquido (heurístico): {self._fmt(caixa)}"
            f"{foco}"
        )
        return texto
