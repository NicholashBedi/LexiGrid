import config


def two_d_to_one_d_coordinate(row, col):
        return row * config.BOARD_HEIGHT + col

# Returns row then column
def one_d_to_two_d_coordinate(one_d):
    return one_d // config.BOARD_HEIGHT, one_d % config.BOARD_HEIGHT

def num_to_char(num: int):
    return chr(ord('A') + num - 1)

def char_to_num(char):
    return ord(char.upper()) - ord('A') + 1
