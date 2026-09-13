import math
def main():
    radius = int(input("반지름을 입력하십시오 : "))
    pi = 3.1415
    if(int(radius) >= 0):
        Daimeter = pi * radius * 2
        print(Daimeter)

    else:
        print("양수를 입력하십시오")
        return

if __name__ == "__main__":
    main()