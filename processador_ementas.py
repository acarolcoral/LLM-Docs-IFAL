import re
import os
from typing import List, Dict
import json

class ProcessadorEmentasAvancado:
    def __init__(self, llm):
        self.llm = llm
        self.max_tokens_por_chunk = 3000
        self.exemplos_ementas = self._carregar_exemplos_few_shot()
    
    def _carregar_exemplos_few_shot(self):
        """Exemplos para Few-Shot Learning - baseados em documentos reais do IFAL"""
        return [
            {
                "documento": "EDITAL Nº 001/2024 - PROGRAMA BOLSA PERMANÊNCIA\n"
                "Objetivo: Oferecer auxílio financeiro...\n"
                "Público-alvo: Estudantes de baixa renda...\n"
                "Valor: R$ 400,00\nVigência: Março a dezembro de 2024",
                "ementa": "Tipo: Edital de Seleção - Programa Bolsa Permanência\n"
                "Objetivo: Conceder auxílio financeiro para custeio de despesas educacionais de estudantes em situação de vulnerabilidade socioeconômica\n"
                "Público-alvo: Estudantes regularmente matriculados com renda familiar per capita de até 1,5 salários mínimos\n"
                "Disposições: Seleção mediante análise documental e socioeconômica, exigência de frequência mínima de 75%\n"
                "Prazos: Inscrições: 01 a 15/03/2024, Vigência: Março a dezembro de 2024\nValor do benefício: R$ 400,00 mensais\n"
                "Observações: Não acumulável com outros benefícios de mesma finalidade"
            }
        ]
    
    def dividir_documento_em_chunks(self, texto_completo: str) -> List[str]:
        """Divide o documento em chunks baseados em tokens"""
        chars_por_chunk = self.max_tokens_por_chunk * 4
        
        if len(texto_completo) <= chars_por_chunk:
            return [texto_completo]
        
        chunks = []
        linhas = texto_completo.split('\n')
        chunk_atual = []
        chars_chunk_atual = 0
        
        for linha in linhas:
            chars_linha = len(linha)
            
            if chars_chunk_atual + chars_linha > chars_por_chunk and chunk_atual:
                chunks.append('\n'.join(chunk_atual))
                chunk_atual = [linha]
                chars_chunk_atual = chars_linha
            else:
                chunk_atual.append(linha)
                chars_chunk_atual += chars_linha
        
        if chunk_atual:
            chunks.append('\n'.join(chunk_atual))
        
        return chunks
    
    def processar_chunk(self, chunk: str, numero_chunk: int, total_chunks: int) -> Dict:
        """Processa cada chunk extraindo informações relevantes"""
        
        # ✅ CORREÇÃO: Usar f-strings corretamente
        exemplos_str = ""
        for i, exemplo in enumerate(self.exemplos_ementas):
            exemplos_str += f"EXEMPLO {i+1}:\n{exemplo['documento']}\n\nEMENTA:\n{exemplo['ementa']}\n\n---\n"
        
        prompt = f"""
Analise este documento oficial e extraia informações para criar uma ementa:

EXEMPLOS DE REFERÊNCIA:
{exemplos_str}

TEXTO PARA ANÁLISE (parte {numero_chunk}/{total_chunks}):
{chunk[:2000]}

Extraia estas informações se presentes:
- Tipo de documento
- Objetivo principal  
- Público-alvo
- Disposições/regras
- Prazos/datas
- Valor do benefício (se aplicável)
- Observações importantes

Formate a resposta exatamente como os exemplos.
"""
        
        try:
            resposta = self.llm(
                prompt,
                max_tokens=800,
                temperature=0.1,
                stop=["###", "---"],
                echo=False
            )
            
            texto_resposta = resposta["choices"][0]["text"].strip()
            return self._extrair_campos_ementa(texto_resposta)
            
        except Exception as e:
            print(f"Erro no chunk {numero_chunk}: {e}")
            return {}
    
    def _extrair_campos_ementa(self, texto_ementa: str) -> Dict:
        """Extrai os campos da ementa formatada"""
        campos = {
            "tipo": "",
            "objetivo": "",
            "publico_alvo": "",
            "disposicoes": "",
            "prazos": "",
            "valor_beneficio": "",
            "observacoes": ""
        }
        
        linhas = texto_ementa.split('\n')
        
        for linha in linhas:
            linha = linha.strip()
            if ':' in linha:
                chave, valor = linha.split(':', 1)
                chave = chave.strip().lower()
                valor = valor.strip()
                
                if 'tipo' in chave:
                    campos["tipo"] = valor
                elif 'objetivo' in chave:
                    campos["objetivo"] = valor
                elif 'público' in chave or 'publico' in chave:
                    campos["publico_alvo"] = valor
                elif 'disposi' in chave:
                    campos["disposicoes"] = valor
                elif 'prazo' in chave:
                    campos["prazos"] = valor
                elif 'valor' in chave:
                    campos["valor_beneficio"] = valor
                elif 'observa' in chave:
                    campos["observacoes"] = valor
        
        return campos
    
    def consolidar_informacoes_chunks(self, informacoes_chunks: List[Dict]) -> Dict:
        """Consolida informações de todos os chunks"""
        consolidado = {
            "tipo": "",
            "objetivo": "",
            "publico_alvo": "",
            "disposicoes": "",
            "prazos": "",
            "valor_beneficio": "",
            "observacoes": ""
        }
        
        for info in informacoes_chunks:
            for campo in consolidado:
                if info.get(campo) and len(info[campo]) > len(consolidado[campo]):
                    consolidado[campo] = info[campo]
        
        return consolidado
    
    def gerar_ementa_final(self, informacoes_consolidadas: Dict) -> str:
        """Gera a ementa final formatada"""
        ementa_final = []
        
        if informacoes_consolidadas["tipo"]:
            ementa_final.append(f"Tipo: {informacoes_consolidadas['tipo']}")
        if informacoes_consolidadas["objetivo"]:
            ementa_final.append(f"Objetivo: {informacoes_consolidadas['objetivo']}")
        if informacoes_consolidadas["publico_alvo"]:
            ementa_final.append(f"Público-alvo: {informacoes_consolidadas['publico_alvo']}")
        if informacoes_consolidadas["disposicoes"]:
            ementa_final.append(f"Disposições: {informacoes_consolidadas['disposicoes']}")
        if informacoes_consolidadas["prazos"]:
            ementa_final.append(f"Prazos: {informacoes_consolidadas['prazos']}")
        if informacoes_consolidadas["valor_beneficio"]:
            ementa_final.append(f"Valor do benefício: {informacoes_consolidadas['valor_beneficio']}")
        if informacoes_consolidadas["observacoes"]:
            ementa_final.append(f"Observações: {informacoes_consolidadas['observacoes']}")
        
        return '\n'.join(ementa_final) if ementa_final else "Ementa não disponível"

# Função principal para uso externo
def processar_documento_para_ementa(texto_completo, llm):
    """Função principal para processar documento e gerar ementa"""
    processador = ProcessadorEmentasAvancado(llm)
    
    chunks = processador.dividir_documento_em_chunks(texto_completo)
    informacoes_chunks = []
    
    for i, chunk in enumerate(chunks):
        informacoes = processador.processar_chunk(chunk, i+1, len(chunks))
        informacoes_chunks.append(informacoes)
    
    informacoes_consolidadas = processador.consolidar_informacoes_chunks(informacoes_chunks)
    ementa_final = processador.gerar_ementa_final(informacoes_consolidadas)
    
    return ementa_final

def criar_secao_ementa_colapsavel(ementa_gerada):
    """Cria uma seção colapsável para a ementa"""
    if not ementa_gerada or "não disponível" in ementa_gerada.lower():
        return "<div style='background-color: #fff3cd; padding: 15px; border-radius: 8px; border-left: 4px solid #ffc107;'><em>Ementa em processamento...</em></div>"
    
    linhas = ementa_gerada.split('\n')
    html_ementa = "<div style='background-color: #f8f9fa; padding: 15px; border-radius: 8px; border-left: 4px solid #006633; font-size: 14px; line-height: 1.5;'>"
    
    for linha in linhas:
        if ':' in linha:
            chave, valor = linha.split(':', 1)
            html_ementa += f"<p style='margin: 8px 0;'><strong style='color: #006633;'>{chave.strip()}:</strong> {valor.strip()}</p>"
        else:
            html_ementa += f"<p style='margin: 8px 0;'>{linha}</p>"
    
    html_ementa += "</div>"
    return html_ementa