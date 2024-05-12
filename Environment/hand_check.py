from collections import Counter


def map_suit(suit):
    if suit == "Diamonds": return "方片"
    if suit == "Clubs": return "梅花"
    if suit == "Spades": return "黑桃"
    if suit == "Hearts": return "红桃"


def map_level(level):
    if level == 1: return "高牌"
    if level == 2: return "一对"
    if level == 3: return "两对"
    if level == 4: return "三条"
    if level == 5: return "顺子"
    if level == 6: return "同花"
    if level == 7: return "葫芦"
    if level == 8: return "四条"
    if level == 9: return "同花顺"


def suit_to_value(suit):
    """将花色转换为数值，用于比较大小"""
    suit_values = {'Hearts': 4, 'Diamonds': 3, 'Clubs': 2, 'Spades': 1}
    return suit_values[suit]


def rank_to_value(rank):
    """将牌面转换为数值，用于比较大小"""
    values = '23456789TJQKA'
    rank_values = {rank: value for rank, value in zip(values, range(2, 15))}
    rank_values.pop('T')
    rank_values['10'] = 10
    return rank_values[rank]


def evaluate_hand(cards):
    """评估手牌并返回牌型及关键牌"""
    cards = [(suit_to_value(card.suit), rank_to_value(card.rank)) for card in cards]
    cards = sorted(cards, key=lambda x: x[1], reverse=True)
    if is_straight_flush(cards) is not False:
        return (9, is_straight_flush(cards))
    if is_four_of_a_kind(cards) is not False:
        return (8, is_four_of_a_kind(cards))
    if is_full_house(cards) is not False:
        return (7, is_full_house(cards))
    if is_flush(cards) is not False:
        return (6, is_flush(cards))
    if is_straight(cards) is not False:
        return (5, is_straight(cards))
    if is_three_of_a_kind(cards) is not False:
        return (4, is_three_of_a_kind(cards))
    if is_two_pair(cards) is not False:
        return (3, is_two_pair(cards))
    if is_one_pair(cards) is not False:
        return (2, is_one_pair(cards))
    return (1, is_high_card(cards))