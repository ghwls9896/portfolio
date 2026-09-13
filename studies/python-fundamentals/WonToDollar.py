EXCH_RATE = 1465

def main():
    won = int(input("원화를 입력하세요 : " ))

    dollar = won // EXCH_RATE   # 정수 나눗셈
    change = won % EXCH_RATE    # 나머지 (거스름돈)

    print(f"{won} 원 =>")
    print(f"환전: {dollar} 달러")
    print(f"거스름: {change} 원")

if __name__ == "__main__":
    main()