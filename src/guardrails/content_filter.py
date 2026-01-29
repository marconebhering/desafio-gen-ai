"""
Guardrail customizado para filtrar conteúdo inadequado
Bloqueia tópicos sensíveis como violência, política, religião, etc.
"""

import re
from typing import List, Dict, Set
from agno.exceptions import CheckTrigger, InputCheckError
from agno.guardrails import BaseGuardrail
from agno.run.agent import RunInput


class ContentFilterGuardrail(BaseGuardrail):
    """
    Guardrail para identificar e bloquear conteúdo inadequado.
    
    Filtra:
    - Violência e agressão
    - Política partidária
    - Religião (proselitismo)
    - Conteúdo sexual explícito
    - Discurso de ódio
    - Tópicos controversos sensíveis
    """
    
    def __init__(
        self,
        block_violence: bool = True,
        block_politics: bool = True,
        block_religion: bool = True,
        block_explicit: bool = True,
        block_hate_speech: bool = True,
        block_illegal: bool = True,
        custom_keywords: List[str] = None,
        strictness: str = "medium"  # "low", "medium", "high"
    ):
        """
        Inicializa o guardrail com configurações customizáveis.
        
        Args:
            block_violence: Bloquear conteúdo violento
            block_politics: Bloquear política partidária
            block_religion: Bloquear proselitismo religioso
            block_explicit: Bloquear conteúdo sexual explícito
            block_hate_speech: Bloquear discurso de ódio
            block_illegal: Bloquear atividades ilegais
            custom_keywords: Lista adicional de palavras-chave para bloquear
            strictness: Nível de rigor ("low", "medium", "high")
        """
        super().__init__()
        self.block_violence = block_violence
        self.block_politics = block_politics
        self.block_religion = block_religion
        self.block_explicit = block_explicit
        self.block_hate_speech = block_hate_speech
        self.block_illegal = block_illegal
        self.strictness = strictness
        
        # Dicionário de categorias e palavras-chave
        self.categories: Dict[str, Set[str]] = self._build_keyword_dict()
        
        # Adicionar palavras customizadas
        if custom_keywords:
            self.categories["custom"] = set(kw.lower() for kw in custom_keywords)
    
    def _build_keyword_dict(self) -> Dict[str, Set[str]]:
        """Constrói dicionário de palavras-chave por categoria."""
        categories = {}
        
        # Violência e agressão
        if self.block_violence:
            categories["violence"] = {
                # Violência física
                "matar", "assassinar", "homicídio", "assassinato", "morte violenta",
                "espancar", "agredir", "agressão", "violência", "bater",
                "tortura", "torturar", "machucar", "ferir", "lesão corporal",
                "esfaquear", "facada", "tiro", "baleado", "atirar",
                "explodir", "explosão", "bomba", "atentado", "terrorismo",
                "sequestro", "sequestrar", "rapto", "raptar",
                "estupro", "estuprar", "violação", "abuso sexual",
                # Armas
                "arma de fogo", "revólver", "pistola", "fuzil", "metralhadora",
                "faca", "punhal", "facão", "navalha",
                # Gangues e crime organizado
                "gangue", "quadrilha", "facção", "tráfico", "narcotráfico",
                "milícia", "confronto armado",
            }
        
        # Política partidária e figuras políticas
        if self.block_politics:
            categories["politics"] = {
                # Termos políticos gerais
                "eleição", "candidato", "partido político", "voto",
                "campanha eleitoral", "comício", "debate político",
                # Espectro político
                "esquerda", "direita", "centro", "liberal", "conservador",
                "socialismo", "comunismo", "capitalismo", "fascismo",
                "petista", "bolsonarista", "lulista",
                # Instituições políticas específicas (com cautela)
                "congresso nacional", "câmara dos deputados", "senado federal",
                "presidência da república", "ministério",
                # Partidos (siglas)
                "pt", "psdb", "mdb", "psd", "pp", "pl", "psol", "pdt",
                # Figuras políticas recentes (adaptar conforme contexto)
                "lula", "bolsonaro", "dilma", "temer", "fhc",
                # Discurso político polarizado
                "golpe", "impeachment", "ditadura", "democracia em risco",
                "corrupção sistêmica", "fraude eleitoral",
            }
        
        # Religião e proselitismo
        if self.block_religion:
            categories["religion"] = {
                # Proselitismo
                "converter", "conversão religiosa", "salvação eterna",
                "aceitar jesus", "aceitar cristo", "batismo",
                "vida eterna", "céu e inferno", "condenação eterna",
                # Conflitos religiosos
                "guerra santa", "jihad", "cruzada", "inquisição",
                "perseguição religiosa", "heresia", "infiel",
                # Extremismo religioso
                "fundamentalismo", "extremismo religioso", "seita",
                "culto religioso", "doutrinação",
                # Ofensas religiosas (pode ser polêmico - ajustar conforme necessário)
                "blasfêmia", "sacrilégio", "profanação",
            }
        
        # Conteúdo sexual explícito
        if self.block_explicit:
            categories["explicit"] = {
                # Termos sexuais explícitos (lista básica)
                "pornografia", "pornográfico", "sexo explícito",
                "nudez", "nu", "despido",
                "orgasmo", "masturbação", "masturbar",
                "relação sexual", "ato sexual", "coito",
                "oral sex", "sexo oral", "anal sex",
                # Anatomia sexual explícita
                "pênis", "vagina", "órgão sexual", "genitália",
                "seios nus", "peitos nus",
                # Conteúdo adulto
                "conteúdo adulto", "+18", "apenas adultos",
                "conteúdo impróprio", "nsfw",
            }
        
        # Discurso de ódio
        if self.block_hate_speech:
            categories["hate_speech"] = {
                # Racismo
                "racismo", "racista", "supremacia branca", "nazismo", "neonazismo",
                "kkk", "ku klux klan", "eugenia", "limpeza étnica",
                # Xenofobia
                "xenofobia", "xenófobo", "estrangeiro sujo",
                # Homofobia
                "homofobia", "homofóbico", "gay repugnante",
                # Misoginia
                "misoginia", "misógino", "mulher inferior",
                # Outros preconceitos
                "discriminação", "preconceito", "intolerância",
                "genocídio", "holocausto",
                # Termos ofensivos de ódio (reduzido por moderação)
                "inferior por raça", "raça superior", "subumano",
            }
        
        # Atividades ilegais
        if self.block_illegal:
            categories["illegal"] = {
                # Drogas
                "como fazer droga", "produzir droga", "sintetizar droga",
                "metanfetamina", "crack", "cocaína", "heroína",
                "comprar droga", "vender droga", "traficar",
                # Hacking/Cybercrime
                "hackear", "invadir sistema", "roubar senha",
                "phishing", "malware", "ransomware", "exploit",
                "ddos", "ataque cibernético",
                # Fraude
                "fraude", "golpe", "estelionato", "falsificação",
                "documento falso", "identidade falsa",
                # Outros crimes
                "roubo", "roubar", "furto", "furtar",
                "contrabando", "pirataria", "receptação",
                "lavagem de dinheiro", "sonegação fiscal",
            }
        
        # Ajustar sensibilidade baseado no strictness
        if self.strictness == "low":
            # Remover termos menos críticos de algumas categorias
            for category in categories.values():
                # Manter apenas termos mais explícitos
                pass  # Implementar lógica de redução se necessário
        
        elif self.strictness == "high":
            # Adicionar termos mais amplos
            if "violence" in categories:
                categories["violence"].update({"conflito", "luta", "briga"})
            if "politics" in categories:
                categories["politics"].update({"política", "governo", "presidente"})
        
        return categories
    
    def _check_keywords(self, text: str) -> tuple[bool, str, List[str]]:
        """
        Verifica se o texto contém palavras-chave bloqueadas.
        
        Returns:
            (is_blocked, category, matched_keywords)
        """
        text_lower = text.lower()
        
        # Normalizar texto (remover acentos para melhor matching)
        text_normalized = self._normalize_text(text_lower)
        
        for category, keywords in self.categories.items():
            matched = []
            for keyword in keywords:
                keyword_normalized = self._normalize_text(keyword)
                # Usar word boundaries para evitar falsos positivos
                pattern = r'\b' + re.escape(keyword_normalized) + r'\b'
                if re.search(pattern, text_normalized):
                    matched.append(keyword)
            
            if matched:
                return True, category, matched
        
        return False, "", []
    
    def _normalize_text(self, text: str) -> str:
        """Remove acentos e normaliza texto."""
        # Mapeamento de caracteres acentuados
        replacements = {
            'á': 'a', 'à': 'a', 'ã': 'a', 'â': 'a', 'ä': 'a',
            'é': 'e', 'è': 'e', 'ê': 'e', 'ë': 'e',
            'í': 'i', 'ì': 'i', 'î': 'i', 'ï': 'i',
            'ó': 'o', 'ò': 'o', 'õ': 'o', 'ô': 'o', 'ö': 'o',
            'ú': 'u', 'ù': 'u', 'û': 'u', 'ü': 'u',
            'ç': 'c', 'ñ': 'n'
        }
        
        normalized = text
        for char, replacement in replacements.items():
            normalized = normalized.replace(char, replacement)
        
        return normalized
    
    def _get_error_message(self, category: str, matched_keywords: List[str]) -> str:
        """Gera mensagem de erro apropriada para a categoria."""
        category_names = {
            "violence": "violência ou agressão",
            "politics": "política partidária",
            "religion": "proselitismo religioso",
            "explicit": "conteúdo sexual explícito",
            "hate_speech": "discurso de ódio",
            "illegal": "atividades ilegais",
            "custom": "conteúdo bloqueado"
        }
        
        category_name = category_names.get(category, "conteúdo inadequado")
        
        # Mensagens genéricas (não expor as palavras exatas por segurança)
        messages = {
            "violence": "Detectamos conteúdo relacionado a violência. Por favor, reformule sua pergunta focando em análise de dados de saúde pública.",
            "politics": "Detectamos conteúdo político-partidário. Este sistema é focado em análise epidemiológica e não discute política.",
            "religion": "Detectamos conteúdo religioso sensível. Por favor, mantenha o foco em questões relacionadas à saúde pública.",
            "explicit": "Detectamos conteúdo inadequado. Por favor, mantenha sua interação profissional e apropriada.",
            "hate_speech": "Detectamos linguagem ofensiva ou discriminatória. Isso não é permitido. Mantenha o respeito.",
            "illegal": "Detectamos referência a atividades ilegais. Este sistema não pode ajudar com esse tipo de conteúdo.",
            "custom": "Seu input contém conteúdo que não é permitido neste sistema."
        }
        
        return messages.get(category, f"Detectamos {category_name} no seu input, o que não é permitido.")
    
    def check(self, run_input: RunInput) -> None:
        """Verifica se o input contém conteúdo bloqueado (síncrono)."""
        if not isinstance(run_input.input_content, str):
            return
        
        is_blocked, category, matched = self._check_keywords(run_input.input_content)
        
        if is_blocked:
            error_message = self._get_error_message(category, matched)
            raise InputCheckError(
                error_message,
                check_trigger=CheckTrigger.INPUT_NOT_ALLOWED,
            )
    
    async def async_check(self, run_input: RunInput) -> None:
        """Verifica se o input contém conteúdo bloqueado (assíncrono)."""
        if not isinstance(run_input.input_content, str):
            return
        
        is_blocked, category, matched = self._check_keywords(run_input.input_content)
        
        if is_blocked:
            error_message = self._get_error_message(category, matched)
            raise InputCheckError(
                error_message,
                check_trigger=CheckTrigger.INPUT_NOT_ALLOWED,
            )
