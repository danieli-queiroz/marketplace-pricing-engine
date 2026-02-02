def percentage_of(percent, total):
    # Calcula quanto é X% de um Total.
    if not total:
        return 0.0
    return (percent / 100) * total

def percent_from_total(value, total):
    # Calcula quantos % o valor representa do total.
    if not total or total == 0:
        return 0.0
    return round((value / total) * 100, 2)

def percentage_division(percent):
    # Transforma 20.0 em 0.20 para divisões
    return percent / 100

def percentage_multiplication(factor):
    # Transforma 0.17 em 17.0 para exibição.
    return factor * 100