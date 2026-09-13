def main():
    try:
        number = int(input("정수를 입력하십시오 : "))
    except ValueError:
        print("정수가 아닙니다! 숫자를 입력하세요.")
        return
    check = None

    if((number%2)== 1):
        check = False
        print(check)
    else:
        check = True
        print(check)


if __name__ == "__main__":
    main()