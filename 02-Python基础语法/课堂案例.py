"""课堂案例：简易计算器"""


def add(a: float, b: float) -> float:
    """加法"""
    return a + b


def subtract(a: float, b: float) -> float:
    """减法"""
    return a - b


def multiply(a: float, b: float) -> float:
    """乘法"""
    return a * b


def divide(a: float, b: float) -> float:
    """除法"""
    if b == 0:
        raise ValueError("除数不能为零！")
    return a / b


def calculator():
    """交互式计算器"""
    print("=== 简易计算器 ===")
    print("支持的运算: +, -, *, /")
    print("输入 'quit' 退出")

    while True:
        expr = input("\n请输入算式 (如 2 + 3): ").strip()

        if expr.lower() == "quit":
            print("再见！")
            break

        parts = expr.split()
        if len(parts) != 3:
            print("格式错误，请使用: 数字 运算符 数字")
            continue

        try:
            a, op, b = float(parts[0]), parts[1], float(parts[2])

            if op == "+":
                result = add(a, b)
            elif op == "-":
                result = subtract(a, b)
            elif op == "*":
                result = multiply(a, b)
            elif op == "/":
                result = divide(a, b)
            else:
                print(f"不支持的运算符: {op}")
                continue

            print(f"结果: {a} {op} {b} = {result}")

        except ValueError as e:
            print(f"错误: {e}")
        except Exception:
            print("输入无效，请重试")


if __name__ == "__main__":
    calculator()
