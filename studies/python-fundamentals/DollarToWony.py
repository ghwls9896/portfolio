EXCH_RATE = 1465

def main():
    dollar = int(input("달러를 입력하세요 : " ))

    won = dollar * EXCH_RATE 

    print(f"{dollar}달러 => {won}원")

if __name__ == "__main__":
    main()