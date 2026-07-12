import json
import re
import requests
from celery import shared_task
from django.conf import settings
from django.contrib.auth import get_user_model
from django.utils import timezone
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage
from studies.models import DailyChallenge
from notifications.services import send_user_notification

User = get_user_model()

@shared_task
def ping_waha_task():
    """
    Ping no servidor WAHA a cada 12 minutos para evitar que ele durma no Render.
    """
    waha_url = getattr(settings, 'WAHA_URL', 'http://localhost:3000')
    try:
        # Pede a rota principal ou docs do WAHA
        response = requests.get(waha_url, timeout=10)
        print(f"WAHA Keepalive Ping: Status {response.status_code}")
        return True
    except Exception as e:
        print(f"Erro no Keepalive Ping do WAHA: {e}")
        return False

@shared_task
def generate_daily_challenges_task():
    """
    Gera desafios diários às 9h da manhã para os níveis: Iniciante, Intermediário e Avançado.
    Em seguida, notifica todos os usuários ativos de acordo com seus níveis.
    """
    groq_key = getattr(settings, 'GROQ_API_KEY', None)
    if not groq_key or groq_key == 'gsk_placeholder_for_development' or groq_key == "":
        print("Chave Groq indisponível. Simulando geração de desafios diários...")
        _generate_mock_daily_challenges()
        return

    levels = ['iniciante', 'intermediario', 'avancado']
    today = timezone.localdate()

    for lvl in levels:
        # Verifica se já existe um desafio gerado hoje para este nível
        if DailyChallenge.objects.filter(date=today, difficulty=lvl).exists():
            continue

        try:
            llm = ChatGroq(
                groq_api_key=groq_key,
                model="llama-3.3-70b-versatile",
                temperature=0.7
            )
            
            prompt = (
                "Você é um criador de desafios de programação Python. Crie um desafio único de programação "
                f"para o nível '{lvl.upper()}'.\n"
                "A IA do usuário é focada em Python, HTML, CSS, Tailwind CSS e JS/TS (Django Templates).\n"
                "Para desafios do nível iniciante/intermediário, foque em Python puro (lógica, funções, estruturas de dados).\n"
                "Para nível avançado, pode sugerir algoritmos mais complexos, estruturas de classes Django fictícias ou manipulações HTML/CSS/JS específicas.\n\n"
                "Retorne APENAS um objeto JSON contendo:\n"
                "- 'title': o título do desafio\n"
                "- 'description': instruções completas, objetivos do que precisa ser desenvolvido\n"
                "- 'initial_code': esqueleto inicial do código (ex: assinatura da função ou estrutura básica em Python)\n"
                "- 'test_code': código com assertivas (ex: assertions ou chamadas) que validam se a resposta do usuário funciona\n\n"
                "Exemplo de formato esperado:\n"
                "{\n"
                "  \"title\": \"Inverter String\",\n"
                "  \"description\": \"Crie uma função chamada inverter(s) que retorne a string invertida.\",\n"
                "  \"initial_code\": \"def inverter(s):\\n    # Seu código aqui\\n    pass\",\n"
                "  \"test_code\": \"assert inverter('ola') == 'alo'\\nassert inverter('python') == 'nohtyp'\"\n"
                "}\n"
                "Não retorne qualquer introdução ou texto fora do JSON."
            )

            response = llm.invoke([HumanMessage(content=prompt)])
            match = re.search(r'\{.*\}', response.content, re.DOTALL)
            if match:
                data = json.loads(match.group(0))
                DailyChallenge.objects.create(
                    title=data.get('title', f"Desafio Diário - {lvl.capitalize()}"),
                    description=data.get('description', 'Resolva o problema proposto.'),
                    difficulty=lvl,
                    initial_code=data.get('initial_code', 'def solucao():\n    pass'),
                    test_code=data.get('test_code', '# Escreva seu teste'),
                    date=today
                )
        except Exception as e:
            print(f"Erro ao gerar desafio diário do nível {lvl}: {e}")

    # Fallback caso algum nível tenha falhado na geração
    _generate_mock_daily_challenges()

    # Notificar todos os usuários ativos
    active_users = User.objects.filter(is_active=True)
    for user in active_users:
        user_lvl = getattr(user, 'level', 'iniciante')
        challenge = DailyChallenge.objects.filter(date=today, difficulty=user_lvl).first()
        if challenge:
            title = f"Desafio Diário Disponível: {challenge.title}"
            message = (
                f"Olá! O seu desafio diário de programação (Nível {user_lvl.capitalize()}) está pronto.\n\n"
                f"Desafio: {challenge.title}\n"
                f"Descrição: {challenge.description}\n\n"
                "Acesse a plataforma para resolver o código e obter o feedback detalhado da inteligência artificial!"
            )
            send_user_notification(user, title, message)

def _generate_mock_daily_challenges():
    """
    Gera desafios simulados caso o Groq falhe ou não esteja configurado.
    """
    today = timezone.localdate()
    mocks = [
        {
            'title': 'Soma de Dois Números',
            'description': 'Crie uma função soma(a, b) que retorne a soma de dois números. Atente-se às boas práticas da PEP8.',
            'difficulty': 'iniciante',
            'initial_code': 'def soma(a, b):\n    # Escreva sua lógica aqui\n    pass',
            'test_code': 'assert soma(2, 3) == 5\nassert soma(-1, 1) == 0'
        },
        {
            'title': 'Filtrar Números Primos',
            'description': 'Crie uma função filtrar_primos(numeros) que receba uma lista de inteiros e retorne apenas os números primos contidos nela.',
            'difficulty': 'intermediario',
            'initial_code': 'def filtrar_primos(numeros):\n    # Escreva sua lógica aqui\n    pass',
            'test_code': 'assert filtrar_primos([1, 2, 3, 4, 5]) == [2, 3, 5]\nassert filtrar_primos([10, 11, 12, 13]) == [11, 13]'
        },
        {
            'title': 'Validador de Parênteses',
            'description': 'Crie uma classe ParantesesValidator com um método is_valid(s: str) -> bool que verifique se os parênteses, colchetes e chaves estão balanceados corretamente.',
            'difficulty': 'avancado',
            'initial_code': 'class ParantesesValidator:\n    def is_valid(self, s: str) -> bool:\n        # Escreva sua lógica aqui\n        pass',
            'test_code': 'validator = ParantesesValidator()\nassert validator.is_valid("()[]{}") == True\nassert validator.is_valid("([)]") == False'
        }
    ]

    for mock in mocks:
        if not DailyChallenge.objects.filter(date=today, difficulty=mock['difficulty']).exists():
            DailyChallenge.objects.create(
                title=mock['title'],
                description=mock['description'],
                difficulty=mock['difficulty'],
                initial_code=mock['initial_code'],
                test_code=mock['test_code'],
                date=today
            )
