print("\x1b[2J")
import os
import unicodedata
from dotenv import load_dotenv
from pydantic import BaseModel, Field
from guardrails import Guard

# Carregar variáveis de ambiente do arquivo .env
load_dotenv()

# Configuração da chave da API da OpenAI
api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    raise ValueError("A chave da API 'OPENAI_API_KEY' não foi encontrada. Verifique o arquivo .env.")

# Lista de tipos de embalagem válidos conforme a legislação
TIPOS_EMBALAGEM_VALIDOS = [
    "plastica", "metalica", "vidro", "papelao", "plastico flexivel", "outro"
]

# Modelo de dados validado pelo Guardrails
class Embalagem(BaseModel):
    tipo_embalagem: str = Field(description="Tipo de embalagem (ex., Plástica, Metálica)")
    e_lavavel: bool = Field(description="Indica se a embalagem é lavável")
    contem_residuos: bool = Field(description="Indica se a embalagem contém resíduos perigosos")
    orientacao: str = Field(description="Orientação para destinação correta")

# Configuração do Guardrails
prompt = """
Você é um assistente especializado em destinação de embalagens de defensivos agrícolas, conforme a Lei nº 14.785, de 27 de dezembro de 2023.
O usuário forneceu os seguintes dados:

Tipo de embalagem: {tipo_embalagem}
É lavável: {e_lavavel}
Contém resíduos perigosos: {contem_residuos}

Se o tipo de embalagem informado não estiver entre as seguintes opções válidas: {tipos_validos}, responda que o tipo de embalagem não é reconhecido pela legislação e não forneça uma orientação.
Caso contrário, forneça uma orientação clara e apropriada para o descarte dessa embalagem. Responda no formato JSON.
"""

guard = Guard.for_pydantic(output_class=Embalagem)

# Função para remover acentos e normalizar texto
def remover_acentos(texto):
    nfkd = unicodedata.normalize('NFKD', texto)
    return u"".join([c for c in nfkd if not unicodedata.combining(c)]).lower()

# Função para interagir com o Guardrails e gerar a orientação
def obter_orientacao(tipo_embalagem, e_lavavel, contem_residuos):
    mensagem = prompt.format(
        tipo_embalagem=tipo_embalagem,
        e_lavavel="Sim" if e_lavavel else "Não",
        contem_residuos="Sim" if contem_residuos else "Não",
        tipos_validos=", ".join(TIPOS_EMBALAGEM_VALIDOS)
    )
    
    try:
        # Enviar o prompt para o modelo via Guardrails
        res = guard(
            model="gpt-4o-mini-2024-07-18",
            messages=[{
                "role": "user",
                "content": mensagem
            }]
        )
        # Retornar a saída validada
        return res.validated_output
    except Exception as e:
        return f"Erro ao gerar orientação: {e}"

# Função auxiliar para processar as respostas do usuário
def processar_resposta(resposta, contexto):
    resposta_normalizada = remover_acentos(resposta.strip().lower())
    respostas_vagas = ["nao sei", "talvez", "nao tenho certeza", "sei la", "indefinido", "o que voce acha", "voce e quem diz", "vai la ver"]
    if resposta_normalizada in respostas_vagas:
        if contexto == "tipo_embalagem":
            print("\nPor favor, especifique o tipo de embalagem para que possamos fornecer uma orientação adequada.")
            return None
        elif contexto == "lavavel":
            print("\nExplicação: Uma embalagem é considerada lavável se pode ser limpa com água para remoção de resíduos antes do descarte.")
            return None
        elif contexto == "residuos":
            print("\nExplicação: Resíduos perigosos são substâncias químicas ou tóxicas que podem causar danos ao meio ambiente ou à saúde, como restos de defensivos agrícolas.")
            return None
    return resposta_normalizada in ["sim", "verdadeiro"]

# Loop de interação com o usuário
if _name_ == "_main_":
    print("Bem-vindo ao sistema de destinação de embalagens! Digite as informações ou 'sair' para encerrar.")
    while True:
        tipo_embalagem = input("Digite o tipo de embalagem (ex., Plástica, Metálica): ")
        tipo_embalagem_normalizado = remover_acentos(tipo_embalagem.lower())
        if tipo_embalagem_normalizado == "sair":
            print("Encerrando a conversa. Até logo!")
            break
        if tipo_embalagem_normalizado not in TIPOS_EMBALAGEM_VALIDOS:
            print("\nErro: Tipo de embalagem não reconhecido pela legislação. Tente novamente.\n")
            continue

        while True:
            e_lavavel = input("A embalagem é lavável? (sim/não/não sei): ")
            if processar_resposta(e_lavavel, "lavavel") is not None:
                e_lavavel = processar_resposta(e_lavavel, "lavavel")
                break

        while True:
            contem_residuos = input("A embalagem contém resíduos perigosos? (sim/não/não sei): ")
            if processar_resposta(contem_residuos, "residuos") is not None:
                contem_residuos = processar_resposta(contem_residuos, "residuos")
                break

        # Gerar orientação
        orientacao = obter_orientacao(tipo_embalagem, e_lavavel, contem_residuos)

        # Exibir orientação no terminal de forma mais amigável
        if isinstance(orientacao, dict):  # Confirma que a saída é um dicionário
            print("\nOrientação:")
            print(f"Tipo de embalagem: {orientacao['tipo_embalagem']}")
            print(f"É lavável: {'Sim' if orientacao['e_lavavel'] else 'Não'}")
            print(f"Contém resíduos perigosos: {'Sim' if orientacao['contem_residuos'] else 'Não'}")
            print(f"Orientação: {orientacao['orientacao']}\n")
        else:
            print(f"\nErro: {orientacao}\n")