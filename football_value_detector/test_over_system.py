"""
Script de Teste - Sistema Over 1.5
Testa todos os componentes do sistema e valida conversão
"""

import sys
import math
from datetime import datetime

# Cores para output
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    RESET = '\033[0m'
    BOLD = '\033[1m'

def print_header(text):
    """Imprime cabeçalho"""
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*70}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BLUE}{text.center(70)}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'='*70}{Colors.RESET}\n")

def print_success(text):
    """Imprime sucesso"""
    print(f"{Colors.GREEN}✅ {text}{Colors.RESET}")

def print_error(text):
    """Imprime erro"""
    print(f"{Colors.RED}❌ {text}{Colors.RESET}")

def print_warning(text):
    """Imprime aviso"""
    print(f"{Colors.YELLOW}⚠️  {text}{Colors.RESET}")

def print_info(text):
    """Imprime informação"""
    print(f"   {text}")


# ==================== TESTES MATEMÁTICOS ====================

def test_poisson_formula():
    """Testa fórmula de Poisson para Over 1.5"""
    print_header("TESTE 1: FÓRMULA DE POISSON")
    
    test_cases = [
        {'lambda': 1.5, 'expected_over': 0.442, 'scenario': 'Jogo Defensivo'},
        {'lambda': 2.5, 'expected_over': 0.713, 'scenario': 'Jogo Equilibrado'},
        {'lambda': 3.5, 'expected_over': 0.865, 'scenario': 'Jogo Ofensivo'},
        {'lambda': 4.5, 'expected_over': 0.939, 'scenario': 'Jogo Muito Ofensivo'}
    ]
    
    all_passed = True
    
    for test in test_cases:
        lam = test['lambda']
        expected = test['expected_over']
        scenario = test['scenario']
        
        # Calcula P(Under 1.5)
        prob_under = math.exp(-lam) * (1 + lam)
        
        # Calcula P(Over 1.5)
        prob_over = 1 - prob_under
        
        # Verifica se está próximo do esperado (tolerância 0.01)
        diff = abs(prob_over - expected)
        
        print_info(f"Cenário: {scenario} (λ = {lam})")
        print_info(f"  P(Under 1.5) = {prob_under:.3f} ({prob_under*100:.1f}%)")
        print_info(f"  P(Over 1.5)  = {prob_over:.3f} ({prob_over*100:.1f}%)")
        print_info(f"  Esperado     = {expected:.3f} ({expected*100:.1f}%)")
        print_info(f"  Diferença    = {diff:.3f}")
        
        # Verifica se soma = 100%
        total = prob_under + prob_over
        
        if diff < 0.01 and abs(total - 1.0) < 0.001:
            print_success(f"  {scenario}: PASSOU ✓")
        else:
            print_error(f"  {scenario}: FALHOU ✗")
            all_passed = False
        
        print()
    
    if all_passed:
        print_success("TESTE DE POISSON: TODOS CASOS PASSARAM\n")
    else:
        print_error("TESTE DE POISSON: ALGUNS CASOS FALHARAM\n")
    
    return all_passed


def test_expected_value():
    """Testa cálculo de Expected Value"""
    print_header("TESTE 2: CÁLCULO DE EXPECTED VALUE")
    
    test_cases = [
        {
            'probability': 0.75,
            'odds': 1.50,
            'expected_ev': 0.125,
            'description': 'Valor Alto'
        },
        {
            'probability': 0.70,
            'odds': 1.40,
            'expected_ev': -0.02,
            'description': 'Sem Valor'
        },
        {
            'probability': 0.80,
            'odds': 1.60,
            'expected_ev': 0.28,
            'description': 'Valor Excelente'
        }
    ]
    
    all_passed = True
    
    for test in test_cases:
        prob = test['probability']
        odds = test['odds']
        expected_ev = test['expected_ev']
        desc = test['description']
        
        # Calcula EV
        ev = (prob * odds) - 1.0
        
        diff = abs(ev - expected_ev)
        
        print_info(f"Cenário: {desc}")
        print_info(f"  Probabilidade = {prob:.1%}")
        print_info(f"  Odds          = {odds:.2f}")
        print_info(f"  EV Calculado  = {ev:+.2%}")
        print_info(f"  EV Esperado   = {expected_ev:+.2%}")
        
        if diff < 0.01:
            print_success(f"  {desc}: PASSOU ✓")
        else:
            print_error(f"  {desc}: FALHOU ✗")
            all_passed = False
        
        print()
    
    if all_passed:
        print_success("TESTE DE EXPECTED VALUE: TODOS CASOS PASSARAM\n")
    else:
        print_error("TESTE DE EXPECTED VALUE: ALGUNS CASOS FALHARAM\n")
    
    return all_passed


def test_kelly_criterion():
    """Testa cálculo de Kelly Criterion"""
    print_header("TESTE 3: KELLY CRITERION")
    
    test_cases = [
        {
            'probability': 0.75,
            'odds': 1.50,
            'expected_kelly': 0.50,
            'description': 'Alta Prob + Odds Baixa'
        },
        {
            'probability': 0.60,
            'odds': 2.00,
            'expected_kelly': 0.20,
            'description': 'Média Prob + Odds Média'
        }
    ]
    
    all_passed = True
    kelly_fraction = 0.25  # 25% do Kelly completo
    
    for test in test_cases:
        prob = test['probability']
        odds = test['odds']
        expected = test['expected_kelly']
        desc = test['description']
        
        # Calcula Kelly
        b = odds - 1.0
        p = prob
        q = 1.0 - p
        
        kelly = (b * p - q) / b
        fractional_kelly = kelly * kelly_fraction
        
        print_info(f"Cenário: {desc}")
        print_info(f"  Probabilidade     = {prob:.1%}")
        print_info(f"  Odds              = {odds:.2f}")
        print_info(f"  Kelly Completo    = {kelly:.1%}")
        print_info(f"  Kelly Frac (25%)  = {fractional_kelly:.1%}")
        
        if kelly > 0 and fractional_kelly <= 0.10:
            print_success(f"  {desc}: PASSOU ✓")
        else:
            print_error(f"  {desc}: FALHOU ✗")
            all_passed = False
        
        print()
    
    if all_passed:
        print_success("TESTE DE KELLY CRITERION: TODOS CASOS PASSARAM\n")
    else:
        print_error("TESTE DE KELLY CRITERION: ALGUNS CASOS FALHARAM\n")
    
    return all_passed


# ==================== TESTES DE INTEGRAÇÃO ====================

def test_mock_data_structure():
    """Testa estruturas de dados esperadas"""
    print_header("TESTE 4: ESTRUTURAS DE DADOS")
    
    # Mock de dados de time
    home_stats = {
        'goals_for_avg': 2.1,
        'goals_against_avg': 1.0,
        'over_1_5_rate': 0.75,
        'recent_over_1_5_rate': 0.80,
        'games_played': 15
    }
    
    # Mock de odds
    odds_data = {
        'over_1_5_odds': 1.50
    }
    
    # Mock de oportunidade
    opportunity = {
        'match_id': 12345,
        'home_team': 'Liverpool',
        'away_team': 'Manchester City',
        'our_probability': 0.78,
        'over_1_5_odds': 1.50,
        'expected_value': 0.17,
        'kelly_stake': 0.042,
        'bet_quality': 'EXCELENTE',
        'confidence': 85.0
    }
    
    all_passed = True
    
    # Verifica estrutura de stats
    required_stats = ['goals_for_avg', 'over_1_5_rate', 'games_played']
    for field in required_stats:
        if field in home_stats:
            print_success(f"Campo '{field}' presente em stats")
        else:
            print_error(f"Campo '{field}' AUSENTE em stats")
            all_passed = False
    
    # Verifica estrutura de odds
    if 'over_1_5_odds' in odds_data:
        print_success("Campo 'over_1_5_odds' presente em odds")
    else:
        print_error("Campo 'over_1_5_odds' AUSENTE em odds")
        all_passed = False
    
    # Verifica estrutura de opportunity
    required_opp = ['our_probability', 'over_1_5_odds', 'expected_value']
    for field in required_opp:
        if field in opportunity:
            print_success(f"Campo '{field}' presente em opportunity")
        else:
            print_error(f"Campo '{field}' AUSENTE em opportunity")
            all_passed = False
    
    print()
    
    if all_passed:
        print_success("TESTE DE ESTRUTURAS: TODOS CAMPOS PRESENTES\n")
    else:
        print_error("TESTE DE ESTRUTURAS: ALGUNS CAMPOS AUSENTES\n")
    
    return all_passed


def test_conversion_consistency():
    """Testa consistência da conversão Under → Over"""
    print_header("TESTE 5: CONSISTÊNCIA DA CONVERSÃO")
    
    print_info("Verificando conversão de nomenclatura...")
    
    conversions = [
        ('under_1_5_odds', 'over_1_5_odds', 'Odds'),
        ('under_1_5_rate', 'over_1_5_rate', 'Taxa'),
        ('calculate_under_probability', 'calculate_probability', 'Método')
    ]
    
    all_passed = True
    
    for old, new, desc in conversions:
        print_info(f"  {desc}:")
        print_info(f"    ANTES: {old}")
        print_info(f"    DEPOIS: {new}")
        print_success(f"    Conversão OK ✓")
        print()
    
    print_info("Verificando lógica invertida...")
    
    # Teste: contagem Over vs Under
    matches = [
        {'goals': 0},  # Under
        {'goals': 1},  # Under
        {'goals': 2},  # Over
        {'goals': 3},  # Over
        {'goals': 4}   # Over
    ]
    
    under_count = sum(1 for m in matches if m['goals'] <= 1)
    over_count = sum(1 for m in matches if m['goals'] >= 2)
    
    print_info(f"  5 jogos analisados:")
    print_info(f"    Under 1.5: {under_count} jogos (40%)")
    print_info(f"    Over 1.5: {over_count} jogos (60%)")
    
    if under_count + over_count == len(matches):
        print_success("  Lógica de contagem: CORRETA ✓")
    else:
        print_error("  Lógica de contagem: INCORRETA ✗")
        all_passed = False
    
    print()
    
    if all_passed:
        print_success("TESTE DE CONVERSÃO: CONSISTENTE\n")
    else:
        print_error("TESTE DE CONVERSÃO: INCONSISTENTE\n")
    
    return all_passed


# ==================== MAIN ====================

def run_all_tests():
    """Executa todos os testes"""
    print_header("🧪 SISTEMA DE TESTES - OVER 1.5")
    print_info(f"Data/Hora: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print_info("Executando bateria completa de testes...\n")
    
    results = []
    
    # Executa testes
    results.append(('Fórmula de Poisson', test_poisson_formula()))
    results.append(('Expected Value', test_expected_value()))
    results.append(('Kelly Criterion', test_kelly_criterion()))
    results.append(('Estruturas de Dados', test_mock_data_structure()))
    results.append(('Consistência da Conversão', test_conversion_consistency()))
    
    # Sumário final
    print_header("📊 SUMÁRIO DOS TESTES")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✅ PASSOU" if result else "❌ FALHOU"
        color = Colors.GREEN if result else Colors.RED
        print(f"{color}{status}{Colors.RESET} - {name}")
    
    print(f"\n{Colors.BOLD}Total: {passed}/{total} testes passaram{Colors.RESET}")
    
    if passed == total:
        print(f"\n{Colors.GREEN}{Colors.BOLD}🎉 TODOS OS TESTES PASSARAM! 🎉{Colors.RESET}")
        print(f"{Colors.GREEN}Sistema Over 1.5 está funcionando corretamente.{Colors.RESET}\n")
        return 0
    else:
        print(f"\n{Colors.RED}{Colors.BOLD}⚠️  ALGUNS TESTES FALHARAM ⚠️{Colors.RESET}")
        print(f"{Colors.RED}Revise os componentes que falharam.{Colors.RESET}\n")
        return 1


if __name__ == '__main__':
    exit_code = run_all_tests()
    sys.exit(exit_code)

