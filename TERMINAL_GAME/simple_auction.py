# # Libraries
import random
import time
import os

# Color
RED = "\033[91m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
BLUE = "\033[94m"
PURPLE = "\033[95m"
CYAN = "\033[96m"
BOLD = "\033[1m"
END = "\033[0m"

# Products for game
PRODUCTS = [
    ("🌹 Розы", 15000, 8000),
    ("🌻 Подсолнухи", 8000, 4000),
    ("🌺 Орхидеи", 25000, 12000),
    ("🌷 Тюльпаны", 12000, 6000),
    ("🌸 Сакура", 30000, 15000),
    ("🌼 Ромашки", 5000, 2500),
    ("🌿 Лаванда", 10000, 5000),
    ("🌺 Пионы", 18000, 9000),
    ("🌻 Георгины", 14000, 7000),
    ("🌷 Ирисы", 11000, 5500),
    ("🌹 Гвоздики", 9000, 4500),
    ("🌺 Лилии", 20000, 10000),
]

# Ai players
AI_PLAYERS = [
    ("Ваня", 150000, "Пионы", "Розы"),
    ("Анастасия", 280000, "Розы", "Пионы"),
    ("Игорь", 200000, "Орхидеи", "Ромашки"),
    ("Марина", 120000, "Тюльпаны", "Георгины"),
    ("Дмитрий", 300000, "Лаванда", "Лилии"),
    ("Светлана", 175000, "Ирисы", "Гвоздики"),
]


# Clean terminal
def clear():
    os.system("cls" if os.name == "nt" else "clear")


# Showing the balance
def format_money(amount):
    return f"{amount:,} ₽"

# Showing heading
def print_header():
    print(f"{BOLD}{PURPLE}{'='*50}")
    print("🔥 ГОЛЛАНДСКИЙ АУКЦИОН GOLAN 🔥")
    print(f"{'='*50}{END}")


def ai_buy_decision(player, product_name, price): #Ai thinking about buying or not
    name, balance, likes, dislikes = player
    if balance < price:
        return False
    if likes in product_name:
        return random.random() < 0.7
    if dislikes in product_name:
        return random.random() < 0.1
    return random.random() < 0.3


def main():
    clear()
    print_header()

    # Create user 
    user_name = input(f"{CYAN}Введите ваше имя: {END}").strip() or "Игрок"
    user_balance = 200000
    user_profit = 0
    user_purchases = 0

    print(f"\n{GREEN}Привет, {user_name}! У вас {format_money(user_balance)}{END}")
    input(f"{YELLOW}Нажмите Enter для начала...{END}")

    # Play 5 rounds
    for round_num in range(1, 6):
        clear()
        print_header()
        print(f"{BOLD}Раунд {round_num}/5{END}\n")

        # Choosing a product
        product_name, start_price, cost = random.choice(PRODUCTS)
        current_price = start_price

        print(f"{BOLD}{YELLOW}💎 ТОВАР: {product_name}{END}")
        print(f"💰 Начальная цена: {GREEN}{format_money(start_price)}{END}")
        print(f"💸 Себестоимость: {RED}{format_money(cost)}{END}")
        potential_profit = cost - start_price
        profit_color = GREEN if potential_profit >= 0 else RED
        profit_sign = "+" if potential_profit >= 0 else ""
        print(
            f"📈 Потенциальная прибыль: {profit_color}{profit_sign}{format_money(potential_profit)}{END}"
        )
        print(f"{CYAN}💡 Прибыль = Цена покупки × 1.3 (130%){END}\n")

        # Showing usre
        print(f"{BOLD}👤 ВАШ ПРОФИЛЬ{END}")
        print(f"💰 Баланс: {GREEN}{format_money(user_balance)}{END}")
        profit_color = GREEN if user_profit >= 0 else RED
        profit_sign = "+" if user_profit >= 0 else ""
        print(
            f"📈 Прибыль: {profit_color}{profit_sign}{format_money(user_profit)}{END}"
        )
        print(f"🛒 Покупки: {YELLOW}{user_purchases}{END}\n")

        # Auction
        winner = None
        final_price = 0

        while current_price > cost:
            print(f"{BOLD}💰 Текущая цена: {GREEN}{format_money(current_price)}{END}")

            # User decision
            choice = input(f"\n{CYAN}1-Купить, 2-Ждать: {END}").strip()

            if choice == "1":
                if user_balance >= current_price:
                    # User buy 
                    user_balance -= current_price
                    profit_multiplier = 1.3  # 130% прибыли
                    profit = current_price * profit_multiplier
                    user_profit += profit
                    user_purchases += 1
                    winner = (user_name, current_price, profit)
                    break
                else:
                    print(f"{RED}❌ Недостаточно средств!{END}")

            # Ai players choosing 
            for player in AI_PLAYERS:
                if ai_buy_decision(player, product_name, current_price):
                    profit_multiplier = 1.3  # 130% прибыли
                    profit = current_price * profit_multiplier
                    winner = (player[0], current_price, profit)
                    break

            if winner:
                break

            # Price lower 
            current_price = int(current_price * 0.95)
            time.sleep(0.5)

        # Round results
        print(f"\n{BOLD}📊 РЕЗУЛЬТАТ РАУНДА:{END}")
        if winner:
            name, price, profit = winner
            print(f"🏆 {GREEN}{name}{END} купил {product_name}")
            print(f"💰 Цена: {GREEN}{format_money(price)}{END}")
            profit_color = GREEN if profit >= 0 else RED
            profit_sign = "+" if profit >= 0 else ""
            print(f"📈 Прибыль: {profit_color}{profit_sign}{format_money(profit)}{END}")
        else:
            print(f"{RED}❌ Товар не продан{END}")

        if round_num < 5:
            input(f"\n{YELLOW}Нажмите Enter для следующего раунда...{END}")

    # Final results
    clear()
    print_header()
    print(f"{BOLD}{GREEN}🎉 ИГРА ЗАВЕРШЕНА! 🎉{END}\n")
    print(f"{BOLD}👤 ВАШИ РЕЗУЛЬТАТЫ:{END}")
    print(f"💰 Финальный баланс: {GREEN}{format_money(user_balance)}{END}")
    profit_color = GREEN if user_profit >= 0 else RED
    profit_sign = "+" if user_profit >= 0 else ""
    print(
        f"📈 Общая прибыль: {profit_color}{profit_sign}{format_money(user_profit)}{END}"
    )
    print(f"🛒 Покупок: {YELLOW}{user_purchases}{END}")
    print(f"\n{CYAN}Спасибо за игру! 👋{END}")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n\n{RED}Игра прервана{END}")
    except Exception as e:
        print(f"\n\n{RED}Ошибка: {e}{END}")
