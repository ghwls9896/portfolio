def main():
    try:
        input_money = int(input("금액을 넣어주세요 : "))
        coff_num = int(input("커피 갯수를 입력해주세요(개당 150원) : "))
        total_coff_price = 150 * coff_num

        if input_money < total_coff_price:
            print("투입한 금액이 더 적습니다. 다시 시도해주세요.")
        else:
            change = input_money - total_coff_price
            print(f"거스름돈: {change}원")

            num_1000 = change // 1000
            change %= 1000

            num_500 = change // 500
            change %= 500

            num_100 = change // 100
            change %= 100

            num_50 = change // 50
            change %= 50

            num_10 = change // 10
            change %= 10

            # 출력
            print(f"1000원: {num_1000}개")
            print(f"500원: {num_500}개")
            print(f"100원: {num_100}개")
            print(f"50원: {num_50}개")
            print(f"10원: {num_10}개")
            print(f"남은 잔돈(10원 미만): {change}원")

    except ValueError:
        print("정수가 아닙니다! 정수를 입력하세요.")
        return


if __name__ == "__main__":
    main()