import services.grade as grade

def main():
    print("--- Import OK ---")
    print("Resumo:", grade.get_resumo())
    print("--- Gerar grade ---")
    result = grade.gerar_grade()
    print("Resultado da geração:", result)
    print("--- Grade atual ---")
    print(grade.get_grade())

if __name__ == "__main__":
    main()
