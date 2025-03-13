import re

from colorama import init, Fore, Style

def center_colored_text(text, width):
    ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')  # Regex for ANSI codes
    visible_text = ansi_escape.sub('', text) 
    padding = max(0, width - len(visible_text))  # Calculate required padding
    left_pad = padding // 2
    right_pad = padding - left_pad
    return " " * left_pad + text + " " * right_pad  # Apply padding around the text

if __name__ == "__main__":
    print("1234|")
    letter = Style.BRIGHT + Fore.WHITE + 'a'
    print(center_colored_text(letter, 4) + '|')
    init(autoreset=True)
    